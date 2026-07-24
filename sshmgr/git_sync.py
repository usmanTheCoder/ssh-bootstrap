"""GitOps-based backup/sync of the SSH configuration.

Auth is a GitHub Personal Access Token (per user decision - device flow
needs a registered OAuth App Client ID we don't have yet). The token is
stored in the OS credential store via `keyring`, never in plain text on
disk and never logged.

The repo holds one file, REPO_CONFIG_FILENAME, containing the portable,
standalone config produced by ssh_config.export() (i.e. no managed-block
markers - it's meant to be read back with ssh_config.import_existing()).
Note IdentityFile paths inside it are whatever this machine's paths are;
restoring onto a different machine still requires re-pointing keys there,
same limitation as any raw ssh config.
"""
import json
import os
import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import git
import keyring
import requests

import logging
from sshmgr import ssh_config
from sshmgr.store import AppStore
from sshmgr.models import Server, JumpHost, SSHKey, Settings

logger = logging.getLogger(__name__)

SERVICE_NAME = "ssh-bootstrap-manager"
TOKEN_KEY = "github-pat"
REPO_CONFIG_FILENAME = "data.json"

ProgressFn = Callable[[str, str], None]


def _noop(message: str, level: str = "info") -> None:
    pass


class GitSyncError(Exception):
    pass


class ConflictError(GitSyncError):
    def __init__(self, message: str, conflicted_files: list):
        super().__init__(message)
        self.conflicted_files = conflicted_files


def default_local_repo_path() -> Path:
    return Path.home() / ".ssh-bootstrap-manager" / "git-repo"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _force_rmtree(path: Path) -> None:
    def remove_readonly(func, path_str, _):
        try:
            os.chmod(path_str, stat.S_IWRITE)
            func(path_str)
        except Exception as e:
            logger.warning(f"Failed to remove {path_str}: {e}")

    if path.exists():
        shutil.rmtree(path, onerror=remove_readonly)


# --------------------------------------------------------------- token
def save_token(token: str) -> None:
    keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)


def get_token() -> Optional[str]:
    return keyring.get_password(SERVICE_NAME, TOKEN_KEY)


def clear_token() -> None:
    try:
        keyring.delete_password(SERVICE_NAME, TOKEN_KEY)
    except keyring.errors.PasswordDeleteError:
        pass


def validate_token(token: str) -> str:
    """Return the authenticated GitHub username, or raise GitSyncError."""
    try:
        resp = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10,
        )
    except requests.RequestException as e:
        raise GitSyncError(f"Could not reach GitHub: {e}")
    if resp.status_code != 200:
        raise GitSyncError(f"GitHub authentication failed (HTTP {resp.status_code}).")
    return resp.json().get("login", "")


def _authed_url(url: str, token: str) -> str:
    if token and url.startswith("https://") and "@" not in url.split("://", 1)[1]:
        return url.replace("https://", f"https://{token}@", 1)
    return url


def _with_authed_remote(repo: "git.Repo", action):
    """Temporarily inject the token into origin's URL for one operation,
    then restore the token-free URL - avoids leaving the token sitting in
    .git/config on disk any longer than the single git invocation needs.
    """
    token = get_token()
    origin = repo.remotes.origin
    original_url = next(origin.urls)
    use_authed = bool(token) and original_url.startswith("https://")
    if use_authed:
        origin.set_url(_authed_url(original_url, token))
    try:
        return action(origin)
    finally:
        if use_authed:
            origin.set_url(original_url)


def _open_repo(local_path: Optional[Path] = None) -> git.Repo:
    path = local_path or default_local_repo_path()
    return git.Repo(path)


# --------------------------------------------------------- repo lifecycle
def is_connected(store: AppStore, local_path: Optional[Path] = None) -> bool:
    path = local_path or default_local_repo_path()
    return bool(store.settings.git_repo_url) and (path / ".git").exists()


