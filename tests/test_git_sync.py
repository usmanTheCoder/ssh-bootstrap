"""Exercises the git mechanics (clone/push/pull/conflict) against local
bare repos acting as the 'remote' - no GitHub/network access needed, since
git itself doesn't care whether the remote is a local path or a URL. Token
handling (keyring, GitHub API validation) is a thin wrapper tested only by
inspection, not here.
"""
import git
import pytest

from sshmgr import git_sync
from sshmgr.store import AppStore
from sshmgr.models import Server


def _set_identity(repo: git.Repo):
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test User")
        cw.set_value("user", "email", "test@example.com")


@pytest.fixture
def bare_repo(tmp_path):
    bare_path = tmp_path / "bare.git"
    git.Repo.init(str(bare_path), bare=True)
    return bare_path


def _store(tmp_path, name):
    return AppStore(path=tmp_path / f"{name}.json")


def test_init_new_and_push(tmp_path, bare_repo):
    store = _store(tmp_path, "a")
    local_path = tmp_path / "repoA"
    git_sync.init_new(store, str(bare_repo), local_path=local_path)
    _set_identity(git.Repo(local_path))

    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    pushed = git_sync.push_changes(store, "add web1", local_path=local_path)
    assert pushed is True
    assert store.settings.last_sync_timestamp is not None

    # nothing changed -> second push is a no-op
    pushed_again = git_sync.push_changes(store, "add web1 again", local_path=local_path)
    assert pushed_again is False

    # verify the bare repo actually received the commit
    verify_path = tmp_path / "verify"
    git.Repo.clone_from(str(bare_repo), verify_path)
    content = (verify_path / git_sync.REPO_CONFIG_FILENAME).read_text()
    assert "Host web1" in content


def test_connect_existing_and_pull_populates_store(tmp_path, bare_repo):
    store_a = _store(tmp_path, "a")
    path_a = tmp_path / "repoA"
    git_sync.init_new(store_a, str(bare_repo), local_path=path_a)
    _set_identity(git.Repo(path_a))
    store_a.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    git_sync.push_changes(store_a, "add web1", local_path=path_a)

    store_b = _store(tmp_path, "b")
    path_b = tmp_path / "repoB"
    git_sync.connect_existing(store_b, str(bare_repo), local_path=path_b)
    assert (path_b / git_sync.REPO_CONFIG_FILENAME).exists()

    added, updated, removed = git_sync.pull_changes(store_b, local_path=path_b)
    assert added == 1
    assert updated == 0
    assert removed == 0
    assert "web1" in store_b.servers


def test_pull_conflict_is_detected_and_resolvable(tmp_path, bare_repo):
    store_a = _store(tmp_path, "a")
    path_a = tmp_path / "repoA"
    git_sync.init_new(store_a, str(bare_repo), local_path=path_a)
    _set_identity(git.Repo(path_a))
    store_a.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    git_sync.push_changes(store_a, "add web1", local_path=path_a)

    store_b = _store(tmp_path, "b")
    path_b = tmp_path / "repoB"
    git_sync.connect_existing(store_b, str(bare_repo), local_path=path_b)
    _set_identity(git.Repo(path_b))
    git_sync.pull_changes(store_b, local_path=path_b)  # populate store_b from the clone

    # Both sides edit the SAME server's hostname differently without syncing in between
    store_a.update_server("web1", Server(alias="web1", hostname="9.9.9.9", username="root"))
    git_sync.push_changes(store_a, "change web1 hostname (A)", local_path=path_a)

    store_b.update_server("web1", Server(alias="web1", hostname="8.8.8.8", username="root"))
    # Write+commit locally in B without pulling first, so history has diverged
    repo_b = git.Repo(path_b)
    from sshmgr import ssh_config as ssh_config_mod
    ssh_config_mod.export(store_b, path_b / git_sync.REPO_CONFIG_FILENAME)
    repo_b.git.add(A=True)
    repo_b.index.commit("change web1 hostname (B)")

    with pytest.raises(git_sync.ConflictError) as excinfo:
        git_sync.pull_changes(store_b, local_path=path_b)
    assert git_sync.REPO_CONFIG_FILENAME in excinfo.value.conflicted_files

    # Resolve by keeping the local (B) version and pushing it
    git_sync.resolve_conflict("local", local_path=path_b)
    content = (path_b / git_sync.REPO_CONFIG_FILENAME).read_text()
    assert "8.8.8.8" in content

    # A pulling afterwards should now cleanly get B's resolved version -
    # pull treats the repo as source of truth, so A's store is refreshed
    added, updated, removed = git_sync.pull_changes(store_a, local_path=path_a)
    assert updated == 1
    assert store_a.servers["web1"].hostname == "8.8.8.8"


def test_restore_on_new_machine(tmp_path, bare_repo):
    store_a = _store(tmp_path, "a")
    path_a = tmp_path / "repoA"
    git_sync.init_new(store_a, str(bare_repo), local_path=path_a)
    _set_identity(git.Repo(path_a))
    store_a.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    git_sync.push_changes(store_a, "add web1", local_path=path_a)

    store_new = _store(tmp_path, "new_machine")
    path_new = tmp_path / "repoNew"
    imported, skipped = git_sync.restore_on_new_machine(store_new, str(bare_repo), local_path=path_new)
    assert imported == 1
    assert "web1" in store_new.servers


def test_disconnect_removes_local_repo(tmp_path, bare_repo):
    store = _store(tmp_path, "a")
    local_path = tmp_path / "repoA"
    git_sync.init_new(store, str(bare_repo), local_path=local_path)
    assert local_path.exists()
    git_sync.disconnect(store, local_path=local_path)
    assert not local_path.exists()
    assert store.settings.git_repo_url is None
