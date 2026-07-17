"""Shared UI helpers: toast notifications, standardized modal dialogs, and
a progress/log dialog for long-running background operations (key deploy,
Git push/pull).

Success/warning notices are non-blocking toasts (auto-dismiss, stacked
bottom-right of the window that triggered them); errors and confirmations
stay modal since they carry text the user must actually read/decide on.
Both are CTk-styled instead of native tk messageboxes so they look
consistent across light/dark mode.
"""
import customtkinter as ctk

LEVEL_COLORS = {
    "info": "#3b82f6",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
}
LEVEL_ICONS = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✕"}

_active_toasts: dict = {}


class Toast(ctk.CTkToplevel):
    """A borderless, auto-dismissing notice stacked bottom-right of `parent`."""

    WIDTH = 320
    HEIGHT = 56
    GAP = 10

    def __init__(self, parent, message: str, level: str = "info", duration: int = 3500):
        super().__init__(parent)
        self._parent = parent
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        color = LEVEL_COLORS.get(level, LEVEL_COLORS["info"])
        icon = LEVEL_ICONS.get(level, "")
        frame = ctk.CTkFrame(self, fg_color=color, corner_radius=8)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(
            frame, text=f"{icon}  {message}", text_color="white",
            wraplength=self.WIDTH - 30, justify="left", font=ctk.CTkFont(size=12),
        ).pack(padx=14, pady=10, fill="both", expand=True)

        stack = _active_toasts.setdefault(id(parent), [])
        stack.append(self)
        self._reposition_stack(parent)
        self.after(duration, self._dismiss)

    def _reposition_stack(self, parent):
        parent.update_idletasks()
        stack = _active_toasts.get(id(parent), [])
        base_x = parent.winfo_rootx() + max(parent.winfo_width() - self.WIDTH - 20, 0)
        base_y = parent.winfo_rooty() + parent.winfo_height() - 20
        for index, toast in enumerate(reversed(stack)):
            y = base_y - (self.HEIGHT + self.GAP) * (index + 1)
            toast.geometry(f"{self.WIDTH}x{self.HEIGHT}+{base_x}+{y}")

    def _dismiss(self):
        stack = _active_toasts.get(id(self._parent), [])
        if self in stack:
            stack.remove(self)
        try:
            self.destroy()
        except Exception:
            pass
        if self._parent.winfo_exists():
            self._reposition_stack(self._parent)


class _ModalDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)

        ctk.CTkLabel(self, text=message, wraplength=340, justify="left").pack(
            padx=20, pady=(20, 10)
        )
        self.button_row = ctk.CTkFrame(self, fg_color="transparent")
        self.button_row.pack(pady=(0, 16))
        self.result = None

    def _finish(self, result):
        self.result = result
        self.destroy()

    def _show_modal(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        parent = self.master
        x = parent.winfo_rootx() + max((parent.winfo_width() - w) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - h) // 2, 0)
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        self.wait_window()
        return self.result


def confirm(parent, title: str, message: str) -> bool:
    dialog = _ModalDialog(parent, title, message)
    ctk.CTkButton(
        dialog.button_row, text="Cancel", fg_color="gray40", command=lambda: dialog._finish(False)
    ).pack(side="left", padx=(0, 8))
    ctk.CTkButton(
        dialog.button_row, text="Confirm", fg_color=LEVEL_COLORS["error"],
        hover_color="#b91c1c", command=lambda: dialog._finish(True),
    ).pack(side="left")
    return bool(dialog._show_modal())


def notify_error(parent, title: str, message: str) -> None:
    dialog = _ModalDialog(parent, title, message)
    ctk.CTkButton(dialog.button_row, text="OK", command=lambda: dialog._finish(True)).pack()
    dialog._show_modal()


def notify_success(parent, title: str, message: str) -> None:
    Toast(parent, message, level="success")


def notify_warning(parent, title: str, message: str) -> None:
    Toast(parent, message, level="warning", duration=4500)


class ProgressDialog(ctk.CTkToplevel):
    """A small modal window with a color-coded log, for operations like
    deploying a key or running Git sync where the user needs live feedback.
    """

    def __init__(self, parent, title: str = "Working..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("480x320")
        self.transient(parent)
        self.grab_set()

        self.log_box = ctk.CTkTextbox(self, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        self.log_box.configure(state="disabled")

        self.close_button = ctk.CTkButton(self, text="Close", command=self.destroy)
        self.close_button.pack(pady=(0, 12))
        self.close_button.configure(state="disabled")

    def log(self, message: str, level: str = "info") -> None:
        def _do():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", message + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

        self.after(0, _do)

    def finish(self) -> None:
        self.after(0, lambda: self.close_button.configure(state="normal"))
