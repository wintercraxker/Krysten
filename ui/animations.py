import time
import os
import sys
from rich.console import Console
from rich.live import Live
from rich.align import Align
from rich.console import Group

from .components import loading_frame, prompt_screen, prompt_input_screen
from .styles import glow_text
from core.prompt import build_prompt

def run_loading_animation(console: Console):
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass
    console.clear()
    dur = 2.2
    start = time.time()

    with Live(loading_frame(0.0, "."), console=console, refresh_per_second=24) as live:
        while True:
            t = time.time() - start
            p = min(1.0, t / dur)
            
            dot_count = int((t * 2.5) % 4)
            dots = "." * dot_count
            
            phase = (t * 0.4) % 1.0
            
            live.update(loading_frame(p, dots, phase))
            if p >= 1.0:
                break
            time.sleep(0.04)

def get_animated_input(console: Console) -> str:
    console.clear()

    prompt_text = build_prompt()
    is_windows = sys.platform == "win32"

    if is_windows:
        import msvcrt
        typed = ""
        pad = max(0, (console.size.width // 2) - 31)
        with Live(console=console, transient=False, refresh_per_second=24) as live:
            start = time.time()
            while True:
                phase = ((time.time() - start) * 0.4) % 1.0
                show_cursor = int((time.time() * 2) % 2) == 0  
                live.update(prompt_input_screen(prompt_text, typed, phase, pad, show_cursor))

                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch in ("\r", "\n"):
                        break
                    elif ch in ("\b", "\x08"):
                        if typed:
                            typed = typed[:-1]
                    else:
                        typed += ch
                time.sleep(0.03)
        return typed
    else:
  
        with Live(console=console, transient=True, refresh_per_second=24) as live:
            anim_start = time.time()
            while time.time() - anim_start < 1.6:
                current_time = time.time() - anim_start
                phase = (current_time * 0.4) % 1.0
                live.update(prompt_screen(prompt_text, phase))
                time.sleep(0.04)

        pad = max(0, (console.size.width // 2) - 31)
        prompt = glow_text(prompt_text, strength=1.4)
        console.print(" " * pad, end="")
        return console.input(prompt)

def display_animated_message(console: Console, message: str, duration: float, strength: float = 1.2, bold: bool = True):
    start_time = time.time()
    with Live(console=console, transient=True, refresh_per_second=15) as live:
        while time.time() - start_time < duration:
            current_time = time.time() - start_time
            phase = (current_time * 0.4) % 1.0
            live.update(Align.center(glow_text(message, strength=strength, bold=bold, phase=phase)))
            time.sleep(0.05)

