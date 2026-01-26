import time
import os
from rich.console import Console
from rich.align import Align
from rich.live import Live

from ui.animations import run_loading_animation, display_animated_message, get_animated_input
from ui.styles import glow_text
from core.validation import is_valid_token
from core.config import save_token, load_token
from ui.panel import show_command_panel

def hard_clear(console: Console):
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass
    console.clear()

def main():
    console = Console()
    hard_clear(console)

    run_loading_animation(console)

    existing_token = load_token()
    if existing_token and is_valid_token(existing_token):
        display_animated_message(console, "Token found. Opening panel...", duration=1.5, strength=1.2)
        hard_clear(console)
        show_command_panel(console)
        return

    # Explicit notice when token is missing or invalid
    display_animated_message(console, "Token not found. Please enter your token.", duration=1.8, strength=1.2)

    while True:
        token_value = get_animated_input(console)

        console.print()

        is_valid = False
        with Live(Align.center(glow_text("Validating token...", strength=1.0, bold=False)), console=console, transient=True):
            is_valid = is_valid_token(token_value)
            time.sleep(1.5)

        if is_valid:
            save_token(token_value)
            display_animated_message(console, "Token accepted and saved.", duration=2.0, strength=1.2)
            hard_clear(console)
            show_command_panel(console)
            break
        else:
            display_animated_message(console, "Invalid token. Please try again.", duration=2.0, strength=1.2, bold=False)

if __name__ == "__main__":
    main()
