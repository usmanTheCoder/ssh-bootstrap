import git
import pytest

from sshmgr import git_sync
from sshmgr.store import AppStore
from sshmgr.models import Server, JumpHost, SSHKey
from sshmgr import ssh_config

def _set_identity(repo: git.Repo):
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test User")
        cw.set_value("user", "email", "test@example.com")
        cw.set_value("pull", "rebase", "false")


@pytest.fixture
def e2e_setup(tmp_path):
    bare_repo = tmp_path / "bare.git"
    git.Repo.init(str(bare_repo), bare=True)
    
    store_path = tmp_path / "data.json"
    store = AppStore(path=store_path)
    
    local_repo_path = tmp_path / "local_repo"
    git_sync.init_new(store, str(bare_repo), local_path=local_repo_path)
    _set_identity(git.Repo(local_repo_path))
    
    ssh_config_path = tmp_path / "config"
    
    return store, local_repo_path, ssh_config_path

def test_end_to_end_workflow(e2e_setup):
    store, local_repo_path, ssh_config_path = e2e_setup
    
    # --- ADD SERVER WORKFLOW ---
    # Add Key
    store.add_key(SSHKey(name="prod_key", private_key_path="/.ssh/prod", public_key_path="/.ssh/prod.pub"))
    # Assign Jump Host
    store.add_jump_host(JumpHost(name="prod_bastion", hostname="bastion.prod.com", username="admin"))
    # Add Server
    store.add_server(Server(alias="prod_db", hostname="10.0.0.5", username="postgres", key_name="prod_key", jump_host="prod_bastion"))
    
    # Verify server appears in list
    assert "prod_db" in store.servers
    
    # Verify SSH config updates
    ssh_config.write(store, config_path=ssh_config_path)
    content = ssh_config_path.read_text(encoding="utf-8")
    assert "Host prod_db" in content
    assert "ProxyJump prod_bastion" in content
    assert "IdentityFile /.ssh/prod" in content
    
    # Verify Git repository updates
    pushed = git_sync.push_changes(store, "Added prod_db", local_path=local_repo_path)
    assert pushed is True
    assert store.settings.last_sync_timestamp is not None
    
    # --- EDIT WORKFLOW ---
    store.update_server("prod_db", Server(alias="prod_db", hostname="10.0.0.6", username="postgres", key_name="prod_key", jump_host="prod_bastion"))
    ssh_config.write(store, config_path=ssh_config_path)
    content = ssh_config_path.read_text(encoding="utf-8")
    assert "10.0.0.6" in content
    
    pushed = git_sync.push_changes(store, "Edited prod_db", local_path=local_repo_path)
    assert pushed is True
    
    # --- JUMP HOST WORKFLOW ---
    # Modify Jump Host
    store.update_jump_host("prod_bastion", JumpHost(name="prod_bastion_v2", hostname="bastion2.prod.com", username="admin"))
    # Verify linked servers update
    assert store.servers["prod_db"].jump_host == "prod_bastion_v2"
    
    ssh_config.write(store, config_path=ssh_config_path)
    content = ssh_config_path.read_text(encoding="utf-8")
    assert "ProxyJump prod_bastion_v2" in content
    assert "Host prod_bastion_v2" in content
    
    pushed = git_sync.push_changes(store, "Edited jump host", local_path=local_repo_path)
    assert pushed is True
    
    # --- DELETE WORKFLOW ---
    store.delete_server("prod_db")
    assert "prod_db" not in store.servers
    
    ssh_config.write(store, config_path=ssh_config_path)
    content = ssh_config_path.read_text(encoding="utf-8")
    assert "Host prod_db" not in content
    
    pushed = git_sync.push_changes(store, "Deleted prod_db", local_path=local_repo_path)
    assert pushed is True
