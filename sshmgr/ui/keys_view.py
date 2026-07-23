import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from sshmgr import keys as key_ops
from sshmgr.ui.widgets import confirm, notify_error, notify_success


class GenerateKeyDialog(ctk.CTkToplevel):
    def __init__(self, parent_screen):
        super().__init__(parent_screen)
        self.parent_screen = parent_screen
        self.title("Generate SSH Key")
        self.geometry("360x260")
        self.transient(parent_screen)
        self.grab_set()

        ctk.CTkLabel(self, text="Key name").pack(anchor="w", padx=16, pady=(16, 4))
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.insert(0, "id_rsa")
        self.name_entry.pack(fill="x", padx=16)

        ctk.CTkLabel(self, text="Key type").pack(anchor="w", padx=16, pady=(12, 4))
        self.type_menu = ctk.CTkOptionMenu(self, values=["rsa", "ed25519"])
        self.type_menu.pack(fill="x", padx=16)

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x", padx=16, pady=20)
        ctk.CTkButton(button_row, text="Cancel", fg_color="gray40", command=self.destroy).pack(
            side="right", padx=(8, 0)
        )
        ctk.CTkButton(button_row, text="Generate", command=self._generate).pack(side="right")

    def _generate(self):
        name = self.name_entry.get().strip()
        key_type = self.type_menu.get()
        try:
            new_key = key_ops.generate(name, key_type=key_type)
            self.parent_screen.app.store.add_key(new_key)
        except (key_ops.KeyError_, Exception) as e:
            notify_error(self, "Key Generation Failed", str(e))
            return
        self.parent_screen.refresh()
        self.destroy()
        notify_success(self.parent_screen.app, "Key Generated", f"'{name}' was generated successfully.")


class KeysScreen(ctk.CTkFrame):
    COLUMNS = ("name", "type", "public_key_path")

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(header, text="SSH Keys", font=ctk.CTkFont(size=22, weight="bold"), text_color=("#111827", "#F9FAFB")).pack(
            side="left"
        )
        ctk.CTkButton(header, text="+ Generate New Key", command=self._open_generate_dialog).pack(
            side="right"
        )

        ctk.CTkLabel(
            self, text="Private key contents are never displayed here.", text_color=("gray20", "gray75")
        ).pack(anchor="w", pady=(0, 10))

        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table_frame, columns=self.COLUMNS, show="headings", selectmode="browse"
        )
        headings = {"name": "Name", "type": "Type", "public_key_path": "Public Key Path"}
        for col in self.COLUMNS:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=180)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.refresh()

    def on_show(self):
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for key in self.app.store.list_keys():
            self.tree.insert(
                "", "end", iid=key.name, values=(key.name, key.key_type, key.public_key_path)
            )

    def _open_generate_dialog(self):
        GenerateKeyDialog(self)
