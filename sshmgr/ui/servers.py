import threading
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from sshmgr import keys as key_ops
from sshmgr import deploy
from sshmgr.models import Server
from sshmgr.store import ValidationError
from sshmgr.ui.widgets import confirm, notify_error, notify_success, ProgressDialog

NONE_OPTION = "(none)"


class ServerDialog(ctk.CTkToplevel):
    def __init__(self, parent_screen, original_alias: str = None):
        super().__init__(parent_screen)
        self.parent_screen = parent_screen
        self.app = parent_screen.app
        self.original_alias = original_alias
        editing = original_alias is not None
        server = self.app.store.servers[original_alias] if editing else None

        self.title("Edit Server" if editing else "Add Server/VM")
        self.geometry("460x640")
        self.transient(parent_screen)
        self.grab_set()

        form = ctk.CTkScrollableFrame(self)
        form.pack(fill="both", expand=True, padx=16, pady=16)

        self.alias_entry = self._labeled_entry(form, "Host Alias *", server.alias if server else "")
        self.hostname_entry = self._labeled_entry(
            form, "Hostname / IP Address *", server.hostname if server else ""
        )
        self.username_entry = self._labeled_entry(form, "Username *", server.username if server else "")
        self.port_entry = self._labeled_entry(
            form, "Port", str(server.port) if server else "22"
        )

        ctk.CTkLabel(form, text="Authentication Key", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", pady=(12, 4)
        )
        self.key_mode = ctk.StringVar(
            value="existing" if (server and server.key_name) else "existing"
        )
        mode_row = ctk.CTkFrame(form, fg_color="transparent")
        mode_row.pack(fill="x")
        ctk.CTkRadioButton(
            mode_row, text="Use existing key", variable=self.key_mode, value="existing",
            command=self._update_key_mode,
        ).pack(anchor="w")
        ctk.CTkRadioButton(
            mode_row, text="Generate a new key", variable=self.key_mode, value="generate",
            command=self._update_key_mode,
        ).pack(anchor="w")
        ctk.CTkRadioButton(
            mode_row, text="Skip (authentication managed separately)", variable=self.key_mode,
            value="skip", command=self._update_key_mode,
        ).pack(anchor="w")

        self.key_fields_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.key_fields_frame.pack(fill="x", pady=(6, 0))

        self.existing_key_frame = ctk.CTkFrame(self.key_fields_frame, fg_color="transparent")
        existing_names = [k.name for k in self.app.store.list_keys()] or [NONE_OPTION]
        self.existing_key_menu = ctk.CTkOptionMenu(self.existing_key_frame, values=existing_names)
        if server and server.key_name and server.key_name in existing_names:
            self.existing_key_menu.set(server.key_name)
        self.existing_key_menu.pack(fill="x")

        self.new_key_frame = ctk.CTkFrame(self.key_fields_frame, fg_color="transparent")
        self.new_key_name_entry = self._labeled_entry(self.new_key_frame, "New key name", "")
        ctk.CTkLabel(self.new_key_frame, text="Key type").pack(anchor="w", pady=(10, 2))
        self.new_key_type_menu = ctk.CTkOptionMenu(self.new_key_frame, values=["rsa", "ed25519"])
        self.new_key_type_menu.pack(fill="x")

        if not server or not server.key_name:
            self.key_mode.set("existing")

        ctk.CTkLabel(form, text="Jump Host (optional)", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", pady=(16, 4)
        )
        jump_host_names = [NONE_OPTION] + [j.name for j in self.app.store.list_jump_hosts()]
        self.jump_host_menu = ctk.CTkOptionMenu(form, values=jump_host_names)
        if server and server.jump_host in jump_host_names:
            self.jump_host_menu.set(server.jump_host)
        else:
            self.jump_host_menu.set(NONE_OPTION)
        self.jump_host_menu.pack(fill="x")

        ctk.CTkLabel(
            form, text="Additional SSH Options (one per line)", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(16, 4))
        self.extra_options_box = ctk.CTkTextbox(form, height=80)
        self.extra_options_box.pack(fill="x")
        if server and server.extra_options:
            self.extra_options_box.insert("1.0", server.extra_options)

        self.deploy_var = ctk.BooleanVar(value=False)
        self.deploy_check = ctk.CTkCheckBox(
            form,
            text="Deploy key to this server now (requires password)",
            variable=self.deploy_var,
            command=self._update_deploy_row,
        )
        self.deploy_check.pack(anchor="w", pady=(16, 4))
        
        self.password_container = ctk.CTkFrame(form, fg_color="transparent")
        self.password_container.pack(fill="x")
        self.password_frame = ctk.CTkFrame(self.password_container, fg_color="transparent")
        self.password_entry = self._labeled_entry(self.password_frame, "Password", "", show="*")

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(button_row, text="Cancel", fg_color="gray40", command=self.destroy).pack(
            side="right", padx=(8, 0)
        )
        ctk.CTkButton(button_row, text="Save", command=self._save).pack(side="right")

        self._update_key_mode()
        self._update_deploy_row()

    def _labeled_entry(self, parent, label, default, show=None):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", pady=(10, 2))
        entry = ctk.CTkEntry(parent, show=show)
        entry.insert(0, default)
        entry.pack(fill="x")
        return entry

    def _update_key_mode(self):
        mode = self.key_mode.get()
        self.existing_key_frame.pack_forget()
        self.new_key_frame.pack_forget()
        
        if mode == "existing":
            self.existing_key_frame.pack(fill="x")
        elif mode == "generate":
            self.new_key_frame.pack(fill="x")

    def _update_deploy_row(self):
        if self.deploy_var.get():
            self.password_frame.pack(fill="x")
        else:
            self.password_frame.pack_forget()

    def _resolve_key_name(self):
        mode = self.key_mode.get()
        if mode == "skip":
            return None
        if mode == "existing":
            value = self.existing_key_menu.get()
            return None if value == NONE_OPTION else value
        # generate
        name = self.new_key_name_entry.get().strip()
        key_type = self.new_key_type_menu.get()
        new_key = key_ops.generate(name, key_type=key_type)
        self.app.store.add_key(new_key)
        return new_key.name

    def _save(self):
        alias = self.alias_entry.get().strip()
        hostname = self.hostname_entry.get().strip()
        username = self.username_entry.get().strip()
        port_text = self.port_entry.get().strip()

        if not port_text.isdigit():
            notify_error(self, "Invalid Port", "Port must be a number.")
            return
        port = int(port_text)

        try:
            key_name = self._resolve_key_name()
        except key_ops.KeyError_ as e:
            notify_error(self, "Key Error", str(e))
            return

        jump_host_value = self.jump_host_menu.get()
        jump_host = None if jump_host_value == NONE_OPTION else jump_host_value

        server = Server(
            alias=alias,
            hostname=hostname,
            username=username,
            port=port,
            key_name=key_name,
            jump_host=jump_host,
            extra_options=self.extra_options_box.get("1.0", "end").strip(),
        )

        try:
            if self.original_alias:
                self.app.store.update_server(self.original_alias, server)
            else:
                self.app.store.add_server(server)
        except ValidationError as e:
            notify_error(self, "Validation Error", str(e))
            return

        if not self.app.sync_ssh_config():
            return

        if self.deploy_var.get() and key_name:
            self._run_deploy(server, key_name)

        self.parent_screen.refresh()
        self.destroy()
        # Parent post-destroy popups to self.app, not this now-destroyed
        # dialog - a Toplevel can't be a valid master once it's gone.
        notify_success(self.app, "Server Saved", f"'{alias}' has been saved and the SSH config was updated.")
        action = "Updated" if self.original_alias else "Added"
        self.app.prompt_git_sync(f"{action} server '{alias}'")

    def _run_deploy(self, server: Server, key_name: str):
        password = self.password_entry.get()
        public_key_path = self.app.store.keys[key_name].public_key_path
        # Parented to self.app (not this dialog) so it survives the dialog
        # closing while the deploy still runs in the background.
        progress = ProgressDialog(self.app, title=f"Deploying key to {server.alias}")

        def worker():
            ok = deploy.deploy_key(
                server.hostname, server.username, password, public_key_path,
                port=server.port, on_progress=progress.log,
            )
            if ok:
                deploy.test_passwordless(
                    server.hostname, server.username, port=server.port,
                    on_progress=progress.log,
                )
            progress.finish()

        threading.Thread(target=worker, daemon=True).start()