def connect_existing(
    store: AppStore, url: str, local_path: Optional[Path] = None, on_progress: ProgressFn = _noop
) -> None:
    """Clone an existing (possibly non-empty) repo as the local working copy."""
    path = local_path or default_local_repo_path()
    _force_rmtree(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    token = get_token()
    clone_url = _authed_url(url, token) if token else url
    on_progress(f"Cloning {url}...", "info")
    try:
        git.Repo.clone_from(clone_url, path)
        logger.info(f"Successfully cloned repository from {url}")
    except git.exc.GitCommandError as e:
        logger.error(f"Clone failed for {url}: {e}")
        err_str = str(e).lower()
        if "authentication failed" in err_str or "could not read username" in err_str or "403" in err_str:
            raise GitSyncError("Clone failed: Authentication error. Please check your GitHub Personal Access Token.")
        raise GitSyncError("Clone failed: Could not connect to the repository. Please check the URL and your internet connection.")

    store.update_settings(git_repo_url=url)
    on_progress("Repository connected.", "success")


def init_new(
    store: AppStore, url: str, local_path: Optional[Path] = None, on_progress: ProgressFn = _noop
) -> None:
    """Initialize a local repo (for a brand-new, empty remote) and point it
    at `url` as origin, ready for the first push."""
    path = local_path or default_local_repo_path()
    path.mkdir(parents=True, exist_ok=True)
    repo = git.Repo.init(path)
    if "origin" not in [r.name for r in repo.remotes]:
        repo.create_remote("origin", url)
    store.update_settings(git_repo_url=url)
    on_progress("New local repository initialized.", "success")


def disconnect(store: AppStore, local_path: Optional[Path] = None) -> None:
    path = local_path or default_local_repo_path()
    _force_rmtree(path)
    store.update_settings(git_repo_url=None, last_sync_timestamp=None)


# -------------------------------------------------------------- push/pull
def _write_repo_config(store: AppStore, repo: git.Repo) -> None:
    data = {
        "servers": [s.to_dict() for s in store.servers.values()],
        "jump_hosts": [j.to_dict() for j in store.jump_hosts.values()],
        "keys": [k.to_dict() for k in store.keys.values()],
        "settings": store.settings.to_dict(),
    }
    path = Path(repo.working_tree_dir) / REPO_CONFIG_FILENAME
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _push_with_retry(repo: git.Repo, on_progress: ProgressFn = _noop) -> None:
    """Push the current branch, with set-upstream, retrying once after a
    fetch+fast-forward if the remote moved since we last looked (another
    sync, or - as observed on Windows - a transient stale-ref race right
    after a prior push). A failed fast-forward means a genuine divergence,
    not a race, and is surfaced so the caller pulls (and resolves any
    conflict) before pushing again.
    """
    branch = repo.active_branch.name

    def _push(origin):
        repo.git.push("--set-upstream", origin.name, branch)

    try:
        _with_authed_remote(repo, _push)
    except git.exc.GitCommandError as e:
        if "non-fast-forward" not in str(e) and "rejected" not in str(e):
            logger.error(f"Push failed (GitCommandError): {e}")
            raise GitSyncError(
                "An unexpected error occurred while pushing.\n\n"
                "If this persists, your local Git cache may be corrupted. "
                "You can safely fix this by going to the Git Synchronization tab, clicking 'Disconnect', and reconnecting."
            )
        logger.warning("Push rejected due to non-fast-forward. Retrying after fetch.")
        on_progress("Remote has newer commits - fetching and retrying...", "warning")
        try:
            _with_authed_remote(repo, lambda origin: origin.fetch())
            repo.git.merge(f"origin/{branch}", "--ff-only")
            _with_authed_remote(repo, _push)
            logger.info("Push successful after fetch and fast-forward.")
        except git.exc.GitCommandError as retry_error:
            logger.error(f"Push rejected permanently after retry: {retry_error}")
            raise GitSyncError(
                "Push rejected - the remote repository has changes that are not in your local copy.\n\n"
                "Please pull the latest changes from the Git Synchronization tab first, and then try pushing again."
            )


def push_changes(
    store: AppStore,
    commit_message: str,
    local_path: Optional[Path] = None,
    on_progress: ProgressFn = _noop,
) -> bool:
    """Write the current config into the repo, commit if there's anything
    to commit, and push. Returns False if there was nothing new to push.
    """
    repo = _open_repo(local_path)
    _write_repo_config(store, repo)

    if not repo.is_dirty(untracked_files=True):
        on_progress("Nothing to sync - already up to date.", "info")
        return False

    on_progress("Committing changes...", "info")
    repo.git.add(A=True)
    repo.index.commit(commit_message)

    on_progress("Pushing to remote...", "info")
    _push_with_retry(repo, on_progress)

    store.update_settings(last_sync_timestamp=_now_iso())
    on_progress("Push complete.", "success")
    return True


def pull_changes(
    store: AppStore, local_path: Optional[Path] = None, on_progress: ProgressFn = _noop
) -> tuple[int, int, int]:
    """Pull the latest config from the remote and reconcile the local store
    to match it exactly - the repo is the source of truth, so existing
    hosts are refreshed, new ones are added, and any missing from the repo
    are removed. Returns (added, updated, removed). Raises ConflictError if
    the pull produced merge conflicts.
    """
    repo = _open_repo(local_path)

    on_progress("Pulling from remote...", "info")
    try:
        with repo.config_writer() as w:
            w.set_value("pull", "rebase", "false")
        _with_authed_remote(repo, lambda origin: origin.pull())
        logger.info("Successfully pulled from remote.")
    except git.exc.GitCommandError as e:
        unmerged = repo.index.unmerged_blobs()
        if unmerged:
            logger.warning(f"Merge conflict while pulling: {list(unmerged.keys())}")
            raise ConflictError("Merge conflict while pulling.", list(unmerged.keys()))
        logger.error(f"Pull failed (GitCommandError): {e}")
        raise GitSyncError(
            "An unexpected error occurred while pulling.\n\n"
            "If this persists, your local Git cache may be corrupted. "
            "You can safely fix this by clicking 'Disconnect' and then reconnecting your repository."
        )

    repo_config_path = Path(repo.working_tree_dir) / REPO_CONFIG_FILENAME
    added = updated = removed = 0
    if repo_config_path.exists():
        data = json.loads(repo_config_path.read_text(encoding="utf-8"))

        new_keys = {k["name"]: SSHKey.from_dict(k) for k in data.get("keys", [])}
        for k_name, k in new_keys.items():
            if k_name not in store.keys:
                store.keys[k_name] = k

        new_jump_hosts = {j["name"]: JumpHost.from_dict(j) for j in data.get("jump_hosts", [])}
        for name in list(store.jump_hosts):
            if name not in new_jump_hosts:
                del store.jump_hosts[name]
                removed += 1
        for name, jh in new_jump_hosts.items():
            if name not in store.jump_hosts:
                added += 1
            elif store.jump_hosts[name] != jh:
                updated += 1
            store.jump_hosts[name] = jh

        new_servers = {s["alias"]: Server.from_dict(s) for s in data.get("servers", [])}
        for alias in list(store.servers):
            if alias not in new_servers:
                del store.servers[alias]
                removed += 1
        for alias, s in new_servers.items():
            if alias not in store.servers:
                added += 1
            elif store.servers[alias] != s:
                updated += 1
            store.servers[alias] = s
            
        if "settings" in data:
            new_settings = Settings.from_dict(data["settings"])
            current_url = store.settings.git_repo_url
            store.settings = new_settings
            store.settings.git_repo_url = current_url

        store.save()

    store.update_settings(last_sync_timestamp=_now_iso())
    on_progress("Pull complete.", "success")
    return added, updated, removed


def resolve_conflict(
    strategy: str, local_path: Optional[Path] = None, on_progress: ProgressFn = _noop
) -> None:
    """strategy: 'local' keeps our version and pushes it; 'remote' discards
    local changes in favor of the remote's version."""
    if strategy not in ("local", "remote"):
        raise ValueError("strategy must be 'local' or 'remote'")
    repo = _open_repo(local_path)
    checkout_flag = "--ours" if strategy == "local" else "--theirs"
    repo.git.checkout(checkout_flag, "--", ".")
    repo.git.add(A=True)
    # repo.index.commit() won't do: it doesn't know about MERGE_HEAD, so it
    # leaves the repo "mid-merge" and breaks the next git operation. The
    # actual `git commit` plumbing reads MERGE_HEAD/MERGE_MSG, makes a
    # proper multi-parent merge commit, and clears the merge state.
    repo.git.commit("-m", f"Resolve SSH config sync conflict (kept {strategy} version)")
    if strategy == "local":
        _push_with_retry(repo, on_progress)
    on_progress(f"Conflict resolved, kept {strategy} version.", "success")


def restore_on_new_machine(
    store: AppStore, url: str, local_path: Optional[Path] = None, on_progress: ProgressFn = _noop
) -> tuple[int, int]:
    """Clone the backup repo and populate the local store from it - the
    'set up a new machine from Git' flow."""
    connect_existing(store, url, local_path=local_path, on_progress=on_progress)
    repo = _open_repo(local_path)
    repo_config_path = Path(repo.working_tree_dir) / REPO_CONFIG_FILENAME
    if not repo_config_path.exists():
        return 0, 0

    data = json.loads(repo_config_path.read_text(encoding="utf-8"))
    
    new_keys = [SSHKey.from_dict(k) for k in data.get("keys", [])]
    new_jump_hosts = [JumpHost.from_dict(j) for j in data.get("jump_hosts", [])]
    new_servers = [Server.from_dict(s) for s in data.get("servers", [])]

    imported, skipped = 0, 0
    for key in new_keys:
        if key.name not in store.keys:
            store.keys[key.name] = key
            imported += 1
    for jh in new_jump_hosts:
        if jh.name not in store.jump_hosts:
            store.jump_hosts[jh.name] = jh
            imported += 1
        else:
            skipped += 1
    for server in new_servers:
        if server.alias not in store.servers:
            store.servers[server.alias] = server
            imported += 1
        else:
            skipped += 1

    if "settings" in data:
        new_settings = Settings.from_dict(data["settings"])
        current_url = store.settings.git_repo_url
        store.settings = new_settings
        store.settings.git_repo_url = current_url

    store.save()
    on_progress(f"Restored {imported} entr{'y' if imported == 1 else 'ies'}.", "success")
    return imported, skipped
