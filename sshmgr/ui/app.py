"""Main application window: sidebar navigation + a swappable content area.

Every screen is a CTkFrame subclass that takes (parent, app) and can call
back into `app.store` (the AppStore) and `app.sync_ssh_config()` (the one
place that regenerates/validates/writes ~/.ssh/config - see the module
docstring in sshmgr/ssh_config.py for why that split exists).
"""
import threading
from tkinter import messagebox

import customtkinter as ctk

from sshmgr.store import AppStore
from sshmgr import ssh_config
from sshmgr import git_sync
from sshmgr.ui.widgets import notify_error, notify_success, notify_warning, ProgressDialog
from sshmgr.ui.dashboard import DashboardScreen
from sshmgr.ui.servers import ServersScreen
from sshmgr.ui.jump_hosts import JumpHostsScreen
from sshmgr.ui.keys_view import KeysScreen
from sshmgr.ui.settings import SettingsScreen
from sshmgr.ui.ssh_config_view import SSHConfigScreen
from sshmgr.ui.git_view import GitSyncScreen

ctk.set_default_color_theme("blue")


class MainApp(ctk.CTk):
    NAV_ITEMS = [
        ("dashboard", "Dashboard"),
        ("servers", "Servers"),
        ("jump_hosts", "Jump Hosts"),
        ("keys", "SSH Keys"),
        ("ssh_config", "SSH Configuration"),
        ("git_sync", "Git Synchronization"),
        ("settings", "Settings"),
    ]

    def __init__(self):
        super().__init__()
        self.store = AppStore()
        
        # Apply the user's saved theme preference
        ctk.set_appearance_mode(self.store.settings.theme)
        
        # Style treeviews based on theme
        from sshmgr.ui.widgets import style_treeview
        style_treeview()

        # Handle UI scaling based on OS

        self.title("SSH Configuration Manager")
        self.geometry("1050x650")
        self.minsize(950, 600)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.screens = {}
        self._register_screens()
        self.show_screen("dashboard")
        
        self.after(500, self._check_first_run_import)

    # ------------------------------------------------------------- sidebar
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=("#F3F4F6", "#212121"))
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_rowconfigure(len(self.NAV_ITEMS) + 1, weight=1)

        ctk.CTkLabel(
            sidebar, text="SSH Manager", font=ctk.CTkFont(size=18, weight="bold"), text_color=("#111827", "#F9FAFB")
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.nav_buttons = {}
        for i, (key, label) in enumerate(self.NAV_ITEMS, start=1):
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                fg_color="transparent",
                text_color=("#4B5563", "#D1D5DB"),
                hover_color=("#E5E7EB", "#2B2B2B"),
                command=lambda k=key: self.show_screen(k),
            )
            btn.grid(row=i, column=0, padx=10, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        theme_switch = ctk.CTkSwitch(
            sidebar,
            text="Dark mode",
            command=self._toggle_theme,
        )
        if self.store.settings.theme == "dark":
            theme_switch.select()
        theme_switch.grid(row=len(self.NAV_ITEMS) + 2, column=0, padx=20, pady=20, sticky="sw")

    def _toggle_theme(self):
        new_theme = "dark" if ctk.get_appearance_mode() == "Light" else "light"
        ctk.set_appearance_mode(new_theme)
        self.store.update_settings(theme=new_theme)
        from sshmgr.ui.widgets import style_treeview
        style_treeview()

    # ------------------------------------------------------------- screens
    def _register_screens(self):
        self.screens["dashboard"] = DashboardScreen(self.content, self)
        self.screens["servers"] = ServersScreen(self.content, self)
        self.screens["jump_hosts"] = JumpHostsScreen(self.content, self)
        self.screens["keys"] = KeysScreen(self.content, self)
        self.screens["ssh_config"] = SSHConfigScreen(self.content, self)
        self.screens["git_sync"] = GitSyncScreen(self.content, self)
        self.screens["settings"] = SettingsScreen(self.content, self)

        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

    def show_screen(self, key: str):
        screen = self.screens[key]
        screen.tkraise()
        if hasattr(screen, "on_show"):
            screen.on_show()
        for nav_key, btn in self.nav_buttons.items():
            if nav_key == key:
                btn.configure(fg_color=("#E5E7EB", "#374151"), text_color=("#111827", "#F9FAFB"))
            else:
                btn.configure(fg_color="transparent", text_color=("#4B5563", "#D1D5DB"))

    # ------------------------------------------------------ config syncing
    def import_config_file(self, path) -> tuple[int, int]:
        """Parse an SSH config file and merge its hosts/jump-hosts/keys into
        the store, skipping aliases that already exist. Returns
        (imported_count, skipped_count). Raises on unparseable input.
        """
        servers, jump_hosts, keys = ssh_config.import_existing(path)

        imported, skipped = 0, 0
        for key in keys:
            if key.name not in self.store.keys:
                self.store.keys[key.name] = key
                imported += 1
        for jh in jump_hosts:
            if jh.name not in self.store.jump_hosts:
                self.store.jump_hosts[jh.name] = jh
                imported += 1
            else:
                skipped += 1
        for server in servers:
            if server.alias not in self.store.servers:
                self.store.servers[server.alias] = server
                imported += 1
            else:
                skipped += 1
        self.store.save()
        return imported, skipped

    def sync_ssh_config(self) -> bool:
        """Regenerate/validate/write ~/.ssh/config from the current store.
        This is the single choke point every mutating screen must call
        after touching the store, so the GUI and the config file never
        drift apart. Returns True on success; shows an error and returns
        False if validation fails (the store mutation itself already
        happened - see the per-screen callers for how they surface this).
        """
        try:
            ssh_config.write(self.store)
            return True
        except ssh_config.SSHConfigError as e:
            notify_error(self, "SSH Config Validation Failed", str(e))
            return False

    def refresh_all_screens(self):
        for screen in self.screens.values():
            if hasattr(screen, "refresh"):
                screen.refresh()

    # ------------------------------------------------------------ git sync
    def prompt_git_sync(self, commit_message: str):
        """Called after a config-changing action's ssh_config.write() has
        already succeeded. Per the user's chosen 'prompt every time'
        default, ask before pushing - does nothing if no repo is connected.
        """
        if not git_sync.is_connected(self.store):
            return
        if not messagebox.askyesno(
            "Sync to Git",
            f"Commit and push this change to your Git repository now?\n\n{commit_message}",
            parent=self,
        ):
            return
        self.push_to_git(commit_message)

    def push_to_git(self, commit_message: str, on_complete=None):
        progress = ProgressDialog(self, title="Pushing to Git")

        def worker():
            try:
                git_sync.push_changes(self.store, commit_message, on_progress=progress.log)
            except git_sync.GitSyncError as e:
                self.after(0, lambda: notify_error(self, "Push Failed", str(e)))
            else:
                if on_complete:
                    self.after(0, on_complete)
            finally:
                progress.finish()

        threading.Thread(target=worker, daemon=True).start()

    def pull_from_git(self, on_complete=None):
        if not git_sync.is_connected(self.store):
            notify_warning(
                self, "Not Connected",
                "Connect a Git repository first, in the Git Synchronization tab.",
            )
            return
        progress = ProgressDialog(self, title="Pulling from Git")

        def worker():
            try:
                added, updated, removed = git_sync.pull_changes(self.store, on_progress=progress.log)
            except git_sync.ConflictError as e:
                self.after(0, lambda: self._handle_conflict(e))
            except git_sync.GitSyncError as e:
                self.after(0, lambda: notify_error(self, "Pull Failed", str(e)))
            else:
                self.after(0, lambda: self._after_pull(added, updated, removed, on_complete))
            finally:
                progress.finish()

        threading.Thread(target=worker, daemon=True).start()

    def _after_pull(self, added, updated, removed, on_complete=None):
        self.sync_ssh_config()
        self.refresh_all_screens()
        if on_complete:
            on_complete()
        notify_success(
            self, "Pull Complete",
            f"Added {added}, updated {updated}, removed {removed} entr"
            f"{'y' if (added + updated + removed) == 1 else 'ies'}.",
        )

    def _handle_conflict(self, error: git_sync.ConflictError):
        files = ", ".join(error.conflicted_files)
        choice = messagebox.askyesnocancel(
            "Sync Conflict",
            f"Conflicting file(s) while pulling: {files}\n\n"
            "Yes = keep your LOCAL version (and push it)\n"
            "No = keep the REMOTE version\n"
            "Cancel = resolve later",
            parent=self,
        )
        if choice is None:
            return
        strategy = "local" if choice else "remote"
        try:
            git_sync.resolve_conflict(strategy)
        except git_sync.GitSyncError as e:
            notify_error(self, "Conflict Resolution Failed", str(e))
            return
        self.sync_ssh_config()
        self.refresh_all_screens()
        notify_success(self, "Conflict Resolved", f"Kept the {strategy} version.")

    def synchronize_now(self):
        """The Dashboard's 'Synchronize Configuration' quick action: push
        whatever local changes exist. Pulling is a separate, explicit
        action on the Git Synchronization screen."""
        if not git_sync.is_connected(self.store):
            notify_warning(
                self, "Not Connected",
                "Connect a Git repository first, in the Git Synchronization tab.",
            )
            return
        self.push_to_git("Manual synchronization", on_complete=self.refresh_all_screens)

    def _check_first_run_import(self):
        """Prompt to import ~/.ssh/config if the app database is completely empty."""
        if len(self.store.list_servers()) > 0 or len(self.store.list_jump_hosts()) > 0:
            return
            
        default_path = ssh_config.default_config_path()
        if not default_path.exists() or default_path.stat().st_size == 0:
            return
            
        if messagebox.askyesno(
            "Import Existing Configuration",
            f"We noticed you have an existing SSH configuration at:\n{default_path}\n\n"
            "Would you like to import it into the manager now?"
        ):
            try:
                imported, skipped = self.import_config_file(str(default_path))
                self.sync_ssh_config()
                if imported > 0:
                    notify_success(
                        self, 
                        "Import Complete", 
                        f"Successfully imported {imported} entries."
                    )
                    if "dashboard" in self.screens:
                        self.screens["dashboard"].refresh()
            except Exception as e:
                notify_error(self, "Import Failed", f"Could not parse configuration:\n{e}")

def run():
    app = MainApp()
    app.mainloop()
