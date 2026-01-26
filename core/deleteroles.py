import time
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.text import Text

from .discord_client import DiscordClient

INFO_STYLE = "bold white on #3498db"
SUCCESS_STYLE = "bold white on #3498db"
ERROR_STYLE = "bold white on #e53935"


def delete_roles(console: Console, client: DiscordClient, guild_id: str, reason: str = "panel-delete-roles", log_sink=None):
    def emit(kind: str, msg: str, style: str):
        if callable(log_sink):
            try:
                log_sink(kind, msg)
                return
            except Exception:
                pass
        console.print(Text(msg, style=style))

    roles: List[dict] = client.get_roles(guild_id)
    if not roles:
        emit("error", "No roles fetched or insufficient permissions.", ERROR_STYLE)
        return

    me = client.get_me()
    if not me:
        emit("error", "Bot not connected.", ERROR_STYLE)
        return
    member = client.get_member(guild_id, me.get("id"))
    if not member:
        emit("error", "Bot is not in the guild.", ERROR_STYLE)
        return

    pos_by_id = {str(r.get("id")): int(r.get("position", 0)) for r in roles}
    name_by_id = {str(r.get("id")): r.get("name") for r in roles}

    highest_pos = 0
    for rid in member.get("roles", []):
        highest_pos = max(highest_pos, pos_by_id.get(str(rid), 0))

    deletable = []
    for r in roles:
        rid = str(r.get("id"))
        if rid == str(guild_id):
            continue
        if bool(r.get("managed")):
            continue
        pos = int(r.get("position", 0))
        if pos < highest_pos:
            deletable.append(r)
    total = len(deletable)

    emit("info", "Starting to delete all roles...", INFO_STYLE)
    emit("info", f"Roles to delete: {total}", INFO_STYLE)

    ok = 0
    err = 0

    def worker(role: dict) -> tuple[str, bool]:
        rid = str(role.get("id"))
        name = role.get("name")
        done = client.delete_role(guild_id, rid, reason=reason)
        return (name, done)

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(worker, r): r for r in sorted(deletable, key=lambda x: int(x.get("position", 0)), reverse=True)}
        for fut in as_completed(futures):
            name, done = fut.result()
            if done:
                ok += 1
                emit("success", f"Deleted {name}", SUCCESS_STYLE)
            else:
                err += 1
                emit("error", f"Failed {name}", ERROR_STYLE)

    if err == 0:
        emit("info", "Delete roles completed.", INFO_STYLE)
    else:
        emit("info", f"Completed with errors. OK: {ok} / ERR: {err}", INFO_STYLE)
