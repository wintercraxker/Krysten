import base64
import os
from io import BytesIO
from typing import Optional
from rich.console import Console
from rich.text import Text
import requests

from .discord_client import DiscordClient

INFO_STYLE = "bold white on #3498db"
SUCCESS_STYLE = "bold white on #3498db"
ERROR_STYLE = "bold white on #e53935"


def _emit(console: Console, kind: str, msg: str, style: str, sink):
    if callable(sink):
        try:
            sink(kind, msg)
            return
        except Exception:
            pass
    console.print(Text(msg, style=style))


def _data_uri_from_bytes(raw: bytes, mime: str) -> str:
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _guess_mime_from_ext(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".png",):
        return "image/png"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext in (".gif",):
        return "image/gif"
    return "image/png"


def prepare_icon_data(client: DiscordClient, spec: str) -> Optional[str]:
    if spec is None:
        return None
    s = spec.strip()
    if not s or s.lower() in ("skip",):
        return "__SKIP__"
    if s.lower() in ("remove", "none"):
        return None
    try:
        if s.startswith(("https://", "http://")):
            r = client.session.get(s, headers=client.headers, timeout=10)
            if r.status_code == 200:
                raw = r.content
                ct = r.headers.get("Content-Type", "image/png")
                if not ct.startswith("image/"):
                    ct = _guess_mime_from_ext(s)
                return _data_uri_from_bytes(raw, ct)
            else:
                raise RuntimeError("Failed to fetch icon URL")
        if s and s[0] == "<":
            parts = s.split(":")
            if len(parts) >= 3:
                animated = parts[0] == "<a"
                eid = parts[2][:-1]
                ext = "gif" if animated else "png"
                url = f"https://cdn.discordapp.com/emojis/{eid}.{ext}?v=1"
                r = client.session.get(url, headers=client.headers, timeout=10)
                if r.status_code == 200:
                    raw = r.content
                    ct = f"image/{ext}"
                    return _data_uri_from_bytes(raw, ct)
                else:
                    raise RuntimeError("Failed to fetch emoji icon")
        if os.path.isfile(s):
            with open(s, "rb") as f:
                raw = f.read()
            ct = _guess_mime_from_ext(s)
            return _data_uri_from_bytes(raw, ct)
    except Exception:
        raise
    raise RuntimeError("Unsupported icon spec")


def change_server_icon(console: Console, client: DiscordClient, guild_id: str, spec: Optional[str], log_sink=None):
    try:
        data = prepare_icon_data(client, spec or "")
        if data == "__SKIP__":
            _emit(console, "info", "Skipped icon.", INFO_STYLE, log_sink)
            return
        if data is None:
            _emit(console, "info", "Removing server icon...", INFO_STYLE, log_sink)
            ok = client.patch_guild(guild_id, {"icon": None}, reason="panel-server-icon")
            if ok:
                _emit(console, "success", "Removed server icon.", SUCCESS_STYLE, log_sink)
            else:
                _emit(console, "error", "Unable to remove server icon.", ERROR_STYLE, log_sink)
            return
        _emit(console, "info", "Setting server icon...", INFO_STYLE, log_sink)
        ok = client.patch_guild(guild_id, {"icon": data}, reason="panel-server-icon")
        if ok:
            _emit(console, "success", "Changed server icon.", SUCCESS_STYLE, log_sink)
        else:
            _emit(console, "error", "Unable to change server icon.", ERROR_STYLE, log_sink)
    except Exception:
        _emit(console, "error", "Icon spec not supported or fetch failed.", ERROR_STYLE, log_sink)


def change_server_name(console: Console, client: DiscordClient, guild_id: str, name: Optional[str], log_sink=None):
    s = (name or "").strip()
    if not s or s.lower() == "skip":
        _emit(console, "info", "Skipped name.", INFO_STYLE, log_sink)
        return
    if len(s) < 2 or len(s) > 100:
        _emit(console, "error", "Server name must be 2–100 characters.", ERROR_STYLE, log_sink)
        return
    me = client.get_me()
    if me:
        perms = client.permissions_for_member(guild_id, me.get("id"))
        ADMINISTRATOR = 1 << 3
        MANAGE_GUILD = 1 << 5
        if (perms & ADMINISTRATOR) == 0 and (perms & MANAGE_GUILD) == 0:
            _emit(console, "error", "Missing 'Manage Guild' permission.", ERROR_STYLE, log_sink)
            return
    _emit(console, "info", f"Setting server name to '{s}'...", INFO_STYLE, log_sink)
    ok = client.patch_guild(guild_id, {"name": s}, reason="panel-server-name")
    if ok:
        _emit(console, "success", "Changed server name.", SUCCESS_STYLE, log_sink)
    else:
        _emit(console, "error", "Unable to change server name.", ERROR_STYLE, log_sink)
