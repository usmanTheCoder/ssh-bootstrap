from datetime import datetime, timezone
import os
import platform
import subprocess
from tkinter import filedialog

import customtkinter as ctk

from sshmgr import ssh_config
from sshmgr import git_sync
from sshmgr.ui.widgets import notify_error, notify_success, notify_warning


def _format_local_time(utc_str: str) -> str:
    if not utc_str or not utc_str.endswith(" UTC"):
        return utc_str
    try:
        dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S UTC")
        dt = dt.replace(tzinfo=timezone.utc)
        local_dt = dt.astimezone()
        # Use a newline to prevent horizontal overflow in the stat card
        return local_dt.strftime('%Y-%m-%d\n%I:%M %p')
    except Exception:
        return utc_str


class _StatCard(ctk.CTkFrame):
    def __init__(self, parent, title: str):
        super().__init__(parent, corner_radius=10, fg_color=("#FFFFFF", "#2B2B2B"))
        
        # Inner frame to keep items vertically centered
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(expand=True, fill="both", padx=10, pady=16)
        
        self.value_label = ctk.CTkLabel(
            self.inner, text="0", font=ctk.CTkFont(size=28, weight="bold"), text_color=("#111827", "#F9FAFB")
        )
        self.value_label.pack(expand=True)
        
        self.title_label = ctk.CTkLabel(
            self.inner, text=title, text_color=("#6B7280", "#9CA3AF"), font=ctk.CTkFont(size=12)
        )
        self.title_label.pack()

    def set_value(self, value: str, color: str = None):
        font_size = 18 if len(value) > 12 else 24 if len(value) > 8 else 28
        self.value_label.configure(
            text=value, 
            font=ctk.CTkFont(size=font_size, weight="bold"),
            text_color=color if color else ("#111827", "#F9FAFB")
        )


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        ctk.CTkLabel(self, text="Dashboard", font=ctk.CTkFont(size=22, weight="bold"), text_color=("#111827", "#F9FAFB")).pack(
            anchor="w", pady=(0, 16)
        )

        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 20))
        for i in range(4):
            cards_row.grid_columnconfigure(i, weight=1)

        self.servers_card = _StatCard(cards_row, "SSH Hosts")
        self.servers_card.grid(row=0, column=0, padx=6, sticky="nsew")

        self.jump_hosts_card = _StatCard(cards_row, "Jump Hosts")
        self.jump_hosts_card.grid(row=0, column=1, padx=6, sticky="nsew")

        self.sync_status_card = _StatCard(cards_row, "Sync Status")
        self.sync_status_card.grid(row=0, column=2, padx=6, sticky="nsew")

        self.last_sync_card = _StatCard(cards_row, "Last Synchronized")
        self.last_sync_card.grid(row=0, column=3, padx=6, sticky="nsew")

        ctk.CTkLabel(self, text="Quick Actions", font=ctk.CTkFont(size=16, weight="bold"), text_color=("#111827", "#F9FAFB")).pack(
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
        
        # --- Config Preview Section ---
        preview_header = ctk.CTkFrame(self, fg_color="transparent")
        preview_header.pack(fill="x", pady=(24, 8))
        
        ctk.CTkLabel(preview_header, text="Configuration Preview", font=ctk.CTkFont(size=16, weight="bold"), text_color=("#111827", "#F9FAFB")).pack(side="left")
        ctk.CTkLabel(preview_header, text="(~/.ssh/config)", font=ctk.CTkFont(size=12), text_color=("#6B7280", "#9CA3AF")).pack(side="left", padx=8)

        self.preview_box = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=("#F9FAFB", "#1F1F1F"), border_width=1, border_color=("#E5E7EB", "#333333"),
            corner_radius=8, wrap="none"
        )
        self.preview_box.pack(fill="both", expand=True, pady=(0, 10))
        self.preview_box.configure(state="disabled")

    def on_show(self):
        self.refresh()

    def refresh(self):
        store = self.app.store
        self.servers_card.set_value(str(len(store.list_servers())))
        self.jump_hosts_card.set_value(str(len(store.list_jump_hosts())))
        
        connected = git_sync.is_connected(store)
        if connected:
            self.sync_status_card.set_value("Connected", color=("#10b981", "#34d399"))  # Green
        else:
            self.sync_status_card.set_value("Not Configured", color=("#ef4444", "#f87171"))  # Red
            
        self.sync_button.configure(state="normal" if connected else "disabled")
        
        last_sync = store.settings.last_sync_timestamp
        self.last_sync_card.set_value(_format_local_time(last_sync) if last_sync else "Never")

        # Refresh preview
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        config_path = ssh_config.default_config_path()
        if config_path.exists():
            try:
                content = config_path.read_text(encoding="utf-8")
                self.preview_box.insert("end", content)
            except Exception as e:
                self.preview_box.insert("end", f"Error reading config: {e}")
        else:
            self.preview_box.insert("end", "No SSH config file found yet. Add some servers to generate one!")
        self.preview_box.configure(state="disabled")

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
