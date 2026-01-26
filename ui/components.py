from rich.console import Console
from rich.align import Align
from rich.text import Text
from rich.console import Group

from .styles import glow_style, glow_text, bar_fill

ASCII = r"""
    __ __                 __           
   / //_/_______  _______/ /____  ____ 
  / ,<  / ___/ / / / ___/ __/ _ \/ __ \
 / /| |/ /  / /_/ (__  ) /_/  __/ / / /
/_/ |_/_/   \__, /____/\__/\___/_/ /_/ 
           /____/                      
""".strip("\n")

def glow_ascii(block):
    lines = block.splitlines()
    w = max((len(x) for x in lines), default=1)
    out = Text()
    for line in lines:
        line = line.ljust(w)
        for i, ch in enumerate(line):
            if ch == " ":
                out.append(" ")
            else:
                out.append(ch, style=f"bold {glow_style(i, w, 0.9)}")
        out.append("\n")
    return out

def loading_frame(p, dots, phase=0.0):
    logo = glow_ascii(ASCII)
    load = glow_text(f"Loading{dots}".ljust(12), strength=1.2, phase=phase)
    bar = bar_fill(p)
    return Align.center(
        Group(
            Align.center(logo),
            Text(),
            Align.center(load),
            Text(),
            Align.center(bar),
        )
    )

def ready_screen(console: Console, phase: float = 0.0):
    logo = glow_ascii(ASCII)
    prompt_text = glow_text("Enter bot token:", strength=1.25, phase=phase)
    
    return Group(
        Align.center(logo),
        Text(),
        Align.center(prompt_text),
        Text(),
    )

def logo_block():
    return glow_ascii(ASCII)

def prompt_screen(prompt: str, phase: float = 0.0):
    logo = glow_ascii(ASCII)
    prompt_text = glow_text(prompt, strength=1.3, phase=phase)
    return Group(
        Align.center(logo),
        Text(),
        Align.center(prompt_text),
        Text(),
    )

def prompt_input_screen(prompt: str, typed: str, phase: float = 0.0, pad: int = 0, show_cursor: bool = False):
    logo = glow_ascii(ASCII)
    prompt_text = glow_text(prompt, strength=1.3, phase=phase)
    combined = Text(" " * max(0, pad))
    combined.append(prompt_text)
    if typed:
        combined.append(typed)
    if show_cursor:
        combined.append(glow_text("|", strength=1.2, phase=phase))
    return Group(
        Align.center(logo),
        Text(),
        Align.left(combined),
        Text(),
    )
