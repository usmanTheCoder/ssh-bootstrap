import os
import platform
import subprocess
from tkinter import filedialog

import customtkinter as ctk

from sshmgr import ssh_config
from sshmgr.ui.widgets import confirm, notify_error, notify_success, notify_warning

EDIT_WARNING = (
    "Manual edits are saved as-is, as an advanced escape hatch:\n\n"
    "- Edits inside the auto-generated managed block will be overwritten the "
    "next time you add, edit, or delete a server or jump host in the app.\n"
    "- Edits outside the managed block are preserved.\n"
    "- Manual edits won't appear in the Servers/Jump Hosts lists unless you "
    "use Import afterward.\n\n"
    "Continue?"
)


class SSHConfigScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.edit_mode = False

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            header, text="SSH Configuration", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(button_row, text="Refresh", command=self.refresh).pack(side="left", padx=(0, 8))
        ctk.CTkButton(button_row, text="Import...", command=self._import).pack(side="left", padx=(0, 8))
        ctk.CTkButton(button_row, text="Export...", command=self._export).pack(side="left", padx=(0, 8))
        ctk.CTkButton(button_row, text="Open in Default Editor", command=self._open).pack(
            side="left", padx=(0, 8)
        )
        self.edit_button = ctk.CTkButton(
            button_row, text="Enable Manual Editing", command=self._toggle_edit_mode
        )
        self.edit_button.pack(side="left", padx=(0, 8))
        self.save_button = ctk.CTkButton(button_row, text="Save Changes", command=self._save_raw)
        self.save_button.pack(side="left")
        self.save_button.configure(state="disabled")

        self.info_label = ctk.CTkLabel(self, text="", text_color="gray60")
        self.info_label.pack(anchor="w", pady=(0, 6))

        self.text_box = ctk.CTkTextbox(self, wrap="none", font=("Consolas", 12))
        self.text_box.pack(fill="both", expand=True)
        self.text_box.configure(state="disabled")

        self.refresh()

    def on_show(self):
        if not self.edit_mode:
            self.refresh()

    def refresh(self):
        path = ssh_config.default_config_path()
        mode_note = "  (advanced manual-edit mode - not yet saved)" if self.edit_mode else ""
        self.info_label.configure(text=f"Location: {path}{mode_note}")
        content = path.read_text(encoding="utf-8") if path.exists() else "(No SSH config file yet.)"
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", content)
        if not self.edit_mode:
            self.text_box.configure(state="disabled")

    def _toggle_edit_mode(self):
        if self.edit_mode:
            self.edit_mode = False
            self.refresh()
            self.edit_button.configure(text="Enable Manual Editing")
            self.save_button.configure(state="disabled")
            return

        if not confirm(self, "Enable Manual Editing", EDIT_WARNING):
            return
        self.edit_mode = True
        self.text_box.configure(state="normal")
        self.edit_button.configure(text="Cancel Editing")
        self.save_button.configure(state="normal")
        self.info_label.configure(
            text=f"Location: {ssh_config.default_config_path()}  (advanced manual-edit mode - not yet saved)"
        )

    def _save_raw(self):
        text = self.text_box.get("1.0", "end")
        problems = ssh_config.validate(text)
        if problems:
            notify_error(self, "Invalid SSH Configuration", "\n".join(problems))
            return
        ssh_config.write_raw(text)
        self.edit_mode = False
        self.refresh()
        self.edit_button.configure(text="Enable Manual Editing")
        self.save_button.configure(state="disabled")
        notify_success(self, "Saved", "Manual changes were validated and saved.")
        self.app.prompt_git_sync("Manually edited ~/.ssh/config")

    def _import(self):
        path = filedialog.askopenfilename(title="Select an SSH config file to import", parent=self)
        if not path:
            return
        try:
            imported, skipped = self.app.import_config_file(path)
        except Exception as e:
            notify_error(self, "Import Failed", f"Could not parse that file:\n{e}")
            return
        if not self.app.sync_ssh_config():
            return
        self.refresh()
        notify_success(
            self, "Import Complete",
            f"Imported {imported} entr{'y' if imported == 1 else 'ies'}."
            + (f" Skipped {skipped} duplicate alias(es)." if skipped else ""),
        )
        self.app.prompt_git_sync(f"Imported {imported} entr{'y' if imported == 1 else 'ies'} from {path}")

    def _export(self):
        dest = filedialog.asksaveasfilename(
            title="Export SSH config to...", defaultextension="", parent=self
        )
        if not dest:
            return
        ssh_config.export(self.app.store, dest)
        notify_success(self, "Exported", f"SSH configuration exported to:\n{dest}")

    def _open(self):
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
