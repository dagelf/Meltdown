# Standard
import os
import sys
import json
import subprocess
import shutil
import signal
import tempfile
import platform
import urllib.parse
import tkinter as tk
from pathlib import Path
from typing import List, Any, Optional

# Libraries
import psutil  # type: ignore
from tkinterdnd2 import TkinterDnD  # type: ignore

# Modules
from .theme import Theme
from .utils import utils


class App:
    def __init__(self) -> None:
        self.here = Path(__file__).parent.expanduser().resolve()
        manifest_path = Path(self.here, "manifest.json")

        with manifest_path.open("r", encoding="utf-8") as file:
            self.manifest = json.load(file)

        title = self.manifest["title"]

        self.intro = [
            f"Welcome to {title}.",
            "Write a prompt and press Enter.",
            "Type /about to learn more.",
        ]

        self.root: tk.Tk
        self.main_frame: tk.Frame
        self.theme: Theme
        self.sticky = False
        self.exit_delay = 100
        self.exit_after: str = ""
        self.streaming = False
        self.loading = False
        self.loaded = False
        self.checks_delay = 200
        self.system_frame_visible = True
        self.autorun_delay = 250
        self.geometry_delay = 250
        self.check_geometry_after = ""
        self.compact_enabled = False
        self.close_enabled = True
        self.clear_enabled = True
        self.time_started = 0.0

    def clear_geometry_after(self) -> None:
        if self.check_geometry_after:
            self.root.after_cancel(self.check_geometry_after)
            self.check_geometry_after = ""

    def on_frame_configure(self) -> None:
        self.clear_geometry_after()

        self.check_geometry_after = self.root.after(
            self.geometry_delay, lambda: self.on_geometry_change()
        )

    def setup_images(self) -> None:
        self.icon_path = Path(self.here, "icon.png")
        self.root.iconphoto(False, tk.PhotoImage(file=self.icon_path))
        self.image_path = Path(self.here, "image.jpg")

    def setup(self, time_started: float) -> None:
        self.time_started = time_started
        self.check_commandoc()
        self.check_compact()
        self.check_sticky()

    def sigint_handler(self, sig: Any, frame: Any) -> None:
        self.exit()

    def run(self) -> None:
        from .args import args

        if not args.show_terminal:
            signal.signal(signal.SIGINT, self.sigint_handler)

        self.autorun()
        self.root.mainloop()

    def exit(self, seconds: Optional[int] = None, force: bool = False) -> None:
        from .args import args
        from .display import display
        from .dialogs import Dialog

        if args.no_exit and (not force):
            return

        if args.confirm_exit and (not force):

            def action() -> None:
                self.exit(seconds, force=True)

            Dialog.show_confirm("Exit the program ?", action)
            return

        self.cancel_exit()
        d = (seconds * 1000) if seconds else self.exit_delay
        d = d if d >= self.exit_delay else self.exit_delay

        if not args.quiet:
            if seconds and seconds >= 1:
                secs = int(d / 1000)
                word = utils.singular_or_plural(secs, "second", "seconds")
                display.print(f"Exiting in {secs} {word}.")

        self.exit_after = self.root.after(d, lambda: self.root.destroy())

    def cancel_exit(self, feedback: bool = False) -> None:
        from .args import args
        from .display import display

        if args.quiet:
            feedback = False

        if self.exit_after:
            self.root.after_cancel(self.exit_after)
            self.exit_after = ""

            if feedback:
                display.print("Exit cancelled.")

    def exists(self) -> bool:
        try:
            return bool(self.root.winfo_exists())
        except RuntimeError:
            return False
        except tk.TclError:
            return False

    def show_about(self) -> None:
        from .args import args
        from .dialogs import Dialog

        title = self.manifest["title"]
        description = self.manifest["description"]
        version = self.manifest["version"]
        author = self.manifest["author"]
        repo = self.manifest["repo"]
        profile = args.profile

        lines = [
            f"{title} v{version}",
            description,
            f"Developed by {author}",
            "All Rights Reserved",
            repo,
            f"Profile: {profile}",
        ]

        cmds = []
        cmds.append(("Commands", lambda: self.show_help("commands")))
        cmds.append(("Arguments", lambda: self.show_help("arguments")))
        cmds.append(("Keyboard", lambda: self.show_help("keyboard")))
        cmds.append(("Ok", lambda: None))

        Dialog.show_commands("\n".join(lines), cmds, image=self.image_path)

    def toggle_maximize(self) -> None:
        if self.root.attributes("-zoomed"):
            self.unmaximize()
        else:
            self.maximize()

    def maximize(self, update: bool = True) -> None:
        self.root.attributes("-zoomed", True)

        if update:
            self.update_bottom()

    def unmaximize(self, update: bool = True) -> None:
        self.root.attributes("-zoomed", False)

        if update:
            self.update_bottom()

    def on_geometry_change(self) -> None:
        from .widgets import widgets

        self.clear_geometry_after()
        widgets.check_details_buttons(1)
        widgets.check_details_buttons(2)

    def set_geometry(self) -> None:
        from .args import args

        width = args.width if args.width != -1 else self.theme.width
        height = args.height if args.height != -1 else self.theme.height
        self.root.geometry(f"{width}x{height}")

        if args.maximize:
            app.update()
            self.maximize(False)

    def update(self) -> None:
        self.root.update_idletasks()

    def update_bottom(self) -> None:
        from .display import display

        display.to_bottom()

        def action() -> None:
            self.update()
            display.to_bottom()

        self.root.after(100, lambda: action())

    def resize(self) -> None:
        self.unmaximize(False)
        self.set_geometry()
        self.update_bottom()

    def toggle_compact(self) -> None:
        if self.compact_enabled:
            self.disable_compact()
        else:
            self.enable_compact()

    def enable_compact(self) -> None:
        from .widgets import widgets
        from .args import args

        confs = [
            args.compact_model,
            args.compact_system,
            args.compact_details_1,
            args.compact_details_2,
            args.compact_buttons,
            args.compact_file,
            args.compact_input,
        ]

        custom = any(confs)

        if custom:
            if args.compact_model:
                widgets.model_frame.grid_remove()

            if args.compact_system:
                widgets.system_frame.grid_remove()
                self.system_frame_visible = False

            if args.compact_details_1:
                widgets.details_frame_1.grid_remove()

            if args.compact_details_2:
                widgets.details_frame_2.grid_remove()

            if args.compact_buttons:
                widgets.buttons_frame.grid_remove()

            if args.compact_file:
                widgets.file_frame.grid_remove()

            if args.compact_input:
                widgets.input_frame.grid_remove()
        else:
            widgets.system_frame.grid_remove()
            widgets.details_frame_1.grid_remove()
            widgets.details_frame_2.grid_remove()
            self.system_frame_visible = False

        self.after_compact(True)

    def disable_compact(self) -> None:
        from .widgets import widgets

        widgets.model_frame.grid()
        widgets.system_frame.grid()
        widgets.details_frame_1.grid()
        widgets.details_frame_2.grid()
        widgets.buttons_frame.grid()
        widgets.file_frame.grid()
        widgets.input_frame.grid()
        self.system_frame_visible = True
        self.after_compact(False)

    def after_compact(self, enabled: bool) -> None:
        from .inputcontrol import inputcontrol

        self.update()
        inputcontrol.focus()
        self.compact_enabled = enabled

    def check_compact(self) -> None:
        from .args import args

        if args.compact or args.only_text:
            self.enable_compact()
        else:
            self.disable_compact()

    def get_opener(self) -> str:
        system = platform.system().lower()
        opener = ""

        if system == "darwin":
            opener = "open"
        elif system == "windows":
            opener = "start"
        else:
            opener = "xdg-open"

        return opener

    def run_command(self, cmd: List[str]) -> None:
        try:
            subprocess.Popen(
                cmd,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
        except BaseException as e:
            utils.error(e)

    def file_command(self, cmd: str, text: str) -> None:
        tmpdir = tempfile.gettempdir()
        name = f"mlt_file_{utils.now_int()}.txt"
        path = Path(tmpdir, name)

        with path.open("w", encoding="utf-8") as file:
            file.write(text)

        self.run_command([cmd, str(path)])

    def open_url(self, url: str) -> None:
        from .args import args

        self.open_generic(url, args.browser)

    def open_path(self, path: str) -> None:
        from .args import args

        self.open_generic(path, args.file_manager)

    def open_generic(self, arg: str, opener: Optional[str] = None) -> None:
        if not arg:
            return

        if opener:
            cmd = [opener, arg]
        else:
            cmd = [self.get_opener(), arg]

        self.run_command(cmd)

    def search_text(self, text: str) -> None:
        base_url = "https://www.google.com/search?"
        query_params = {"q": text}
        url = base_url + urllib.parse.urlencode(query_params)
        self.open_url(url)

    def get_terminal(self) -> List[str]:
        from .args import args

        cmd = []

        if args.terminal == "auto":
            if shutil.which("alacritty"):
                cmd = ["alacritty", "-e"]
            elif shutil.which("terminator"):
                cmd = ["terminator", "-e"]
            elif shutil.which("konsole"):
                cmd = ["konsole", "-e"]
            elif shutil.which("xterm"):
                cmd = ["urxvt", "-e"]
            elif shutil.which("xterm"):
                cmd = ["xterm", "-e"]
        else:
            cmd = [args.terminal, "-e"]

        return cmd

    def open_task_manager(self, mode: str = "normal") -> None:
        from .args import args

        cmd = self.get_terminal()

        if not cmd:
            return

        if mode == "normal":
            if args.task_manager == "auto":
                if shutil.which("btop"):
                    cmd.extend(["btop"])
                elif shutil.which("htop"):
                    cmd.extend(["htop"])
                elif shutil.which("top"):
                    cmd.extend(["top"])
                else:
                    return
            else:
                cmd.extend([args.task_manager])
        elif mode == "gpu":
            if args.task_manager_gpu == "auto":
                if shutil.which("amdgpu_top"):
                    cmd.extend(["amdgpu_top"])
                elif shutil.which("btop"):
                    cmd.extend(["btop"])
                elif shutil.which("htop"):
                    cmd.extend(["htop"])
                elif shutil.which("top"):
                    cmd.extend(["top"])
                else:
                    return
            else:
                cmd.extend([args.task_manager_gpu])

        self.run_command(cmd)

    def setup_focus(self) -> None:
        self.root.bind("<FocusIn>", lambda e: self.on_focus_in(e))
        self.root.bind("<FocusOut>", lambda e: self.on_focus_out(e))

    def on_focus_in(self, event: Any) -> None:
        from .dialogs import Dialog
        from .menus import Menu

        what = str(event.widget)

        if what == ".":
            Dialog.focus_all()
            Menu.focus_all()

    def on_focus_out(self, event: Any) -> None:
        from .keyboard import keyboard

        what = str(event.widget)

        if what == ".":
            keyboard.reset()

    def prepare(self) -> None:
        from .args import args

        if args.drag_and_drop:
            self.root = TkinterDnD.Tk(className=self.manifest["program"])
        else:
            self.root = tk.Tk(className=self.manifest["program"])

        title = args.title

        if not title:
            title = self.manifest["title"]

            if args.profile:
                title += f" ({args.profile})"

        self.root.title(title)
        self.main_frame = tk.Frame(self.root)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.minsize(100, 100)

        self.setup_images()
        self.setup_focus()
        self.setup_binds()

        self.main_frame.bind("<Configure>", lambda e: self.on_frame_configure())

        self.set_theme()
        self.set_geometry()
        self.show_window()

    def show_window(self) -> None:
        pad = self.theme.padx
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)

    def set_theme(self) -> None:
        from .config import config
        from .light_theme import LightTheme
        from .dark_theme import DarkTheme
        from .contrast_theme import ContrastTheme

        if config.theme == "light":
            self.theme = LightTheme()
        elif config.theme == "contrast":
            self.theme = ContrastTheme()
        else:
            self.theme = DarkTheme()

        self.theme.setup()

    def setup_binds(self) -> None:
        self.main_frame.bind("<Button-1>", lambda e: self.on_frame_click())

    def on_frame_click(self) -> None:
        self.hide_all()

    def toggle_fullscreen(self) -> None:
        if self.root.attributes("-fullscreen"):
            self.unfullscreen()
        else:
            self.fullscreen()

    def fullscreen(self) -> None:
        self.root.attributes("-fullscreen", True)

    def unfullscreen(self) -> None:
        self.root.attributes("-fullscreen", False)

    def show_help(self, what: str, mode: Optional[str] = None) -> None:
        from .display import display
        from .commands import commands
        from .keyboard import keyboard
        from .args import args

        if what == "commands":
            tab_id = display.make_tab("Commands", mode="ignore")
            commands.show_help(tab_id=tab_id, mode=mode)
        elif what == "arguments":
            tab_id = display.make_tab("Arguments", mode="ignore")
            args.show_help(tab_id=tab_id, mode=mode)
        elif what == "keyboard":
            tab_id = display.make_tab("Keyboard", mode="ignore")
            keyboard.show_help(tab_id=tab_id, mode=mode)
        else:
            return

        display.to_top(tab_id=tab_id)

    def hide_all(self, hide_dialog: bool = True, hide_menu: bool = True) -> None:
        from .dialogs import Dialog
        from .menus import Menu
        from .tooltips import ToolTip

        if hide_dialog:
            Dialog.hide_all()

        if hide_menu:
            Menu.hide_all()

        ToolTip.hide_all()

    def hide_frames(self) -> None:
        from .widgets import widgets

        widgets.model_frame.grid_remove()
        widgets.system_frame.grid_remove()
        widgets.details_frame_1.grid_remove()
        widgets.details_frame_2.grid_remove()
        widgets.buttons_frame.grid_remove()
        widgets.file_frame.grid_remove()
        widgets.input_frame.grid_remove()

    def autorun(self) -> None:
        from .args import args
        from .commands import commands

        if not args.autorun:
            return

        def action() -> None:
            commands.exec(args.autorun)

        self.root.after(self.autorun_delay, lambda: action())

    def stats(self) -> None:
        from .args import args
        from .commands import commands
        from .keyboard import keyboard
        from .dialogs import Dialog

        lines = []
        lines.append(f"Commands: {len(commands.commands)}")
        lines.append(f"Arguments: {len(vars(args))}")
        lines.append(f"Keyboard: {len(keyboard.commands)}")

        Dialog.show_message("\n".join(lines))

    def show_memory(self) -> None:
        from .dialogs import Dialog

        process = psutil.Process(os.getpid())
        memory_in_bytes = process.memory_info().rss
        memory_in_megabytes = int(memory_in_bytes / (1024 * 1024))
        Dialog.show_message(f"Memory: {memory_in_megabytes} MB")

    def show_started(self) -> None:
        from .dialogs import Dialog

        date = utils.to_date(self.time_started)
        date += "\n"
        date += utils.time_ago(self.time_started, utils.now())

        Dialog.show_message(date)

    def toggle_sticky(self) -> None:
        if self.sticky:
            self.disable_sticky()
        else:
            self.enable_sticky()

    def enable_sticky(self) -> None:
        self.sticky = True
        self.root.attributes("-topmost", True)

    def disable_sticky(self) -> None:
        self.sticky = False
        self.root.attributes("-topmost", False)

    def check_sticky(self) -> None:
        from .args import args

        if args.sticky:
            self.enable_sticky()

    def check_commandoc(self) -> None:
        from .args import args
        from .commands import commands

        exit = False

        if args.commandoc:
            commands.run("commandoc", args.commandoc)
            exit = True

        if args.argumentdoc:
            commands.run("argumentdoc", args.argumentdoc)
            exit = True

        if args.keyboardoc:
            commands.run("keyboardoc", args.keyboardoc)
            exit = True

        if exit:
            sys.exit(0)

    def do_checks(self) -> None:
        from .args import args
        from .model import model
        from .commands import commands
        from .widgets import widgets
        from .display import display

        if model.loaded_model:
            if not self.loaded:
                self.loaded = True
                widgets.load_button.set_text("Unload")

                self.update()
                widgets.model.move_to_end()
        elif self.loaded:
            self.loaded = False
            widgets.load_button.set_text("Load")

            self.update()
            widgets.model.move_to_end()

        if model.streaming:
            if not self.streaming:
                self.streaming = True
                widgets.enable_stop_button()
        elif self.streaming:
            self.streaming = False
            widgets.disable_stop_button()
            display.stream_stopped()
            commands.after_stream()

        if args.disable_buttons:
            model_empty = widgets.model.get() == ""

            if model.model_loading or (model_empty and (not model.loaded_model)):
                if not self.loading:
                    self.loading = True
                    widgets.disable_load_button()
                    widgets.disable_format_select()
            elif self.loading:
                self.loading = False
                widgets.enable_load_button()
                widgets.enable_format_select()

            if display.num_tabs_open <= 1:
                if self.close_enabled:
                    self.close_enabled = False
                    widgets.disable_close_button()
            elif not self.close_enabled:
                self.close_enabled = True
                widgets.enable_close_button()

            if (not display.is_modified()) or display.is_ignored():
                if self.clear_enabled:
                    self.clear_enabled = False
                    widgets.disable_clear_button()
            elif not self.clear_enabled:
                self.clear_enabled = True
                widgets.enable_clear_button()

    def start_checks(self) -> None:
        self.do_checks()
        app.root.after(self.checks_delay, self.start_checks)

    def program(self, mode: str, cmd: Optional[str] = None) -> None:
        from .args import args
        from .display import display

        if not cmd:
            if mode == "text":
                cmd = args.progtext or args.program
            elif mode == "json":
                cmd = args.progjson or args.program

        if not cmd:
            display.print("No program specified.")
            return

        tabconvo = display.get_tab_convo(None)

        if not tabconvo:
            return

        if mode == "text":
            text = tabconvo.convo.to_text()
            ext = "txt"
        elif mode == "json":
            text = tabconvo.convo.to_json()
            ext = "json"
        else:
            return

        tmpdir = tempfile.gettempdir()
        name = f"mlt_{utils.now_int()}.{ext}"
        path = Path(tmpdir, name)

        with path.open("w", encoding="utf-8") as file:
            file.write(text)

        self.run_command([cmd, str(path)])

    def focused(self) -> Optional[tk.Widget]:
        if app.exists():
            widget = self.root.focus_get()

            if isinstance(widget, tk.Widget):
                return widget

        return None

    def open_profile(self) -> None:
        from .paths import paths
        from .dialogs import Dialog

        cmds = []

        def show_config() -> None:
            self.open_generic(str(paths.config_dir))

        def show_data() -> None:
            self.open_generic(str(paths.data_dir))

        cmds.append(("Config", lambda: show_config()))
        cmds.append(("Data", lambda: show_data()))

        Dialog.show_commands("Open directories", cmds)

    def show_info(self) -> None:
        from .dialogs import Dialog

        cmds = []
        cmds.append(("Memory", lambda: app.show_memory()))
        cmds.append(("Started", lambda: app.show_started()))

        Dialog.show_commands("Information", cmds)


app = App()
