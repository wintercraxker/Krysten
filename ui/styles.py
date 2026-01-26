from rich.text import Text

PALETTE = ["#ff2f2f", "#ff4a4a", "#ff6a6a", "#ff8f8f", "#ffd0d0", "#ffffff"]

def glow_style(i, n, strength=1.0, phase=0.0):
    if n <= 1:
        return PALETTE[-1]
    x = (i / (n - 1) + phase) % 1.0
    mid = 1 - abs(2 * x - 1)
    mid = mid ** (0.55 / max(0.05, strength))
    idx = int(mid * (len(PALETTE) - 1))
    return PALETTE[idx]

def glow_text(s, strength=1.0, bold=True, phase=0.0):
    t = Text()
    n = len(s)
    for i, ch in enumerate(s):
        st = glow_style(i, n, strength, phase)
        t.append(ch, style=f"{'bold ' if bold else ''}{st}")
    return t

def bar_fill(p, width=46):
    out = Text()
    filled = int(p * width)
    for i in range(width):
        if i < filled:
            out.append("█", style="bold red")
        else:
            out.append("░", style="#bfbfbf")
    return out

BLUE_STYLE = "bold white on #3498db"
RED_STYLE = "bold white on #e53935"

SUCCESS_GRAD = ["#2ecc71", "#3bd36a", "#7fd235", "#b8d12b", "#f1c40f"]
BLUE_GRAD = ["#2980b9", "#3498db", "#40a9f3", "#5dade2", "#85c1e9"]
RED_GRAD = ["#e74c3c", "#e53935", "#ff2f2f", "#ff4a4a", "#ff6a6a"]

def gradient_text(s: str, palette: list[str], bold: bool = True) -> Text:
    t = Text()
    n = len(s)
    for i, ch in enumerate(s):
        idx = int((i / max(1, n - 1)) * (len(palette) - 1))
        color = palette[idx]
        t.append(ch, style=(f"bold {color}" if bold else color))
    return t

def gradient_bg_text(s: str, palette: list[str], bold: bool = True) -> Text:
    t = Text()
    n = len(s)
    for i, ch in enumerate(s):
        idx = int((i / max(1, n - 1)) * (len(palette) - 1))
        color = palette[idx]
        t.append(ch, style=(f"bold white on {color}" if bold else f"white on {color}"))
    return t

def success_prefix() -> Text:
    return gradient_bg_text("[SUCCESS]", SUCCESS_GRAD, bold=True)

def error_prefix() -> Text:
    return gradient_bg_text("[ERROR]", RED_GRAD, bold=True)

def info_prefix() -> Text:
    return gradient_bg_text("[INFO]", BLUE_GRAD, bold=True)

def finalized_prefix() -> Text:
    return gradient_bg_text("[FINALIZED]", BLUE_GRAD, bold=True)

def format_log(kind: str, message: str) -> Text:
    line = Text()
    if kind == "success":
        line.append(success_prefix())
    elif kind == "error":
        line.append(error_prefix())
    elif kind == "finalized":
        line.append(finalized_prefix())
    else:
        line.append(info_prefix())
    line.append(" - ", style="#bfbfbf")
    line.append(message, style="bold white")
    return line
