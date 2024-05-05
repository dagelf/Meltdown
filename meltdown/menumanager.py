# Standard
from typing import Any

# Modules
from .menus import Menu


class MainMenu:
    def __init__(self) -> None:
        from .app import app
        from .config import config
        from .session import session
        from .logs import logs
        from .commands import commands
        from .widgets import widgets

        self.menu = Menu()

        self.menu.add("System", lambda e: widgets.write_system_prompt())

        self.menu.separator()

        self.menu.add("Configs", lambda e: config.menu())
        self.menu.add("Sessions", lambda e: session.menu())
        self.menu.add("Logs", lambda e: logs.menu())

        self.menu.separator()

        self.menu.add("Commands", lambda e: commands.show_palette())

        self.menu.separator()

        self.menu.add("Compact", lambda e: app.toggle_compact())
        self.menu.add("Resize", lambda e: app.resize())

        self.menu.separator()

        self.menu.add("Theme", lambda e: app.pick_theme())
        self.menu.add("About", lambda e: app.show_about())

        self.menu.separator()

        self.menu.add("Exit", lambda e: app.exit())

    def show(self, event: Any = None) -> None:
        from .widgets import widgets

        if event:
            self.menu.show(event)
        else:
            widget = getattr(widgets, "main_menu_button")
            self.menu.show(widget=widget)


class ModelMenu:
    def __init__(self) -> None:
        from .model import model
        from .widgets import widgets

        self.menu = Menu()
        self.menu.add("Recent Models", lambda e: widgets.show_recent_models())
        self.menu.add("Browse Models", lambda e: widgets.browse_models())
        self.menu.add("Use GPT Model", lambda e: gpt_menu.show())
        self.menu.add("Set API Key", lambda e: model.set_api_key())

    def show(self, event: Any = None) -> None:
        from .widgets import widgets

        if event:
            self.menu.show(event)
        else:
            widget = getattr(widgets, "model_menu_button")
            self.menu.show(widget=widget)


class GPTMenu:
    def __init__(self) -> None:
        from .model import model
        from .widgets import widgets

        self.menu = Menu()

        for gpt in model.gpts:
            self.menu.add(gpt[1], lambda e, gpt=gpt: widgets.use_gpt(gpt[0]))

    def show(self, event: Any = None) -> None:
        from .widgets import widgets

        if event:
            self.menu.show(event)
        else:
            widget = getattr(widgets, "model_menu_button")
            self.menu.show(widget=widget)


class MoreMenu:
    def __init__(self) -> None:
        from .display import display

        self.menu = Menu()

        self.menu.add("Find", lambda e: display.find())
        self.menu.add("Find All", lambda e: display.find_all())

        self.menu.separator()

        self.menu.add("Copy All", lambda e: display.copy_output())
        self.menu.add("Select All", lambda e: display.select_output())

        self.menu.separator()

        self.menu.add("View Text", lambda e: display.view_text())
        self.menu.add("View JSON", lambda e: display.view_json())

        self.menu.separator()

        self.menu.add("Font", lambda e: font_menu.show())

    def show(self, event: Any = None) -> None:
        from .widgets import widgets

        if event:
            self.menu.show(event)
        else:
            widget = getattr(widgets, "more_menu_button")
            self.menu.show(widget=widget)


class TabMenu:
    def __init__(self) -> None:
        from .display import display

        self.menu_single = Menu()
        self.menu_single.add("Rename", lambda e: display.rename_tab())
        self.menu_single.add("Move", lambda e: display.move_tab())
        self.menu_single.add("Clear", lambda e: display.clear())

        self.menu_multi = Menu()
        self.menu_multi.add("Tab List", lambda e: display.show_tab_list(e))

        self.menu_multi.separator()

        self.menu_multi.add("Tab Left", lambda e: display.tab_left())
        self.menu_multi.add("Tab Right", lambda e: display.tab_right())

        self.menu_multi.separator()

        self.menu_multi.add("First Tab", lambda e: display.select_first_tab())
        self.menu_multi.add("Last Tab", lambda e: display.select_last_tab())

        self.menu_multi.separator()

        self.menu_multi.add("Active Tab", lambda e: display.select_active_tab())

        self.menu_multi.separator()

        self.menu_multi.add("Rename", lambda e: display.rename_tab())
        self.menu_multi.add("Move", lambda e: display.move_tab())
        self.menu_multi.add("Close", lambda e: display.tab_menu_close())

    def show(self, event: Any = None, mode: str = "normal") -> None:
        from .display import display

        if display.num_tabs() > 1:
            menu = self.menu_multi
        else:
            menu = self.menu_single

        if event:
            display.tab_menu_id = display.current_tab
            menu.show(event)
        else:
            page = display.book.current_page

            if not page:
                return

            widget = page.tab.frame

            if widget:
                display.tab_menu_id = page.id
                menu.show(widget=widget)


class FontMenu:
    def __init__(self) -> None:
        from .config import config
        from .display import display
        from .dialogs import Dialog

        def action(text: str) -> None:
            display.set_font_size(text)

        def set_font() -> None:
            Dialog.show_input(
                "Set Font Size", lambda a: action(a), value=str(config.font_size)
            )

        self.menu = Menu()
        self.menu.add("Set Font", lambda e: set_font())
        self.menu.add("Bigger Font", lambda e: display.increase_font())
        self.menu.add("Smaller Font", lambda e: display.decrease_font())
        self.menu.add("Font Family", lambda e: font_family_menu.show())
        self.menu.separator()
        self.menu.add("Reset Font", lambda e: display.reset_font())

    def show(self, event: Any = None) -> None:
        from .widgets import widgets

        if event:
            self.menu.show(event)
        else:
            widget = getattr(widgets, "more_menu_button")
            self.menu.show(widget=widget)


class FontFamilyMenu:
    def __init__(self) -> None:
        from .display import display

        self.menu = Menu()
        self.menu.add("Serif", lambda e: display.set_font_family("serif"))
        self.menu.add("Sans-Serif", lambda e: display.set_font_family("sans-serif"))
        self.menu.add("Monospace", lambda e: display.set_font_family("monospace"))

    def show(self, event: Any = None) -> None:
        from .widgets import widgets

        if event:
            self.menu.show(event)
        else:
            widget = getattr(widgets, "more_menu_button")
            self.menu.show(widget=widget)


class ThemeMenu:
    def __init__(self) -> None:
        from .config import config
        from .dialogs import Dialog

        def action(new_theme: str) -> None:
            config.set("theme", new_theme)
            Dialog.show_message("Theme will change after restarting the program")

        self.menu = Menu()
        self.menu.add("Dark Theme", lambda e: action("dark"))
        self.menu.add("Light Theme", lambda e: action("light"))
        self.menu.add("High Contrast", lambda e: action("high_contrast"))

    def show(self, event: Any = None) -> None:
        from .widgets import widgets

        if event:
            self.menu.show(event)
        else:
            widget = getattr(widgets, "main_menu_button")
            self.menu.show(widget=widget)


main_menu = MainMenu()
model_menu = ModelMenu()
gpt_menu = GPTMenu()
more_menu = MoreMenu()
tab_menu = TabMenu()
font_menu = FontMenu()
font_family_menu = FontFamilyMenu()
theme_menu = ThemeMenu()
