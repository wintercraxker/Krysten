from .config import load_token
from .validation import get_bot_name

def build_prompt() -> str:
    token = load_token()
    if token:
        name = get_bot_name(token)
        if name:
            return f"[{name}] -> "
    return ">> "