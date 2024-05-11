# Standard
from typing import Optional

# Modules
from .args import args
from .display import display
from .model import model


def summarize(tab_id: Optional[str] = None) -> None:
    tabconvo = display.get_tab_convo(tab_id)

    if not tabconvo:
        return

    text = tabconvo.convo.to_text()

    if not text:
        return

    prompt = {}
    prompt["user"] = "Please summarize this."
    prompt["text"] = f"{args.summarize_prompt}: "
    prompt["text"] += text

    tab_id = display.make_tab()
    model.stream(prompt, tab_id=tab_id)
