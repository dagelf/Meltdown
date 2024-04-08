# Standard
import re
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

# Modules
from .app import app
from .config import config
from .dialogs import Dialog
from .menus import Menu
from .args import args
from .paths import paths
from . import utils
from . import timeutils
from . import filemanager


class QueueItem:
    def __init__(self, cmd: str, argument: str) -> None:
        self.cmd = cmd
        self.argument = argument


class Queue:
    def __init__(self, items: List[QueueItem], wait: float = 0.0) -> None:
        self.items = items
        self.wait = wait


class Commands:
    def __init__(self) -> None:
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.loop_delay = 25
        self.queues: List[Queue] = []

    def setup(self) -> None:
        prefix = utils.escape_regex(args.prefix)
        andchar = utils.escape_regex(args.andchar)
        self.cmd_pattern = fr"{andchar}(?= {prefix}\w+)"

        self.make_commands()
        self.make_aliases()
        self.load_file()
        self.start_loop()
        self.get_cmdkeys()

    def get_cmdkeys(self) -> None:
        self.cmdkeys = []

        for key in self.commands:
            self.cmdkeys.append(key)

        for key in self.aliases:
            self.cmdkeys.append(key)

    def start_loop(self) -> None:
        def loop() -> None:
            for queue in self.queues:
                if queue.wait > 0.0:
                    queue.wait -= self.loop_delay

                    if queue.wait <= 0.0:
                        queue.wait = 0.0

                    continue

                if queue.items:
                    item = queue.items.pop(0)

                    if item.cmd == "sleep":
                        if not item.argument:
                            item.argument = "1"

                        if item.argument and queue.items:
                            queue.wait = float(item.argument) * 1000.0
                    else:
                        if self.aliases.get(item.cmd):
                            self.exec(self.aliases[item.cmd], queue)
                        else:
                            self.try_to_run(item.cmd, item.argument)

                    if not queue.items:
                        self.queues.remove(queue)

            app.root.after(self.loop_delay, lambda: loop())

        loop()

    def make_commands(self) -> None:
        from .display import display
        from .model import model
        from .session import session
        from .logs import logs
        from .widgets import widgets
        from .inputcontrol import inputcontrol
        force = "Use 'force' to force"
        file_name = "You can provide the file name"
        sortfilter = "Use 'sort' or a word to filter"

        self.commands = {
            "clear": {
                "help": "Clear the conversation",
                "extra": force,
                "action": lambda a=None: display.clear(force=a),
                "type": "force",
            },
            "exit": {
                "help": "Exit the application. Optional seconds delay",
                "action": lambda a=None: app.exit(a),
                "type": float,
            },
            "cancelexit": {
                "help": "Cancel the exit if you had set a delay",
                "action": lambda a=None: app.cancel_exit(True),
            },
            "compact": {
                "help": "Toggle compact mode",
                "action": lambda a=None: app.toggle_compact(),
            },
            "log": {
                "help": "Show the log menu",
                "action": lambda a=None: logs.menu(),
            },
            "logtext": {
                "help": "Save conversation to a text file",
                "action": lambda a=None: logs.to_text(),
            },
            "logjson": {
                "help": "Save conversation to a JSON file",
                "action": lambda a=None: logs.to_json(),
            },
            "logtextall": {
                "help": "Save all conversations to text files",
                "action": lambda a=None: logs.to_text(True),
            },
            "logjsonall": {
                "help": "Save all conversations to JSON files",
                "action": lambda a=None: logs.to_json(True),
            },
            "logsdir": {
                "help": "Open the logs directory",
                "action": lambda a=None: logs.open(),
            },
            "resize": {
                "help": "Resize the window",
                "action": lambda a=None: app.resize(),
            },
            "stop": {
                "help": "Stop the current stream",
                "action": lambda a=None: model.stop_stream(),
            },
            "system": {
                "help": "Open the system task manager",
                "action": lambda a=None: app.open_task_manager(),
            },
            "top": {
                "help": "Scroll to the top",
                "action": lambda a=None: display.to_top(),
            },
            "bottom": {
                "help": "Scroll to the bottom",
                "action": lambda a=None: display.to_bottom(),
            },
            "maximize": {
                "help": "Maximize the window",
                "action": lambda a=None: app.toggle_maximize(),
            },
            "close": {
                "help": "Close current tab",
                "extra": force,
                "action": lambda a=None: display.close_tab(force=a),
                "type": "force",
            },
            "closeothers": {
                "help": "Close other tabs",
                "extra": force,
                "action": lambda a=None: display.close_other_tabs(force=a),
                "type": "force",
            },
            "closeall": {
                "help": "Close all tabs",
                "extra": force,
                "action": lambda a=None: display.close_all_tabs(force=a),
                "type": "force",
            },
            "closeold": {
                "help": "Close old tabs",
                "extra": force,
                "action": lambda a=None: display.close_old_tabs(force=a),
                "type": "force",
            },
            "closeleft": {
                "help": "Close tabs to the left",
                "extra": force,
                "action": lambda a=None: display.close_tabs_left(force=a),
                "type": "force",
            },
            "closeright": {
                "help": "Close tabs to the right",
                "extra": force,
                "action": lambda a=None: display.close_tabs_right(force=a),
                "type": "force",
            },
            "new": {
                "help": "Make a new tab",
                "action": lambda a=None: display.make_tab(),
            },
            "theme": {
                "help": "Change the color theme",
                "action": lambda a=None: app.toggle_theme(),
            },
            "about": {
                "help": "Show the about window",
                "action": lambda a=None: app.show_about(),
            },
            "help": {
                "help": "Show help information",
                "action": lambda a=None: self.help_command(),
            },
            "commands": {
                "help": "Show the commands help",
                "action": lambda a=None: app.show_help("commands", mode=a),
                "extra": sortfilter,
                "type": str,
            },
            "arguments": {
                "help": "Show the arguments help",
                "action": lambda a=None: app.show_help("arguments", mode=a),
                "extra": sortfilter,
                "type": str,
            },
            "keyboard": {
                "help": "Show the keyboard help",
                "action": lambda a=None: app.show_help("keyboard", mode=a),
                "extra": sortfilter,
                "type": str,
            },
            "list": {
                "help": "Show the tab list to pick a tab",
                "action": lambda a=None: display.show_tab_list(),
            },
            "find": {
                "help": "Find a text string",
                "action": lambda a=None: display.find(query=a),
                "type": str,
            },
            "findall": {
                "help": "Find a text string among all tabs",
                "action": lambda a=None: display.find_all(a),
                "type": str,
            },
            "first": {
                "help": "Go to the first tab",
                "action": lambda a=None: display.select_first_tab(),
            },
            "last": {
                "help": "Go to the last tab",
                "action": lambda a=None: display.select_last_tab(),
            },
            "config": {
                "help": "Show the config menu",
                "action": lambda a=None: config.menu(),
            },
            "session": {
                "help": "Show the session menu",
                "action": lambda a=None: session.menu(),
            },
            "reset": {
                "help": "Reset the config",
                "extra": force,
                "action": lambda a=None: config.reset(force=a),
                "type": "force",
            },
            "viewtext": {
                "help": "View raw text",
                "action": lambda a=None: display.view_text(),
            },
            "viewjson": {
                "help": "View raw JSON",
                "action": lambda a=None: display.view_json(),
            },
            "move": {
                "help": "Move tab to start or end",
                "action": lambda a=None: display.move_tab(True),
            },
            "tab": {
                "help": "Go to a tab by its number or by its name",
                "action": lambda a=None: display.select_tab_by_string(a),
                "type": str,
                "arg_req": True,
            },
            "fullscreen": {
                "help": "Toggle fullscreen",
                "action": lambda a=None: app.toggle_fullscreen(),
            },
            "next": {
                "help": "Find next text match",
                "action": lambda a=None: display.find_next(),
            },
            "scrollup": {
                "help": "Scroll up",
                "action": lambda a=None: display.scroll_up(),
            },
            "scrolldown": {
                "help": "Scroll down",
                "action": lambda a=None: display.scroll_down(),
            },
            "load": {
                "help": "Load the model",
                "action": lambda a=None: model.load(),
            },
            "unload": {
                "help": "Unload the model",
                "action": lambda a=None: model.unload(True),
            },
            "context": {
                "help": "Show the context list",
                "action": lambda a=None: widgets.show_context(),
            },
            "left": {
                "help": "Go to the tab on the left",
                "action": lambda a=None: display.tab_left(),
            },
            "right": {
                "help": "Go to the tab on the right",
                "action": lambda a=None: display.tab_right(),
            },
            "menu": {
                "help": "Show the main menu",
                "action": lambda a=None: widgets.show_main_menu(),
            },
            "savesession": {
                "help": "Save the current session",
                "action": lambda a=None: session.save_state(name=a),
                "type": str,
            },
            "loadsession": {
                "help": "Load a session",
                "extra": file_name,
                "action": lambda a=None: session.load_state(name=a),
                "type": str,
            },
            "saveconfig": {
                "help": "Save the current config",
                "action": lambda a=None: config.save_state(name=a),
                "type": str,
            },
            "loadconfig": {
                "help": "Load a session",
                "extra": file_name,
                "action": lambda a=None: config.load_state(name=a),
                "type": str,
            },
            "copy": {
                "help": "Copy all the text",
                "action": lambda a=None: display.copy_output(),
            },
            "select": {
                "help": "Select all text",
                "action": lambda a=None: display.select_output(),
            },
            "deselect": {
                "help": "Deselect all text",
                "action": lambda a=None: display.deselect_output(),
            },
            "browse": {
                "help": "Browse the models",
                "action": lambda a=None: model.browse_models(),
            },
            "palette": {
                "help": "Show the command palette",
                "action": lambda a=None: self.show_palette(),
            },
            "rename": {
                "help": "Rename the tab",
                "action": lambda a=None: display.rename_tab(True),
            },
            "input": {
                "help": "Prompt the AI with this input",
                "action": lambda a=None: inputcontrol.submit(text=a),
                "type": str,
                "arg_req": True,
            },
            "write": {
                "help": "Set the input without submitting",
                "action": lambda a=None: inputcontrol.set(text=a),
                "type": str,
                "arg_req": True,
            },
            "sleep": {
                "help": "Wait X seconds before running the next command",
                "action": lambda a=None: None,
                "type": int,
                "arg_req": True,
            },
            "hide": {
                "help": "Close dialogs and menus",
                "action": lambda a=None: app.hide_all(),
            },
            "printconfig": {
                "help": "Print all the config settings",
                "action": lambda a=None: config.print_config(),
            },
            "bigger": {
                "help": "Increase the font size",
                "action": lambda a=None: display.increase_font(),
            },
            "smaller": {
                "help": "Decrease the font size",
                "action": lambda a=None: display.decrease_font(),
            },
            "font": {
                "help": "Set an exact font size",
                "action": lambda a=None: display.set_font_size(a),
                "type": int,
                "arg_req": True,
            },
            "resetfont": {
                "help": "Reset the font size",
                "action": lambda a=None: display.reset_font(),
            },
            "togglescroll": {
                "help": "Scroll to the bottom or to the top",
                "action": lambda a=None: display.toggle_scroll(),
            },
            "setconfig": {
                "help": "Set a config: [key] [value]",
                "action": lambda a=None: config.set_command(a),
                "type": str,
                "arg_req": True,
            },
            "resetconfig": {
                "help": "Reset a config: [key]",
                "action": lambda a=None: config.reset_one(a),
                "type": str,
                "arg_req": True,
            },
            "stats": {
                "help": "Show some internal information",
                "action": lambda a=None: app.stats()
            },
            "sticky": {
                "help": "Make the window stay at the top",
                "action": lambda a=None: app.toggle_sticky()
            },
            "commandoc": {
                "help": "Make a file with all the commands. Provide a path",
                "action": lambda a=None: self.to_markdown(a),
                "type": str,
                "arg_req": True,
            },
            "active": {
                "help": "Go to the tab that is currently streaming",
                "action": lambda a=None: display.select_active_tab(),
            },
        }

        for key in self.commands:
            self.commands[key]["date"] = 0.0

    def make_aliases(self) -> None:
        self.aliases = {}

        for alias in args.aliases:
            split = alias.split("=")
            key = split[0].strip()
            value = "=".join(split[1:]).strip()

            if not key or not value:
                continue

            self.aliases[key] = value

    def is_command(self, text: str) -> bool:
        if len(text) < 2:
            return False

        with_prefix = text.startswith(args.prefix)
        second_char = text[1:2]
        return with_prefix and second_char.isalpha()

    def exec(self, text: str, queue: Optional[Queue] = None) -> bool:
        text = text.strip()

        if not self.is_command(text):
            return False

        cmds = re.split(self.cmd_pattern, text)
        items = []

        for item in cmds:
            split = item.strip().split(" ")
            cmd = split[0][1:]
            argument = " ".join(split[1:])
            queue_item = QueueItem(cmd, argument)
            items.append(queue_item)

        if items:
            if queue:
                queue.items = items + queue.items
            else:
                queue = Queue(items)
                self.queues.append(queue)

        return True

    def run(self, cmd: str, argument: str = "") -> None:
        item = self.commands.get(cmd)

        if not item:
            return

        arg_req = item.get("arg_req")

        if (not argument) and arg_req:
            return

        argtype = item.get("type")
        new_argument: Any = None

        if argtype and argument:
            if argtype == "force":
                new_argument = True if argument.lower() == "force" else False
            elif argtype == str:
                new_argument = self.argument_replace(argument)
            else:
                new_argument = argtype(argument)

        item = self.commands[cmd]
        item["action"](new_argument)
        item["date"] = timeutils.now()
        self.save_commands()

    def argument_replace(self, argument: str) -> str:
        return argument.replace(f"{args.keychar}now", str(timeutils.now_int()))

    def save_commands(self) -> None:
        cmds = {}

        for key in self.commands:
            cmds[key] = {"date": self.commands[key]["date"]}

        filemanager.save(paths.commands, cmds)

    def try_to_run(self, cmd: str, argument: str) -> None:
        # Check normal
        for key in self.commands.keys():
            if cmd == key:
                self.run(key, argument)
                return

        # Similarity on keys
        for key in self.commands.keys():
            if utils.check_match(cmd, key):
                self.run(key, argument)
                return

    def help_command(self) -> None:
        from .display import display
        p = args.prefix

        items = []
        items.append(f"Use {p}commands to see commands")
        items.append(f"Use {p}arguments to see command line arguments")
        items.append(f"Use {p}keyboard to see keyboard shortcuts")

        text = "\n".join(items)
        display.print(text)

    def show_help(self, tab_id: str = "", mode: str = "") -> None:
        from .display import display
        display.print("Commands:", tab_id=tab_id)
        text = []

        keys = list(self.commands.keys())

        if mode:
            if mode == "sort":
                keys = list(sorted(keys))
            else:
                keys = [key for key in keys if mode in key]

        for key in keys:
            data = self.commands[key]
            msg = data["help"]
            extra = data.get("extra")

            if extra:
                msg += f" ({extra})"

            text.append(f"{args.prefix}{key} = {msg}")

        display.print("\n".join(text), tab_id=tab_id)

    def make_palette(self) -> None:
        self.palette = Menu()

        def add_item(key: str) -> None:
            cmd = self.commands[key]

            def command() -> None:
                if cmd.get("arg_req"):
                    Dialog.show_input("Argument", lambda a: self.run(key, a))
                else:
                    self.run(key)

            if args.alt_palette:
                text = key
                tooltip = cmd["help"]
            else:
                text = cmd["help"]
                tooltip = key

            self.palette.add(text=text, command=command, tooltip=tooltip)

        keys = sorted(self.commands, key=lambda x: self.commands[x]["date"], reverse=True)

        for key in keys:
            add_item(key)

    def show_palette(self) -> None:
        from .widgets import widgets
        self.make_palette()
        self.palette.show(widget=widgets.main_menu_button)

    def cmd(self, text: str) -> str:
        return args.prefix + text

    def load_file(self) -> None:
        if (not paths.commands.exists()) or (not paths.commands.is_file()):
            return

        with open(paths.commands, "r", encoding="utf-8") as file:
            try:
                cmds = json.load(file)
            except BaseException:
                cmds = {}

        for key in cmds:
            if key in self.commands:
                self.commands[key]["date"] = cmds[key].get("date", 0.0)

    def to_markdown(self, pathstr: str) -> None:
        from .display import display
        path = Path(pathstr)

        if (not path.parent.exists()) or (not path.parent.is_dir()):
            utils.error(f"Invalid path: {pathstr}")
            return

        text = "## Commands\n\n"
        text += "These are all the available commands."
        sep = "\n\n---\n\n"

        for key in self.commands:
            cmd = self.commands[key]
            info = cmd["help"]
            text += sep
            text += f">{key}\n\n"
            text += info

        with open(path, "w", encoding="utf-8") as file:
            file.write(text)

        msg = f"Saved to {path}"
        display.print(msg)
        utils.msg(msg)

    def after_stream(self) -> None:
        if args.after_stream:
            app.root.after(100, lambda: self.exec(args.after_stream))


commands = Commands()
