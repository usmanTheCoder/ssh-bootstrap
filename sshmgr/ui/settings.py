import customtkinter as ctk

from sshmgr.ui.widgets import notify_success


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(header, text="Settings", font=ctk.CTkFont(size=22, weight="bold"), text_color=("#111827", "#F9FAFB")).pack(
            side="left"
        )

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, pady=(20, 0))

        # Theme Section
        ctk.CTkLabel(form, text="Appearance", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(0, 10)
        )
        
        self.theme_var = ctk.StringVar(value=self.app.store.settings.theme.capitalize())
        theme_row = ctk.CTkFrame(form, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(theme_row, text="Theme Mode:").pack(side="left", padx=(0, 10))
        self.theme_menu = ctk.CTkOptionMenu(
            theme_row, 
            values=["Dark", "Light", "System"], 
            variable=self.theme_var
        )
        self.theme_menu.pack(side="left")

        # GitOps / Auto-Sync Section
        ctk.CTkLabel(form, text="GitOps & Synchronization", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(20, 10)
        )
        
        self.auto_sync_var = ctk.BooleanVar(value=self.app.store.settings.auto_sync)
        self.auto_sync_check = ctk.CTkCheckBox(
            form,
            text="Automatically commit and push changes to Git (Requires linked repo)",
            variable=self.auto_sync_var
        )
        self.auto_sync_check.pack(anchor="w", pady=(0, 30))

        # Save Button
        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(fill="x", pady=(20, 0))
        self._save_btn = ctk.CTkButton(action_row, text="Save Settings", command=self._save)
        self._save_btn.pack(pady=20)
        
        # Add a flexible spacer to push the credits to the bottom
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)
        
        # Credits at the bottom
        credits_label = ctk.CTkLabel(
            self, 
            text="Developed by M. Usman Sharif & M Umair Khan", 
            text_color=("#9CA3AF", "#4B5563"),
            font=ctk.CTkFont(size=12, slant="italic")
        )
        credits_label.pack(side="bottom", pady=15)

    def _save(self):
        theme_choice = self.theme_var.get().lower()
        self.app.store.settings.theme = theme_choice
        self.app.store.settings.auto_sync = self.auto_sync_var.get()
        self.app.store.save()
        
        # Apply theme globally immediately
        ctk.set_appearance_mode(theme_choice)
        from sshmgr.ui.widgets import style_treeview
        style_treeview()
        
        notify_success(self.app, "Settings Saved", "Your preferences have been updated.")

    def on_show(self):
        # Refresh state when screen is shown in case it was changed elsewhere (e.g. sidebar toggle)
        self.theme_var.set(self.app.store.settings.theme.capitalize())
        self.auto_sync_var.set(self.app.store.settings.auto_sync)
