import time
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.text import Text

from .discord_client import DiscordClient

INFO_STYLE = "bold white on #3498db"
SUCCESS_STYLE = "bold white on #3498db"
ERROR_STYLE = "bold white on #e53935"


def delete_channels(console: Console, client: DiscordClient, guild_id: str, reason: str = "panel-delete-channels", log_sink=None):
    def emit(kind: str, msg: str, style: str):
        if callable(log_sink):
            try:
                log_sink(kind, msg)
                return
            except Exception:
                pass
        console.print(Text(msg, style=style))

    chans: List[dict] = client.list_channels(guild_id)
    if not chans:
        emit("error", "No channels fetched or insufficient permissions.", ERROR_STYLE)
        return

    emit("info", "Starting to delete all channels...", INFO_STYLE)
    emit("info", f"Channels to delete: {len(chans)}", INFO_STYLE)

    ok = 0
    err = 0

    def worker(ch: dict) -> tuple[str, bool]:
        cid = str(ch.get("id"))
        name = ch.get("name")
        done = client.delete_channel(cid, reason=reason)
        return (name, done)

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(worker, c): c for c in chans}
        for fut in as_completed(futures):
            name, done = fut.result()
            if done:
                ok += 1
                emit("success", f"Deleted {name}", SUCCESS_STYLE)
            else:
                err += 1
                emit("error", f"Failed {name}", ERROR_STYLE)

    if err == 0:
        emit("info", "Delete channels completed.", INFO_STYLE)
    else:
        emit("info", f"Completed with errors. OK: {ok} / ERR: {err}", INFO_STYLE)
