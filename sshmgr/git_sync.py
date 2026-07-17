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
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import git
import keyring
import requests

from sshmgr import ssh_config
from sshmgr.store import AppStore

SERVICE_NAME = "ssh-bootstrap-manager"
TOKEN_KEY = "github-pat"
REPO_CONFIG_FILENAME = "ssh_config"

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
    if path.exists():
        shutil.rmtree(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    token = get_token()
    clone_url = _authed_url(url, token) if token else url
    on_progress(f"Cloning {url}...", "info")
    try:
        git.Repo.clone_from(clone_url, path)
    except git.exc.GitCommandError as e:
        raise GitSyncError(f"Clone failed: {e}")

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
    if path.exists():
        shutil.rmtree(path)
    store.update_settings(git_repo_url=None, last_sync_timestamp=None)


# -------------------------------------------------------------- push/pull
def _write_repo_config(store: AppStore, repo: git.Repo) -> None:
    ssh_config.export(store, Path(repo.working_tree_dir) / REPO_CONFIG_FILENAME)


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
            raise GitSyncError(f"Push failed: {e}")
        on_progress("Remote has newer commits - fetching and retrying...", "warning")
        try:
            _with_authed_remote(repo, lambda origin: origin.fetch())
            repo.git.merge(f"origin/{branch}", "--ff-only")
            _with_authed_remote(repo, _push)
        except git.exc.GitCommandError as retry_error:
            raise GitSyncError(
                f"Push rejected - the remote has changes not in your local copy. "
                f"Pull first, then push again. ({retry_error})"
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
        _with_authed_remote(repo, lambda origin: origin.pull())
    except git.exc.GitCommandError as e:
        unmerged = repo.index.unmerged_blobs()
        if unmerged:
            raise ConflictError("Merge conflict while pulling.", list(unmerged.keys()))
        raise GitSyncError(f"Pull failed: {e}")

    repo_config_path = Path(repo.working_tree_dir) / REPO_CONFIG_FILENAME
    added = updated = removed = 0
    if repo_config_path.exists():
        servers, jump_hosts, keys = ssh_config.import_existing(repo_config_path)

        for key in keys:
            if key.name not in store.keys:
                store.keys[key.name] = key

        new_jump_hosts = {jh.name: jh for jh in jump_hosts}
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

        new_servers = {s.alias: s for s in servers}
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

    servers, jump_hosts, keys = ssh_config.import_existing(repo_config_path)
    imported, skipped = 0, 0
    for key in keys:
        if key.name not in store.keys:
            store.keys[key.name] = key
            imported += 1
    for jh in jump_hosts:
        if jh.name not in store.jump_hosts:
            store.jump_hosts[jh.name] = jh
            imported += 1
        else:
            skipped += 1
    for server in servers:
        if server.alias not in store.servers:
            store.servers[server.alias] = server
            imported += 1
        else:
            skipped += 1
    store.save()
    on_progress(f"Restored {imported} entr{'y' if imported == 1 else 'ies'}.", "success")
    return imported, skipped
