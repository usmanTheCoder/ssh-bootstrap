import pytest
import customtkinter as ctk

from sshmgr.store import AppStore
from sshmgr.models import Server, JumpHost
from sshmgr.ui.app import MainApp

@pytest.fixture
def store(tmp_path):
    return AppStore(path=tmp_path / "data.json")

def test_app_initialization(store):
    app = MainApp()
    app.store = store
    # verify screens exist
    assert "dashboard" in app.screens
    assert "servers" in app.screens
    assert "jump_hosts" in app.screens
    assert "keys" in app.screens
    assert "ssh_config" in app.screens
    assert "git_sync" in app.screens
    assert "settings" in app.screens
    
    app.update() # process events
    app.destroy()

def test_dashboard_stats(store):
    # Add data
    store.add_jump_host(JumpHost(name="jh1", hostname="1.1.1.1", username="root"))
    store.add_server(Server(alias="web1", hostname="2.2.2.2", username="user"))
    
    app = MainApp()
    app.store = store
    dashboard = app.screens["dashboard"]
    dashboard.refresh()
    
    assert dashboard.servers_card.value_label.cget("text") == "1"
    assert dashboard.jump_hosts_card.value_label.cget("text") == "1"
    
    app.update()
    app.destroy()
