import pytest
import time
from sshmgr.store import AppStore
from sshmgr.ui.app import MainApp

@pytest.fixture
def empty_store(tmp_path, monkeypatch):
    # Create an isolated empty store for the test
    store_path = tmp_path / "data.json"
    store = AppStore(path=store_path)
    
    # We must patch the global default paths so the app doesn't touch the real system
    monkeypatch.setattr("sshmgr.ssh_config.default_config_path", lambda: tmp_path / "config")
    
    return store

def test_comprehensive_e2e_journey(empty_store, monkeypatch):
    """
    Simulates a full user journey:
    1. Verify Empty Dashboard
    2. Add Jump Host
    3. Add Server (using Jump Host)
    4. Verify Dashboard Counts
    5. Verify SSH Config Output
    6. Delete Server & Verify Dashboard
    """
    app = MainApp()
    app.store = empty_store
    app.update()

    # Disable confirmation dialogs so they don't block the test
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda title, msg: True)
    monkeypatch.setattr("sshmgr.ui.servers.confirm", lambda parent, title, msg: True)
    monkeypatch.setattr("sshmgr.ui.jump_hosts.confirm", lambda parent, title, msg: True)
    monkeypatch.setattr("sshmgr.ui.servers.notify_error", lambda parent, title, msg: print(f"ERROR: {msg}"))
    monkeypatch.setattr("sshmgr.ui.jump_hosts.notify_error", lambda parent, title, msg: print(f"ERROR: {msg}"))

    dashboard = app.screens["dashboard"]
    servers_screen = app.screens["servers"]
    jump_hosts_screen = app.screens["jump_hosts"]
    ssh_config_screen = app.screens["ssh_config"]
    
    # ==========================================
    # PHASE 0: Verify initial state
    # ==========================================
    dashboard.refresh()
    assert dashboard.servers_card.value_label.cget("text") == "0"
    assert dashboard.jump_hosts_card.value_label.cget("text") == "0"
    
    # ==========================================
    # PHASE 0.5: Verify UI Rendering & Layout
    # ==========================================
    # Check that sidebar renders properly
    assert len(app.nav_buttons) >= 5, "Sidebar should render navigation buttons"
    
    # Check that Servers Screen renders correctly
    app.show_screen("servers")
    app.update()
    assert servers_screen.winfo_ismapped() == 1, "Servers screen should be visible"
    
    # Check Treeview Columns
    columns = servers_screen.tree["columns"]
    assert "alias" in columns
    assert "hostname" in columns
    assert "username" in columns
    
    # Verify action buttons on Servers screen
    action_buttons = [c for c in servers_screen.winfo_children()[-1].winfo_children() if "ctkbutton" in str(type(c)).lower()]
    action_labels = [b.cget("text") for b in action_buttons]
    assert "Edit" in action_labels
    assert "Duplicate" in action_labels
    assert "Delete" in action_labels

    # ==========================================
    # PHASE 1: Add Jump Host
    # ==========================================
    app.show_screen("jump_hosts")
    
    # Open dialog
    jump_hosts_screen._open_add_dialog()
    app.update()
    
    # Grab the dialog instance that was created
    dialogs = [c for c in app.winfo_children() if "toplevel" in str(type(c)).lower() or "dialog" in str(type(c)).lower()]
    if not dialogs:
        dialogs = [c for c in jump_hosts_screen.winfo_children() if "toplevel" in str(type(c)).lower() or "dialog" in str(type(c)).lower()]
    
    dialog = dialogs[-1]
    
    # Fill in the form programmatically
    dialog.name_entry.insert(0, "bastion-01")
    dialog.hostname_entry.insert(0, "10.0.0.1")
    dialog.username_entry.insert(0, "admin")
    dialog.key_mode.set("skip")
    
    # Trigger Save
    dialog._save()
    app.update()
    
    # Verify internal store saved it
    assert "bastion-01" in empty_store.list_jump_hosts()[0].name
    
    # ==========================================
    # PHASE 2: Add Server using Jump Host
    # ==========================================
    app.show_screen("servers")
    
    servers_screen.open_add_dialog()
    app.update()
    
    dialogs = [c for c in app.winfo_children() if "toplevel" in str(type(c)).lower() or "dialog" in str(type(c)).lower()]
    if not dialogs:
        dialogs = [c for c in servers_screen.winfo_children() if "toplevel" in str(type(c)).lower() or "dialog" in str(type(c)).lower()]
        
    dialog = dialogs[-1]
    
    dialog.alias_entry.insert(0, "prod-db")
    dialog.hostname_entry.insert(0, "192.168.1.50")
    dialog.username_entry.insert(0, "dbuser")
    dialog.key_mode.set("skip")
    
    # Select Jump Host from OptionMenu
    dialog.jump_host_menu.set("bastion-01")
    
    dialog._save()
    app.update()
    
    # Verify internal store
    server = empty_store.servers["prod-db"]
    assert server.jump_host == "bastion-01"
    
    # ==========================================
    # PHASE 3: Dashboard Verification
    # ==========================================
    app.show_screen("dashboard")
    dashboard.refresh()
    app.update()
    
    assert dashboard.servers_card.value_label.cget("text") == "1"
    assert dashboard.jump_hosts_card.value_label.cget("text") == "1"
    
    # ==========================================
    # PHASE 4: SSH Config Generation Check
    # ==========================================
    app.show_screen("ssh_config")
    ssh_config_screen.refresh()
    app.update()
    
    config_text = ssh_config_screen.text_box.get("1.0", "end")
    assert "Host bastion-01" in config_text
    assert "Host prod-db" in config_text
    assert "ProxyJump bastion-01" in config_text
    
    # ==========================================
    # PHASE 4.5: Edit Server Alias
    # ==========================================
    app.show_screen("servers")
    
    # Mock selection
    monkeypatch.setattr(servers_screen, "_selected_alias", lambda: "prod-db")
    servers_screen._edit_selected()
    app.update()
    
    dialogs = [c for c in app.winfo_children() if "toplevel" in str(type(c)).lower() or "dialog" in str(type(c)).lower()]
    if not dialogs:
        dialogs = [c for c in servers_screen.winfo_children() if "toplevel" in str(type(c)).lower() or "dialog" in str(type(c)).lower()]
        
    dialog = dialogs[-1]
    
    # Change the alias
    dialog.alias_entry.delete(0, "end")
    dialog.alias_entry.insert(0, "db-renamed")
    
    dialog._save()
    app.update()
    
    # Verify internal store updated
    assert "prod-db" not in empty_store.servers
    assert "db-renamed" in empty_store.servers
    
    # Verify SSH config updated
    app.show_screen("ssh_config")
    ssh_config_screen.refresh()
    app.update()
    
    config_text = ssh_config_screen.text_box.get("1.0", "end")
    assert "Host db-renamed" in config_text
    assert "Host prod-db\n" not in config_text

    # ==========================================
    # PHASE 5: Deletion Cleanup
    # ==========================================
    app.show_screen("servers")
    
    # Mock selection and trigger delete
    monkeypatch.setattr(servers_screen, "_selected_alias", lambda: "db-renamed")
    servers_screen._delete_selected()
    app.update()
    
    # Verify store
    assert "db-renamed" not in empty_store.servers
    
    app.show_screen("dashboard")
    dashboard.refresh()
    assert dashboard.servers_card.value_label.cget("text") == "0"
    
    app.destroy()
