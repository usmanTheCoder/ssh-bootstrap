import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from sshmgr import keys as key_ops
from sshmgr.models import JumpHost
from sshmgr.store import ValidationError
from sshmgr.ui.widgets import confirm, notify_error, notify_success

NONE_OPTION = "(none)"


class JumpHostDialog(ctk.CTkToplevel):
    def __init__(self, parent_screen, original_name: str = None):
        super().__init__(parent_screen)
        self.parent_screen = parent_screen
        self.app = parent_screen.app
        self.original_name = original_name
        editing = original_name is not None
        jump_host = self.app.store.jump_hosts[original_name] if editing else None

        self.title("Edit Jump Host" if editing else "Add Jump Host")
        self.geometry("420x560")
        self.transient(parent_screen)
        self.grab_set()

        form = ctk.CTkScrollableFrame(self)
        form.pack(fill="both", expand=True, padx=16, pady=16)

        self.name_entry = self._labeled_entry(form, "Jump Host Name *", jump_host.name if jump_host else "")
        self.hostname_entry = self._labeled_entry(
            form, "Hostname / IP Address *", jump_host.hostname if jump_host else ""
        )
        self.username_entry = self._labeled_entry(
            form, "Username *", jump_host.username if jump_host else ""
        )
        self.port_entry = self._labeled_entry(
            form, "Port", str(jump_host.port) if jump_host else "22"
        )

        ctk.CTkLabel(form, text="Authentication Key", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", pady=(12, 4)
        )
        self.key_mode = ctk.StringVar(value="existing")
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
        if jump_host and jump_host.key_name and jump_host.key_name in existing_names:
            self.existing_key_menu.set(jump_host.key_name)
        self.existing_key_menu.pack(fill="x")

        self.new_key_frame = ctk.CTkFrame(self.key_fields_frame, fg_color="transparent")
        self.new_key_name_entry = self._labeled_entry(self.new_key_frame, "New key name", "")
        ctk.CTkLabel(self.new_key_frame, text="Key type").pack(anchor="w", pady=(10, 2))
        self.new_key_type_menu = ctk.CTkOptionMenu(self.new_key_frame, values=["rsa", "ed25519"])
        self.new_key_type_menu.pack(fill="x")

        if not jump_host or not jump_host.key_name:
            self.key_mode.set("existing")

        ctk.CTkLabel(
            form, text="Additional SSH Options (one per line)", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(16, 4))
        self.extra_options_box = ctk.CTkTextbox(form, height=80)
        self.extra_options_box.pack(fill="x")
        if jump_host and jump_host.extra_options:
            self.extra_options_box.insert("1.0", jump_host.extra_options)

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(button_row, text="Cancel", fg_color="gray40", command=self.destroy).pack(
            side="right", padx=(8, 0)
        )
        ctk.CTkButton(button_row, text="Save", command=self._save).pack(side="right")

        self._update_key_mode()

    def _labeled_entry(self, parent, label, default):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", pady=(10, 2))
        entry = ctk.CTkEntry(parent)
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

    def _resolve_key_name(self):
        mode = self.key_mode.get()
        if mode == "skip":
            return None
        if mode == "existing":
            value = self.existing_key_menu.get()
            return None if value == NONE_OPTION else value
        name = self.new_key_name_entry.get().strip()
        key_type = self.new_key_type_menu.get()
        new_key = key_ops.generate(name, key_type=key_type)
        self.app.store.add_key(new_key)
        return new_key.name

    def _save(self):
        name = self.name_entry.get().strip()
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

        jump_host = JumpHost(
            name=name,
            hostname=hostname,
            username=username,
            port=port,
            key_name=key_name,
            extra_options=self.extra_options_box.get("1.0", "end").strip(),
        )

        try:
            if self.original_name:
                self.app.store.update_jump_host(self.original_name, jump_host)
            else:
                self.app.store.add_jump_host(jump_host)
        except ValidationError as e:
            notify_error(self, "Validation Error", str(e))
            return

        if not self.app.sync_ssh_config():
            return

        self.parent_screen.refresh()
        self.destroy()
        notify_success(
            self.app, "Jump Host Saved",
            f"'{name}' has been saved. All dependent servers were updated in the SSH config.",
        )
        action = "Updated" if self.original_name else "Added"
        self.app.prompt_git_sync(f"{action} jump host '{name}'")


class JumpHostsScreen(ctk.CTkFrame):
    COLUMNS = ("name", "hostname", "username", "port", "dependents")

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(header, text="Jump Hosts", font=ctk.CTkFont(size=22, weight="bold"), text_color=("#111827", "#F9FAFB")).pack(
            side="left"
        )
        ctk.CTkButton(header, text="+ Add Jump Host", command=self._open_add_dialog).pack(
            side="right"
        )

        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table_frame, columns=self.COLUMNS, show="headings", selectmode="browse"
        )
        headings = {
            "name": "Name", "hostname": "Hostname/IP", "username": "Username",
            "port": "Port", "dependents": "Dependent Servers",
        }
        for col in self.COLUMNS:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=150)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(action_row, text="Edit", command=self._edit_selected).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            action_row, text="Delete", fg_color="#ef4444", hover_color="#b91c1c",
            command=self._delete_selected,
        ).pack(side="left")

        self.refresh()

    def on_show(self):
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for jh in self.app.store.list_jump_hosts():
            dependents = self.app.store.servers_using_jump_host(jh.name)
            dependents_text = ", ".join(s.alias for s in dependents) if dependents else "-"
            self.tree.insert(
                "", "end", iid=jh.name,
                values=(jh.name, jh.hostname, jh.username, jh.port, dependents_text),
            )

    def _selected_name(self):
        selection = self.tree.selection()
        return selection[0] if selection else None

    def _open_add_dialog(self):
        JumpHostDialog(self)

    def _edit_selected(self):
        name = self._selected_name()
        if not name:
            notify_error(self, "No Selection", "Select a jump host first.")
            return
        JumpHostDialog(self, original_name=name)

    def _delete_selected(self):
        name = self._selected_name()
        if not name:
            notify_error(self, "No Selection", "Select a jump host first.")
            return

        dependents = self.app.store.servers_using_jump_host(name)
        if dependents:
            aliases = ", ".join(s.alias for s in dependents)
            message = (
                f"Jump Host '{name}' is used by: {aliases}.\n\n"
                "Deleting it will remove ProxyJump from these servers. Continue?"
            )
        else:
            message = f"Delete jump host '{name}'? This cannot be undone."

        if not confirm(self, "Delete Jump Host", message):
            return

        self.app.store.delete_jump_host(name)
        self.app.sync_ssh_config()
        self.refresh()
        notify_success(self, "Deleted", f"'{name}' was removed and the SSH config was updated.")
        self.app.prompt_git_sync(f"Deleted jump host '{name}'")
