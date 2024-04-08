# Standard
import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Any, Optional, Dict

# Modules
from .app import app
from .separatorbox import SeparatorBox
from .args import args
from .tooltips import ToolTip
from . import utils


class MenuItem:
    def __init__(self, text: str,
                 command: Optional[Callable[..., Any]] = None,
                 separator: bool = False, disabled: bool = False,
                 tooltip: str = ""):

        self.text = text
        self.command = command
        self.separator = separator
        self.disabled = disabled
        self.tooltip = tooltip
        self.coords = {"x": 0, "y": 0}
        self.filter_text = text.lower().replace(" ", "")


class Menu:
    current_menu: Optional["Menu"] = None

    @staticmethod
    def hide_all() -> None:
        if Menu.current_menu:
            Menu.current_menu.hide()

    @staticmethod
    def focus() -> None:
        if Menu.current_menu:
            Menu.current_menu.canvas.focus_set()

    def __init__(self) -> None:
        self.container: Optional[tk.Frame] = None
        self.items: List[MenuItem] = []

    def add(self, text: str,
            command: Optional[Callable[..., Any]] = None,
            disabled: bool = False, tooltip: str = "") -> None:

        self.items.append(MenuItem(text, command,
                                   disabled=disabled, tooltip=tooltip))

    def separator(self) -> None:
        self.items.append(MenuItem("", lambda: None, separator=True))

    def clear(self) -> None:
        self.items = []

    def on_mousewheel(self, direction: str) -> None:
        if not self.container:
            return

        y_top = self.container.winfo_y()
        y_bottom = y_top + self.container.winfo_height()
        height = self.canvas.winfo_height()
        distance = height - y_bottom

        if direction == "up":
            if y_top >= 0:
                return

            self.canvas.yview_scroll(-1, "units")
        elif direction == "down":
            if distance >= 0:
                return

            self.canvas.yview_scroll(1, "units")

    def make(self) -> None:
        self.root = tk.Frame(app.main_frame, background=app.theme.menu_border)
        self.canvas = tk.Canvas(self.root, borderwidth=0, highlightthickness=0, background=app.theme.menu_canvas_background)
        self.container = tk.Frame(self.canvas, background=app.theme.menu_background, borderwidth=0, highlightthickness=0)
        self.canvas.create_window((0, 0), window=self.container, anchor="nw")
        self.canvas.bind("<FocusOut>", lambda e: self.hide())
        self.canvas.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.current_widget = None
        self.selected_index = -1
        self.make_items()
        self.select_first_item()
        self.configure_geometry()
        self.setup_keyboard()
        self.canvas.grid(padx=app.theme.menu_border_width, pady=app.theme.menu_border_width)
        self.filter = ""

    def make_items(self) -> None:
        if not self.container:
            return

        def exec() -> None:
            if self.selected_index not in self.elements:
                return

            item = self.items[self.selected_index]

            if item.command:
                item.command()

        def cmd() -> None:
            self.hide()
            app.main_frame.after(10, lambda: exec())

        def on_motion(event: Any) -> None:
            widget = event.widget.winfo_containing(event.x_root, event.y_root)

            if not widget:
                return

            if isinstance(widget, SeparatorBox):
                return

            if isinstance(widget, tk.Frame):
                return

            if self.current_widget != widget:
                if self.current_widget:
                    self.current_widget.event_generate("<<Custom-Leave>>")

                self.current_widget = widget

                if self.current_widget:
                    self.current_widget.event_generate("<<Custom-Enter>>")

        self.container.bind("<Button-4>", lambda e: self.on_mousewheel("up"))
        self.container.bind("<Button-5>", lambda e: self.on_mousewheel("down"))
        self.canvas.bind("<Escape>", lambda e: self.hide())
        self.canvas.bind("<Return>", lambda e: cmd())
        self.canvas.bind("<Up>", lambda e: self.arrow_up())
        self.canvas.bind("<Down>", lambda e: self.arrow_down())
        self.elements: Dict[int, Dict[str, Any]] = {}
        self.separators: List[SeparatorBox] = []

        def bind_mouse(parent: tk.Widget) -> None:
            for child in parent.winfo_children():
                child.bind("<Motion>", lambda e: on_motion(e))
                child.bind("<B1-Motion>", lambda e: on_motion(e))
                child.bind("<Button-4>", lambda e: self.on_mousewheel("up"))
                child.bind("<Button-5>", lambda e: self.on_mousewheel("down"))
                child.bind("<ButtonRelease-1>", lambda e: cmd())
                child.bind("<ButtonRelease-1>", lambda e: cmd())
                bind_mouse(child)

        def make_item(item: MenuItem, i: int) -> None:
            if not self.container:
                return

            colors = self.get_colors(item)

            if item.separator:
                separator = SeparatorBox(self.container, app.theme.menu_background, padx=6, pady=2)
                separator.grid(row=i, column=0, sticky="ew")
                self.separators.append(separator)
            else:
                label = ttk.Label(self.container, text=item.text, background=colors["background"], foreground=colors["foreground"],
                                  wraplength=600, justify=tk.LEFT, anchor="w", font=app.theme.font_menu, borderwidth=0, padding=(4, 2, 4, 2))

                label.configure(cursor="hand2" if not item.disabled else "arrow")
                self.elements[i] = {"item": item, "index": i, "label": label, "visible": True}
                label.bind("<Button-3>", lambda e: self.show_tooltip(e, label, item.tooltip))
                label.bind("<<Custom-Enter>>", lambda e: self.on_enter(i))
                label.bind("<<Custom-Leave>>", lambda e: self.on_leave(i))
                label.grid(row=i, column=0, sticky="ew", pady=0)

        for i, item in enumerate(self.items):
            make_item(item, i)

        self.no_items = ttk.Label(self.container, text="No Items", background=app.theme.menu_background, foreground=app.theme.menu_foreground,
                                  wraplength=600, justify=tk.LEFT, anchor="w", font=app.theme.font, borderwidth=0, padding=(4, 2, 4, 2))

        self.no_items.grid(row=len(self.items), column=0, sticky="ew", pady=0)
        self.no_items.grid_remove()
        bind_mouse(self.canvas)

    def all_hidden(self) -> bool:
        return self.num_visible() == 0

    def configure_geometry(self) -> None:
        if not self.canvas or not self.container:
            return

        self.canvas.update_idletasks()
        self.container.update_idletasks()

        window_width = app.main_frame.winfo_width()
        window_height = app.main_frame.winfo_height()

        cwidth = self.container.winfo_reqwidth()

        # Limit height to 500 or window height if smaller
        cheight = min(500, self.container.winfo_reqheight())

        # Limit width to fit the container
        self.canvas.configure(width=cwidth)

        h = min(window_height, cheight)
        self.canvas.configure(height=h)

        menu_width = self.canvas.winfo_reqwidth()
        menu_height = self.canvas.winfo_reqheight()
        x = self.coords["x"] - app.main_frame.winfo_rootx()
        y = self.coords["y"] - app.main_frame.winfo_rooty()

        if x < 0:
            x = 0
        elif x + menu_width > window_width:
            x = window_width - menu_width

        if y < 0:
            y = 0
        elif y + menu_height > window_height:
            y = window_height - menu_height

        x -= app.theme.menu_border_width * 2
        self.root.place(x=x, y=y)

    def setup_keyboard(self) -> None:
        def on_key(event: Any) -> None:
            if event.keysym == "BackSpace":
                self.filter = ""
            elif event.char:
                if not self.all_hidden():
                    self.filter += event.char

            self.do_filter()

        self.canvas.bind("<KeyPress>", lambda e: on_key(e))

    def check_filter(self, filtr: str, item: MenuItem) -> bool:
        text = item.filter_text

        if not filtr:
            return True

        if not text:
            return False

        # Check normal
        if filtr in text:
            return True

        # Similarity on keys
        if utils.check_match(text, filtr):
            return True

        return False

    def do_filter(self) -> None:
        if not self.filter:
            for els in self.elements.values():
                self.show_item(els["index"])

            for sep in self.separators:
                sep.grid()
        else:
            filtr = self.filter.lower().replace(" ", "")

            for els in self.elements.values():
                if els["item"].disabled:
                    self.hide_item(els["index"])
                elif self.check_filter(filtr, els["item"]):
                    self.show_item(els["index"])
                else:
                    self.hide_item(els["index"])

            for sep in self.separators:
                sep.grid_remove()

        if self.all_hidden():
            self.no_items.grid()
            self.selected_index = -1
        else:
            self.no_items.grid_remove()
            self.select_first_item()

        self.configure_geometry()
        self.canvas.yview_moveto(0.0)

    def show_item(self, index: int) -> None:
        els = self.elements[index]
        els["visible"] = True
        els["label"].grid()

    def hide_item(self, index: int) -> None:
        els = self.elements[index]
        els["visible"] = False
        els["label"].grid_remove()

    def select_first_item(self) -> None:
        for i in range(len(self.items)):
            if i not in self.elements:
                continue

            if self.elements[i]["visible"]:
                self.select_item(i)
                break

    def show(self, event: Optional[Any] = None, widget: Optional[tk.Widget] = None) -> None:
        Menu.hide_all()

        if not self.items:
            return

        if event:
            self.coords = {"x": event.x_root, "y": event.y_root}
        elif widget:
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() + widget.winfo_height() // 2
            self.coords = {"x": x, "y": y}
        else:
            return

        self.make()

        if self.root:
            self.canvas.update_idletasks()
            self.canvas.focus_set()
            Menu.current_menu = self

    def hide(self) -> None:
        from .keyboard import keyboard
        ToolTip.hide_all()

        if self.root:
            self.root.place_forget()
            self.root.destroy()
            ToolTip.block()
            keyboard.block()

        Menu.current_menu = None

    def no_item(self) -> bool:
        return self.selected_index not in self.elements

    def num_visible(self) -> int:
        return len([els for els in self.elements.values() if els["visible"]])

    def arrow_up(self, n: int = -1) -> None:
        if self.no_item():
            return

        if self.num_visible() < 2:
            return

        if n == -1:
            n = self.selected_index

        n -= 1

        if n < 0:
            if args.wrap:
                n = len(self.items) - 1
            else:
                return

        if not self.select_item(n):
            self.arrow_up(n)

    def arrow_down(self, n: int = -1) -> None:
        if self.no_item():
            return

        if self.num_visible() < 2:
            return

        if n == -1:
            n = self.selected_index

        n += 1

        if n >= len(self.items):
            if args.wrap:
                n = 0
            else:
                return

        if not self.select_item(n):
            self.arrow_down(n)

    def select_item(self, index: int) -> bool:
        if index not in self.elements:
            return False

        if self.elements[index]["item"].disabled:
            return False

        if not self.elements[index]["visible"]:
            return False

        self.on_enter(index)
        return True

    def on_enter(self, index: int) -> None:
        if index not in self.elements:
            return

        self.on_leave(self.selected_index)
        els = self.elements[index]
        colors = self.get_colors(els["item"])
        els["label"]["background"] = colors["hover_background"]
        els["label"]["foreground"] = colors["hover_foreground"]
        self.selected_index = index

        if index <= 1:
            self.canvas.yview_moveto(0.0)
        else:
            self.scroll_to_item()

    def on_leave(self, index: int) -> None:
        ToolTip.hide_all()

        if index not in self.elements:
            return

        els = self.elements[index]
        colors = self.get_colors(els["item"])
        els["label"]["background"] = colors["background"]
        els["label"]["foreground"] = colors["foreground"]

    def get_colors(self, item: MenuItem) -> Any:
        background = app.theme.menu_background

        if item.disabled:
            foreground = app.theme.menu_disabled_foreground
            hover_foreground = app.theme.menu_disabled_foreground
            hover_background = app.theme.menu_background
        else:
            foreground = app.theme.menu_foreground
            hover_foreground = app.theme.menu_hover_foreground
            hover_background = app.theme.menu_hover_background

        return {"background": background, "foreground": foreground,
                "hover_background": hover_background, "hover_foreground": hover_foreground}

    def scroll_to_item(self) -> None:
        if self.no_item():
            return

        els = self.elements[self.selected_index]
        tries = 0

        widget_height = els["label"].winfo_height()
        container_height = self.canvas.winfo_height()

        def widget_y() -> int:
            return int(els["label"].winfo_rooty() - self.canvas.winfo_rooty())

        def not_visible() -> bool:
            wy = widget_y()
            return (wy + widget_height) > container_height or (wy < 0)

        while tries < 16:
            if not_visible():
                wy = widget_y()
                outside_top = abs(min(0, wy))
                outside_bottom = max(0, (wy + widget_height) - container_height)
                units = 3

                if outside_top > 0:
                    self.canvas.yview_scroll(-units, "units")
                elif outside_bottom > 0:
                    self.canvas.yview_scroll(units, "units")
                else:
                    break

                app.update()
            else:
                break

            tries += 1

    def show_tooltip(self, event: Any, widget: tk.Widget, text: str) -> None:
        if not text:
            return

        tooltip = ToolTip(widget, text, bind=False)
        tooltip.direct(event)
