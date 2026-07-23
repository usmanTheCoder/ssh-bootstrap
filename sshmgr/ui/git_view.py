import threading

import customtkinter as ctk

from sshmgr import git_sync
from sshmgr.ui.widgets import confirm, notify_error, notify_success, ProgressDialog


class TokenDialog(ctk.CTkToplevel):
    def __init__(self, parent_screen):
        super().__init__(parent_screen)
        self.parent_screen = parent_screen
        self.title("GitHub Personal Access Token")
        self.geometry("420x260")
        self.transient(parent_screen)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="Paste a GitHub PAT with 'repo' scope.\nIt is stored in your OS credential store, never in plain text.",
            justify="left",
        ).pack(anchor="w", padx=16, pady=(16, 8))

        self.token_entry = ctk.CTkEntry(self, show="*")
        self.token_entry.pack(fill="x", padx=16)

        self.status_label = ctk.CTkLabel(self, text="", text_color=("gray20", "gray75"))
        self.status_label.pack(anchor="w", padx=16, pady=(8, 0))

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x", padx=16, pady=20)
        ctk.CTkButton(button_row, text="Cancel", fg_color="gray40", command=self.destroy).pack(
            side="right", padx=(8, 0)
        )
        ctk.CTkButton(button_row, text="Save & Verify", command=self._save).pack(side="right")

    def _save(self):
        token = self.token_entry.get().strip()
        if not token:
            notify_error(self, "Token Required", "Paste a Personal Access Token first.")
            return
        self.status_label.configure(text="Verifying with GitHub...")
        self.update_idletasks()
        try:
            username = git_sync.validate_token(token)
        except git_sync.GitSyncError as e:
            notify_error(self, "Verification Failed", str(e))
            return
        git_sync.save_token(token)
        self.parent_screen.refresh()
        self.destroy()
        notify_success(self.parent_screen.app, "Token Saved", f"Authenticated as GitHub user '{username}'.")


class GitSyncScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(header, text="Git Synchronization", font=ctk.CTkFont(size=22, weight="bold"), text_color=("#111827", "#F9FAFB")).pack(
            side="left"
        )

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.refresh()

    def on_show(self):
        self.refresh()

    def refresh(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        if git_sync.is_connected(self.app.store):
            self._build_connected_view()
        else:
            self._build_connect_view()

    # ------------------------------------------------------- not connected
    def _build_connect_view(self):
        token_row = ctk.CTkFrame(self.container, fg_color="transparent")
        token_row.pack(fill="x", pady=(0, 16))
        token_status = "Saved" if git_sync.get_token() else "Not set"
        ctk.CTkLabel(token_row, text=f"GitHub Token: {token_status}").pack(side="left")
        ctk.CTkButton(
            token_row, text="Set / Update Token", command=lambda: TokenDialog(self)
        ).pack(side="left", padx=(12, 0))

        ctk.CTkLabel(self.container, text="Repository URL").pack(anchor="w", pady=(8, 4))
        self.url_entry = ctk.CTkEntry(
            self.container, placeholder_text="https://github.com/username/ssh-config-backup.git"
        )
        self.url_entry.pack(fill="x")

        button_row = ctk.CTkFrame(self.container, fg_color="transparent")
        button_row.pack(fill="x", pady=(12, 0))
        ctk.CTkButton(
            button_row, text="Clone Existing Repository", command=self._clone_existing
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            button_row, text="Initialize New Repository", command=self._init_new
        ).pack(side="left")

    def _require_token(self) -> bool:
        if not git_sync.get_token():
            notify_error(self, "No Token", "Set a GitHub Personal Access Token first.")
            return False
        return True

    def _clone_existing(self):
        if not self._require_token():
            return
        url = self.url_entry.get().strip()
        if not url:
            notify_error(self, "Repository URL Required", "Enter a repository URL first.")
            return
        self._run_git_op(
            "Connecting Repository",
            lambda progress: self._connect_and_pull(url, progress),
        )

    def _connect_and_pull(self, url, progress):
        git_sync.connect_existing(self.app.store, url, on_progress=progress.log)
        added, updated, removed = git_sync.pull_changes(self.app.store, on_progress=progress.log)
        self.app.after(0, lambda: self._after_connect(added, updated, removed))

    def _after_connect(self, added, updated, removed):
        self.app.sync_ssh_config()
        self.refresh()
        self.app.refresh_all_screens()
        notify_success(
            self, "Repository Connected",
            f"Added {added}, updated {updated}, removed {removed} entr{'y' if added + updated + removed == 1 else 'ies'} from the repository.",
        )

    def _init_new(self):
        if not self._require_token():
            return
        url = self.url_entry.get().strip()
        if not url:
            notify_error(self, "Repository URL Required", "Enter a repository URL first.")
            return
        self._run_git_op(
            "Initializing Repository",
            lambda progress: self._init_and_push(url, progress),
        )

    def _init_and_push(self, url, progress):
        git_sync.init_new(self.app.store, url, on_progress=progress.log)
        git_sync.push_changes(self.app.store, "Initial SSH configuration sync", on_progress=progress.log)
        self.app.after(0, self._after_init)

    def _after_init(self):
        self.refresh()
        notify_success(self, "Repository Initialized", "Your SSH configuration has been pushed.")

    # ----------------------------------------------------------- connected
    def _build_connected_view(self):
        settings = self.app.store.settings
        ctk.CTkLabel(self.container, text=f"Repository: {settings.git_repo_url}").pack(
            anchor="w", pady=(0, 4)
        )
        last_sync = settings.last_sync_timestamp or "Never"
        ctk.CTkLabel(self.container, text=f"Last synchronized: {last_sync}").pack(
            anchor="w", pady=(0, 16)
        )

        auto_sync_var = ctk.BooleanVar(value=settings.auto_sync)
        ctk.CTkCheckBox(
            self.container,
            text="Push automatically after every change (skip the prompt)",
            variable=auto_sync_var,
            command=lambda: self.app.store.update_settings(auto_sync=auto_sync_var.get()),
        ).pack(anchor="w", pady=(0, 16))

        button_row = ctk.CTkFrame(self.container, fg_color="transparent")
        button_row.pack(fill="x")
        ctk.CTkButton(button_row, text="Push Now", command=self._push_now).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(button_row, text="Pull Now", command=self._pull_now).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            button_row, text="Disconnect", fg_color="#ef4444", hover_color="#b91c1c",
            command=self._disconnect,
        ).pack(side="left")

    def _push_now(self):
        self.app.push_to_git("Manual synchronization", on_complete=self.refresh)

    def _pull_now(self):
        self.app.pull_from_git(on_complete=self.refresh)

    def _disconnect(self):
        if not confirm(
            self, "Disconnect Repository",
            "Disconnect this Git repository? Your local SSH config and app data are unaffected.",
        ):
            return
        git_sync.disconnect(self.app.store)
        self.refresh()

    def _run_git_op(self, title, operation_fn, on_success=None):
        progress = ProgressDialog(self, title=title)

        def worker():
            try:
                operation_fn(progress)
            except git_sync.GitSyncError as e:
                self.after(0, lambda: notify_error(self, "Git Error", str(e)))
            else:
                if on_success:
                    self.after(0, on_success)
            finally:
                progress.finish()

        threading.Thread(target=worker, daemon=True).start()
