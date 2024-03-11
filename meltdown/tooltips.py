# Modules
from .app import app

# Standard
import re
import tkinter as tk
from tkinter import ttk
from typing import Any, Optional, Tuple


def clean_string(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class ToolTip:
    current_tooltip: Optional["ToolTip"] = None

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = clean_string(text)
        self.tooltip: Optional[tk.Toplevel] = None
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.update_event)
        self.widget.bind("<Button-1>", self.hide_tooltip)
        self.id = ""

    def update_event(self, event: Any) -> None:
        self.current_event = event

    def schedule_tooltip(self, event: Any) -> None:
        if ToolTip.current_tooltip is not None:
            ToolTip.current_tooltip.hide_tooltip()

        self.id = self.widget.after(500, lambda: self.show_tooltip())
        ToolTip.current_tooltip = self

    def show_tooltip(self) -> None:
        from .widgets import widgets
        event = self.current_event

        if widgets.menu_open:
            return

        box: Optional[Tuple[int, int, int, int]] = None

        if isinstance(self.widget, ttk.Combobox):
            box = self.widget.bbox("insert")
        elif isinstance(self.widget, ttk.Entry):
            box = self.widget.bbox(0)
        else:
            box = self.widget.bbox()

        if not box:
            return

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        label = tk.Label(self.tooltip, text=self.text, background="white",
                         wraplength=250, justify=tk.LEFT)
        label.pack()

        self.tooltip.update_idletasks()
        x, y, _, _ = box
        y += event.y_root + 20
        width = self.tooltip.winfo_reqwidth()
        window_width = app.root.winfo_width()
        window_x = app.root.winfo_x()
        left_edge = window_x
        right_edge = window_x + window_width
        x = event.x_root - (width // 2)

        if x < left_edge:
            x = left_edge
        elif x + width > right_edge:
            x = right_edge - width

        self.tooltip.wm_geometry(f"+{x}+{y}")

    def hide_tooltip(self, event: Any = None) -> None:
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = ""

        ToolTip.current_tooltip = None
