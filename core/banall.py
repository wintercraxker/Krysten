import time
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.text import Text

from .discord_client import DiscordClient

SUCCESS_STYLE = "bold white on #3498db"  
ERROR_STYLE = "bold white on #e53935"   
INFO_STYLE = "bold white on #3498db"     


def _print(console: Console, msg: str, style: str = INFO_STYLE):
    console.print(Text(msg, style=style))


def ban_all(console: Console, client: DiscordClient, guild_id: str, delete_message_seconds: int = 0, reason: str = "", log_sink=None):
    def _emit(kind: str, msg: str, style: str = INFO_STYLE):
        if callable(log_sink):
            try:
                log_sink(kind, msg)
                return
            except Exception:
                pass
        _print(console, msg, style=style)

    members: List[dict] = []
    after: Optional[str] = None
    _emit("info", "Starting ban all...", style=INFO_STYLE)
    while True:
        page = client.list_members(guild_id, limit=1000, after=after)
        if not page:
            break
        members.extend(page)
        if len(page) < 1000:
            break
        after = str(page[-1].get("user", {}).get("id"))
        time.sleep(0.2)

    if not members:
        _emit("error", "No members fetched or insufficient permissions.", style=ERROR_STYLE)
        return

    me = client.get_me()
    my_id = me.get("id") if me else None

    to_ban = [m for m in members if str(m.get("user", {}).get("id")) != str(my_id)]
    total = len(to_ban)
    _emit("info", f"Members to ban: {total}", style=INFO_STYLE)

    ok_count = 0
    err_count = 0

    def worker(member: dict) -> bool:
        uid = str(member.get("user", {}).get("id"))
        return client.ban_member(guild_id, uid, delete_message_seconds, reason)

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(worker, m): m for m in to_ban}
        for fut in as_completed(futures):
            member = futures[fut]
            user = member.get("user", {})
            tag = f"{user.get('username')}#{user.get('discriminator')}"
            try:
                ok = fut.result()
                if ok:
                    ok_count += 1
                    _emit("success", f"Banned {tag}", style=SUCCESS_STYLE)
                else:
                    err_count += 1
                    _emit("error", f"Failed {tag}", style=ERROR_STYLE)
            except Exception:
                err_count += 1
                _emit("error", f"Error banning {tag}", style=ERROR_STYLE)

    if err_count == 0:
        _emit("info", "Ban all completed.", style=INFO_STYLE)
    else:
        _emit("info", f"Completed with errors. OK: {ok_count} / ERR: {err_count}", style=INFO_STYLE)