class ServersScreen(ctk.CTkFrame):
    COLUMNS = ("alias", "hostname", "username", "port", "jump_host")

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(header, text="Servers", font=ctk.CTkFont(size=22, weight="bold"), text_color=("#111827", "#F9FAFB")).pack(
            side="left"
        )
        ctk.CTkButton(header, text="+ Add Server/VM", command=self.open_add_dialog).pack(
            side="right"
        )

        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", pady=(0, 10))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Search by alias or hostname...",
            textvariable=self.search_var,
        )
        search_entry.pack(fill="x")

        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table_frame, columns=self.COLUMNS, show="headings", selectmode="browse"
        )
        headings = {
            "alias": "Host Alias", "hostname": "Hostname/IP", "username": "Username",
            "port": "Port", "jump_host": "Jump Host",
        }
        for col in self.COLUMNS:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=140)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(action_row, text="Edit", command=self._edit_selected).pack(side="left", padx=(0, 8))
        ctk.CTkButton(action_row, text="Duplicate", command=self._duplicate_selected).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            action_row, text="Delete", fg_color="#ef4444", hover_color="#b91c1c",
            command=self._delete_selected,
        ).pack(side="left")

        self.refresh()

    def on_show(self):
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        query = self.search_var.get()
        for server in self.app.store.search_servers(query):
            self.tree.insert(
                "", "end", iid=server.alias,
                values=(server.alias, server.hostname, server.username, server.port, server.jump_host or ""),
            )

    def _selected_alias(self):
        selection = self.tree.selection()
        return selection[0] if selection else None

    def open_add_dialog(self):
        ServerDialog(self)

    def _edit_selected(self):
        alias = self._selected_alias()
        if not alias:
            notify_error(self, "No Selection", "Select a server first.")
            return
        ServerDialog(self, original_alias=alias)

    def _duplicate_selected(self):
        alias = self._selected_alias()
        if not alias:
            notify_error(self, "No Selection", "Select a server first.")
            return
        new_alias = f"{alias}-copy"
        suffix = 2
        while new_alias in self.app.store.servers:
            new_alias = f"{alias}-copy{suffix}"
            suffix += 1
        try:
            self.app.store.duplicate_server(alias, new_alias)
        except ValidationError as e:
            notify_error(self, "Duplicate Failed", str(e))
            return
        self.app.sync_ssh_config()
        self.refresh()
        self.app.prompt_git_sync(f"Duplicated server '{alias}' as '{new_alias}'")

    def _delete_selected(self):
        alias = self._selected_alias()
        if not alias:
            notify_error(self, "No Selection", "Select a server first.")
            return
        if not confirm(self, "Delete Server", f"Delete server '{alias}'? This cannot be undone."):
            return
        self.app.store.delete_server(alias)
        self.app.sync_ssh_config()
        self.refresh()
        notify_success(self, "Deleted", f"'{alias}' was removed and the SSH config was updated.")
        self.app.prompt_git_sync(f"Deleted server '{alias}'")
