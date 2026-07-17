import os
import platform
import subprocess
from tkinter import filedialog

import customtkinter as ctk

from sshmgr import ssh_config
from sshmgr import git_sync
from sshmgr.ui.widgets import notify_error, notify_success, notify_warning


class _StatCard(ctk.CTkFrame):
    def __init__(self, parent, title: str):
        super().__init__(parent, corner_radius=10)
        self.value_label = ctk.CTkLabel(self, text="0", font=ctk.CTkFont(size=28, weight="bold"))
        self.value_label.pack(pady=(16, 0))
        ctk.CTkLabel(self, text=title, text_color="gray60").pack(pady=(0, 16))

    def set_value(self, value: str):
        self.value_label.configure(text=value)


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        ctk.CTkLabel(self, text="Dashboard", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", pady=(0, 16)
        )

        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 20))
        for i in range(4):
            cards_row.grid_columnconfigure(i, weight=1)

        self.servers_card = _StatCard(cards_row, "Configured SSH Hosts")
        self.servers_card.grid(row=0, column=0, padx=6, sticky="ew")

        self.jump_hosts_card = _StatCard(cards_row, "Configured Jump Hosts")
        self.jump_hosts_card.grid(row=0, column=1, padx=6, sticky="ew")

        self.sync_status_card = _StatCard(cards_row, "Sync Status")
        self.sync_status_card.grid(row=0, column=2, padx=6, sticky="ew")

        self.last_sync_card = _StatCard(cards_row, "Last Synchronized")
        self.last_sync_card.grid(row=0, column=3, padx=6, sticky="ew")

        ctk.CTkLabel(self, text="Quick Actions", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(10, 10)
        )

        actions_row = ctk.CTkFrame(self, fg_color="transparent")
        actions_row.pack(fill="x")

        ctk.CTkButton(actions_row, text="Add Server/VM", command=self._add_server).pack(
            side="left", padx=(0, 10)
        )
        ctk.CTkButton(actions_row, text="Import Configuration", command=self._import_config).pack(
            side="left", padx=(0, 10)
        )
        self.sync_button = ctk.CTkButton(
            actions_row, text="Synchronize Configuration", command=self.app.synchronize_now
        )
        self.sync_button.pack(side="left", padx=(0, 10))
        ctk.CTkButton(actions_row, text="Open SSH Config", command=self._open_ssh_config).pack(
            side="left"
        )

    def on_show(self):
        self.refresh()

    def refresh(self):
        store = self.app.store
        self.servers_card.set_value(str(len(store.list_servers())))
        self.jump_hosts_card.set_value(str(len(store.list_jump_hosts())))
        connected = git_sync.is_connected(store)
        self.sync_status_card.set_value("Connected" if connected else "Not configured")
        self.sync_button.configure(state="normal" if connected else "disabled")
        last_sync = store.settings.last_sync_timestamp
        self.last_sync_card.set_value(last_sync if last_sync else "Never")

    def _add_server(self):
        self.app.show_screen("servers")
        self.app.screens["servers"].open_add_dialog()

    def _import_config(self):
        path = filedialog.askopenfilename(
            title="Select an SSH config file to import", parent=self
        )
        if not path:
            return
        try:
            imported, skipped = self.app.import_config_file(path)
        except Exception as e:
            notify_error(self, "Import Failed", f"Could not parse that file:\n{e}")
            return

        if not self.app.sync_ssh_config():
            return

        notify_success(
            self,
            "Import Complete",
            f"Imported {imported} entr{'y' if imported == 1 else 'ies'}."
            + (f" Skipped {skipped} duplicate alias(es)." if skipped else ""),
        )
        self.on_show()
        self.app.prompt_git_sync(f"Imported {imported} entr{'y' if imported == 1 else 'ies'} from {path}")

    def _open_ssh_config(self):
        path = ssh_config.default_config_path()
        if not path.exists():
            notify_warning(self, "No SSH Config", f"{path} does not exist yet.")
            return
        system = platform.system()
        if system == "Windows":
            os.startfile(str(path))
        elif system == "Darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])
