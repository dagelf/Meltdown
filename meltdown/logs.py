# Standard
from pathlib import Path
from typing import Optional

# Modules
from .app import app
from .dialogs import Dialog
from .display import display
from .args import args
from .session import session
from .session import Conversation
from .paths import paths
from .files import files
from .utils import utils


class Logs:
    def menu(self, full: bool = True, tab_id: Optional[str] = None) -> None:
        cmds = []

        if full:
            cmds.append(("Open", lambda: self.open()))
            cmds.append(("Save All", lambda: self.save_all()))

        cmds.append(("To JSON", lambda: self.to_json(tab_id=tab_id)))
        cmds.append(("To Text", lambda: self.to_text(tab_id=tab_id)))

        Dialog.show_commands("Save conversation to a file?", cmds)

    def save_all(self) -> None:
        cmds = []
        cmds.append(("To JSON", lambda: self.to_json(True)))
        cmds.append(("To Text", lambda: self.to_text(True)))
        Dialog.show_commands("Save all conversations?", cmds)

    def save_file(
        self, text: str, name: str, ext: str, save_all: bool, overwrite: bool, mode: str
    ) -> None:
        text = text.strip()
        name = name.replace(" ", "_").lower()
        paths.logs.mkdir(parents=True, exist_ok=True)
        file_name = name + f".{ext}"
        file_path = Path(paths.logs, file_name)
        num = 2

        if (not overwrite) and args.increment_logs:
            while file_path.exists():
                file_name = f"{name}_{num}.{ext}"
                file_path = Path(paths.logs, file_name)
                num += 1

                if num > 9999:
                    break

        with file_path.open("w", encoding="utf-8") as file:
            file.write(text)

        if not save_all:
            if not args.quiet and args.log_feedback:
                msg = f"Log saved as {file_name}"
                display.print(utils.emoji_text(msg, "storage"))

            cmd = ""

            if (mode == "text") and args.on_log_text:
                cmd = args.on_log_text
            elif (mode == "json") and args.on_log_json:
                cmd = args.on_log_json
            elif args.on_log:
                cmd = args.on_log

            if cmd:
                app.run_command([cmd, str(file_path)])

    def save(
        self,
        mode: str,
        save_all: bool,
        name: Optional[str] = None,
        tab_id: Optional[str] = None,
    ) -> None:
        if mode == "text":
            ext = "txt"
        elif mode == "json":
            ext = "json"
        else:
            return

        num = 0

        if save_all:
            conversations = [
                session.get_conversation(key) for key in session.conversations
            ]
        else:
            tabconvo = display.get_tab_convo(tab_id)

            if not tabconvo:
                return

            conversations = [tabconvo.convo]

        for conversation in conversations:
            if not conversation:
                continue

            if mode == "text":
                text = self.get_text(conversation)
            elif mode == "json":
                text = self.get_json(conversation)
            else:
                text = ""

            if not text:
                continue

            num += 1

            if not name:
                name = conversation.name
                overwrite = False
            else:
                overwrite = True

            self.save_file(text, name, ext, save_all, overwrite=overwrite, mode=mode)

        if save_all:
            if args.quiet or (not args.log_feedback):
                return

            f_type = "text" if mode == "text" else "JSON"
            word = utils.singular_or_plural(num, "log", "logs")
            msg = f"{num} {f_type} {word} saved."
            display.print(utils.emoji_text(msg, "storage"))

    def to_json(
        self,
        save_all: bool = False,
        name: Optional[str] = None,
        tab_id: Optional[str] = None,
    ) -> None:
        self.save("json", save_all, name, tab_id=tab_id)

    def get_json(self, conversation: Conversation) -> str:
        if not conversation:
            return ""

        if not conversation.items:
            return ""

        return conversation.to_json()

    def to_text(
        self,
        save_all: bool = False,
        name: Optional[str] = None,
        tab_id: Optional[str] = None,
    ) -> None:
        self.save("text", save_all, name, tab_id=tab_id)

    def get_text(self, conversation: Conversation) -> str:
        if not conversation:
            return ""

        if not conversation.items:
            return ""

        text = conversation.to_text()

        if not text:
            return ""

        full_text = ""
        full_text += conversation.name + "\n"
        full_text += utils.date() + "\n\n"
        full_text += text
        return full_text

    def open(self, name: Optional[str] = None) -> None:
        files.open_log(name)


logs = Logs()
