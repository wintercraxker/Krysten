import time
import os
import sys
from rich.console import Console, Group
from rich.table import Table
from rich.align import Align
from rich.live import Live
from rich.columns import Columns
from rich.text import Text as RText

from .styles import glow_text
from .components import logo_block
from core.config import load_token, load_clean_config, write_default_clean_config, save_clean_config
from core.discord_client import DiscordClient
from core.prompt import build_prompt
from core.utils import snowflake_to_iso


def _line(num: str, name: str) -> RText:
    t = RText()
    t.append(num.rjust(2), style="bold #ff4a4a")
    t.append("  |  ", style="#a0a0a0")
    t.append(name, style="bold white")
    return t

def _guild_line(gid: str, name: str) -> RText:
    t = RText()
    t.append(str(gid), style="bold #ff4a4a")
    t.append("  |  ", style="#a0a0a0")
    t.append(name or "", style="bold white")
    return t

def _guild_pick_line(idx: int, gid: str, name: str) -> RText:
    t = RText()
    t.append(str(idx).rjust(2), style="bold #ff4a4a")
    t.append("  |  ", style="#a0a0a0")
    t.append((name or ""), style="bold white")
    t.append("  ", style="#000000")
    t.append(f"({gid})", style="#bfbfbf")
    return t


def _column(items):
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column(justify="left")
    for n, name in items:
        table.add_row(_line(n, name))
    return table

def _items_row(items):
    cells = [_line(n, name) for n, name in items]
    return Columns(cells, equal=True, expand=False, padding=(0, 6))


def show_command_panel(console: Console):
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass
    console.clear()
    token = load_token()
    if not token:
        console.print(glow_text("No token found. Use >> to enter it.", strength=1.2))
        return

    client = DiscordClient(token)
    me = client.get_me()
    name = me.get("username") if me else "Bot"

    left = [
        ("01", "Ban All"),
        ("02", "Check Guilds"),
        ("03", "Delete All Roles"),
        ("04", "Delete All Channels"),
        ("05", "Delete All Emojis"),
    ]
    middle = [
        ("06", "Clean Guild"),
        ("07", "Mass DMs (soon)"),
        ("08", "Forum Spam (soon)"),
        ("09", "Data Check (soon)"),
        ("10", "Grabber (soon)"),
    ]
    right = [
        ("11", "???"),
        ("12", "???"),
        ("13", "???"),
        ("14", "???"),
        ("00", "Exit"),
    ]

    def render_panel(phase: float):
        ascii_logo = Align.center(logo_block())
        grid = Columns([_column(left), _column(middle), _column(right)], equal=False, expand=False, padding=(0, 6))
        connected = client.is_connected()
        status_style = "bold white on #2ecc71" if connected else "bold white on #e53935"
        status_line = RText(f"Logged in as {name} — " + ("Connected" if connected else "Disconnected"), style=status_style)
        return Group(ascii_logo, RText(), Align.center(status_line), RText(), Align.center(grid))

    is_windows = sys.platform == "win32"
    sleep_idle = 0.02
    hb_interval = 0.2
    cursor_interval = 0.5
    _cursor_on = True
    _last_cursor_toggle = time.time()

    with Live(console=console, refresh_per_second=12, transient=False) as live:
        start = time.time()
        panel_static = render_panel(0.0)
        while True:
            phase = ((time.time() - start) * 0.4) % 1.0
            if is_windows:
                import msvcrt
                typed = ""
                prompt_label = build_prompt()
                pad = max(0, (console.size.width // 2) - 50) + 8

                def render_input():
                    line = RText(" " * pad)
                    line.append(glow_text(prompt_label, strength=1.2))  
                    if typed:
                        line.append(RText(typed, style="bold white"))
                    line.append(RText("|", style="white"))
                    live.update(Group(panel_static, RText(), Align.left(line)))

                render_input()
                while True:
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        if ch in ("\r", "\n"):
                            choice = typed.strip()
                            break
                        elif ch in ("\b", "\x08"):
                            if typed:
                                typed = typed[:-1]
                            render_input()
                        else:
                            typed += ch
                            render_input()
                    else:
                        time.sleep(0.03)
            else:
                live.update(render_panel(phase))
                prompt_text = build_prompt()
                prompt_disp = glow_text(prompt_text, strength=1.3)
                choice = console.input(Align.center(prompt_disp)).strip()

            if choice == "00":
                try:
                    os.system('cls' if os.name == 'nt' else 'clear')
                except Exception:
                    pass
                console.clear()
                break
            elif choice == "01":
                from core.banall import ban_all
                guilds = client.list_guilds()
                if not guilds:
                    console.print(glow_text("No guilds or insufficient permissions.", strength=1.1))
                else:
                    if is_windows:
                        import msvcrt
                        typed = ""

                        def pick_table():
                            tbl = Table(show_header=False, box=None, pad_edge=False)
                            tbl.add_column(justify="left")
                            for i, g in enumerate(guilds, start=1):
                                tbl.add_row(_guild_pick_line(i, g.get("id"), g.get("name")))
                            return tbl

                        ascii_static = Align.center(logo_block())
                        tbl_static = pick_table()
                        prompt_cached = glow_text(build_prompt(), strength=1.2)
                        pad_left = max(0, (console.size.width // 2) - 43) + 8

                        hb_interval = 0.2
                        sleep_idle = 0.02
                        cursor_interval = 0.5
                        _cursor_on = True
                        _last_cursor_toggle = time.time()

                        def render_pick_view(msg: RText | None = None, show_cursor: bool = True):
                            instruction = RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a")
                            input_line = RText(" " * pad_left)
                            input_line.append(prompt_cached)
                            if typed:
                                input_line.append(RText(typed, style="bold white"))
                            if show_cursor:
                                input_line.append(RText("|", style="white"))
                            parts = [ascii_static, RText(), Align.left(instruction), RText(), Align.left(tbl_static)]
                            if msg is not None:
                                parts += [RText(), Align.left(msg)]
                            parts += [RText(), Align.left(input_line)]
                            return Group(*parts)

                        _pending_msg: RText | None = None
                        _dirty = True
                        _last_render = time.time()

                        def draw(msg: RText | None = None):
                            nonlocal _pending_msg, _dirty
                            _pending_msg = msg
                            _dirty = True

                        draw()
                        while True:
                            if msvcrt.kbhit():
                                enter = False
                                while msvcrt.kbhit():
                                    ch = msvcrt.getwch()
                                    if ch in ("\r", "\n"):
                                        enter = True
                                    elif ch in ("\b", "\x08"):
                                        if typed:
                                            typed = typed[:-1]
                                        draw()
                                    else:
                                        typed += ch
                                        draw()
                                if enter:
                                    sel = typed.strip()
                                    typed = ""
                                    if sel.lower() == "back":
                                        break
                                    if not sel.isdigit():
                                        draw(RText("Invalid selection.", style="bold white on #e53935"))
                                        continue
                                    idx = int(sel)
                                    if idx < 1 or idx > len(guilds):
                                        draw(RText("Out of range.", style="bold white on #e53935"))
                                        continue
                                    g = guilds[idx - 1]
                                    gid = str(g.get("id"))

                                    confirm_typed = ""
                                    logs: list[RText] = []

                                    def render_confirm_view():
                                        instruction = RText(f"Confirm ban all for '{g.get('name')}'? (Y/N)", style="bold #ff4a4a")
                                        input_line = RText(" " * pad_left)
                                        input_line.append(glow_text("Confirm (Y/N): ", strength=1.1))
                                        if confirm_typed:
                                            input_line.append(RText(confirm_typed, style="bold white"))
                                        input_line.append(RText("|", style="white"))
                                        parts = [ascii_static, RText(), Align.center(instruction), RText(), Align.left(input_line)]
                                        if logs:
                                            log_table = Table(show_header=False, box=None, pad_edge=False)
                                            log_table.add_column(justify="left")
                                            for ln in logs[-20:]:
                                                log_table.add_row(ln)
                                            parts += [RText(), Align.center(log_table)]
                                        return Group(*parts)

                                    live.update(render_confirm_view())
                                    while True:
                                        if msvcrt.kbhit():
                                            enter2 = False
                                            while msvcrt.kbhit():
                                                ch2 = msvcrt.getwch()
                                                if ch2 in ("\r", "\n"):
                                                    enter2 = True
                                                elif ch2 in ("\b", "\x08"):
                                                    if confirm_typed:
                                                        confirm_typed = confirm_typed[:-1]
                                                    live.update(render_confirm_view())
                                                else:
                                                    confirm_typed += ch2
                                                    live.update(render_confirm_view())
                                            if enter2:
                                                resp = confirm_typed.strip().lower()
                                                confirm_typed = ""
                                                if resp.startswith("y"):
                                                    from threading import Thread
                                                    from queue import Queue
                                                    from ui.styles import format_log

                                                    logq: Queue[RText] = Queue()

                                                    def sink(kind: str, message: str):
                                                        logq.put(format_log(kind, message))

                                                    def runner():
                                                        ban_all(console, client, gid, delete_message_seconds=0, reason="panel-banall", log_sink=sink)

                                                    t = Thread(target=runner, daemon=True)
                                                    t.start()

                                                    last_heartbeat = time.time()
                                                    while t.is_alive():
                                                        updated = False
                                                        while not logq.empty():
                                                            logs.append(logq.get_nowait())
                                                            updated = True
                                                        now = time.time()
                                                        if updated or (now - last_heartbeat) > 0.2:
                                                            live.update(render_confirm_view())
                                                            last_heartbeat = now
                                                        time.sleep(0.01)

                                                    while not logq.empty():
                                                        logs.append(logq.get_nowait())
                                                    logs.append(format_log("finalized", "Press Enter to back..."))
                                                    live.update(render_confirm_view())
                                                    waiting = True
                                                    while waiting:
                                                        if msvcrt.kbhit():
                                                            ch3 = msvcrt.getwch()
                                                            if ch3 in ("\r", "\n"):
                                                                waiting = False
                                                        else:
                                                            time.sleep(0.01)
                                                    typed = ""
                                                    draw()
                                                    break
                                                elif resp.startswith("n") or resp == "":
                                                    draw(RText("Cancelled.", style="bold #ff4a4a"))
                                                    break
                                                else:
                                                    live.update(render_confirm_view())
                                                    time.sleep(0.05)
                                        else:
                                            time.sleep(0.01)
                                else:
                                    draw()
                            else:
                                time.sleep(0.001)
                    else:
                        console.print(RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a"))
                        for i, g in enumerate(guilds, start=1):
                            console.print(_guild_pick_line(i, g.get("id"), g.get("name")))
                        while True:
                            inp = console.input(glow_text(build_prompt(), strength=1.2)).strip()
                            if inp.lower() == "back":
                                break
                            if not inp.isdigit():
                                console.print(RText("Invalid selection.", style="bold white on #e53935"))
                                continue
                            idx = int(inp)
                            if idx < 1 or idx > len(guilds):
                                console.print(RText("Out of range.", style="bold white on #e53935"))
                                continue
                            g = guilds[idx - 1]
                            gid = str(g.get("id"))
                            confirm = console.input(glow_text(f"Confirm ban all for '{g.get('name')}'? (Y/N): ", strength=1.1)).strip().lower()
                            if confirm.startswith("y"):
                                from ui.styles import format_log

                                def sink(kind: str, message: str):
                                    console.print(format_log(kind, message))

                                ban_all(console, client, gid, delete_message_seconds=0, reason="panel-banall", log_sink=sink)
                                console.print(format_log("finalized", "Press Enter to back..."))
                                console.input("\n")
                                break
                            else:
                                console.print(glow_text("Cancelled.", strength=1.1))
            elif choice == "02":
                guilds = client.list_guilds()
                if not guilds:
                    console.print(glow_text("No guilds or insufficient permissions.", strength=1.1))
                else:
                    if is_windows:
                        import msvcrt
                        typed = ""
                        details = None

                        def guilds_table():
                            tbl = Table(show_header=False, box=None, pad_edge=False)
                            tbl.add_column(justify="left")
                            for g in guilds:
                                tbl.add_row(_guild_line(g.get("id"), g.get("name")))
                            return tbl

                        ascii_static = Align.center(logo_block())
                        guilds_tbl_static = guilds_table()
                        prompt_cached = glow_text(build_prompt(), strength=1.2)
                        pad_left = max(0, (console.size.width // 2) - 43) + 8

                        def render_check_view():
                            instruction = RText("Select a guild by ID (type 'back' to return):", style="bold #ff4a4a")
                            input_line = RText(" " * pad_left)
                            input_line.append(prompt_cached)
                            if typed:
                                input_line.append(RText(typed, style="bold white"))
                            input_line.append(RText("|", style="white"))
                            parts = [ascii_static, RText(), Align.center(instruction), RText(), Align.center(guilds_tbl_static)]
                            if details is not None:
                                parts += [RText(), Align.center(details)]
                            parts += [RText(), Align.left(input_line)]
                            return Group(*parts)

                        def draw():
                            live.update(render_check_view())

                        draw()
                        while True:
                            if msvcrt.kbhit():
                                enter = False
                                while msvcrt.kbhit():
                                    ch = msvcrt.getwch()
                                    if ch in ("\r", "\n"):
                                        enter = True
                                    elif ch in ("\b", "\x08"):
                                            if typed:
                                                typed = typed[:-1]
                                            draw()
                                    else:
                                            typed += ch
                                            draw()
                                if enter:
                                    sel = typed.strip()
                                    if sel.lower() == "back":
                                        break
                                    if sel:
                                        if not sel.isdigit():
                                            details = Align.center(RText("Invalid guild ID.", style="bold white on #e53935"))
                                            typed = ""
                                            draw()
                                            continue
                                        in_g = client.is_in_guild(sel)
                                        gdet = client.get_guild(sel, with_counts=True) if in_g else None
                                        has_ban = client.has_ban_permissions(sel) if in_g else False
                                        name_disp = (gdet.get('name') if gdet else "Unknown")
                                        owner_id = gdet.get('owner_id') if gdet else None
                                        owner = client.get_member(sel, owner_id) if (owner_id and in_g) else None
                                        owner_tag = None
                                        if owner and owner.get('user'):
                                            u = owner['user']
                                            owner_tag = f"{u.get('username')}#{u.get('discriminator')} ({owner_id})"
                                        created = snowflake_to_iso(int(sel))
                                        roles_count = len(client.get_roles(sel)) if in_g else 0
                                        members_count = gdet.get('approximate_member_count') if gdet else None

                                        def kv(label: str, value: str) -> RText:
                                            t = RText()
                                            t.append(label, style="bold #ff4a4a")
                                            t.append(" ")
                                            t.append((value or ""), style="bold white")
                                            return t

                                        rows = [
                                            kv("Guild Name:", name_disp),
                                            kv("Guild ID:", sel),
                                            kv("Owner:", owner_tag or (owner_id or "Unknown")),
                                            kv("Created:", created),
                                            kv("Members:", str(members_count) if members_count is not None else "Unknown"),
                                            kv("Roles:", str(roles_count)),
                                            kv("In guild:", "YES" if in_g else "NO"),
                                            kv("Ban permission:", "YES" if has_ban else "NO"),
                                        ]

                                        dtbl = Table(show_header=False, box=None, pad_edge=False)
                                        dtbl.add_column(justify="left")
                                        for r in rows:
                                            dtbl.add_row(r)
                                        details = Align.center(dtbl)
                                    typed = ""
                                    draw()
                                else:
                                    draw()
                            else:
                                time.sleep(0.001)
                    else:
                        console.print(RText("Select a guild by ID (type 'back' to return):", style="bold #ff4a4a"))
                        for g in guilds:
                            console.print(_guild_line(g.get('id'), g.get('name')))
                        while True:
                            gid_sel = console.input(glow_text(build_prompt(), strength=1.2)).strip()
                            if gid_sel.lower() == "back":
                                break
                            if not gid_sel:
                                continue
                            if not gid_sel.isdigit():
                                console.print(RText("Invalid guild ID.", style="bold white on #e53935"))
                                continue
                            in_g = client.is_in_guild(gid_sel)
                            gdet = client.get_guild(gid_sel, with_counts=True) if in_g else None
                            has_ban = client.has_ban_permissions(gid_sel) if in_g else False
                            name_disp = (gdet.get('name') if gdet else "Unknown")
                            owner_id = gdet.get('owner_id') if gdet else None
                            owner = client.get_member(gid_sel, owner_id) if (owner_id and in_g) else None
                            owner_tag = None
                            if owner and owner.get('user'):
                                u = owner['user']
                                owner_tag = f"{u.get('username')}#{u.get('discriminator')} ({owner_id})"
                            created = snowflake_to_iso(int(gid_sel))
                            roles_count = len(client.get_roles(gid_sel)) if in_g else 0
                            members_count = gdet.get('approximate_member_count') if gdet else None

                            def kv(label: str, value: str) -> RText:
                                t = RText()
                                t.append(label, style="bold #ff4a4a")
                                t.append(" ")
                                t.append(value or "", style="bold white")
                                return t

                            rows = [
                                kv("Guild Name:", name_disp),
                                kv("Guild ID:", gid_sel),
                                kv("Owner:", owner_tag or (owner_id or "Unknown")),
                                kv("Created:", created),
                                kv("Members:", str(members_count) if members_count is not None else "Unknown"),
                                kv("Roles:", str(roles_count)),
                                kv("In guild:", "YES" if in_g else "NO"),
                                kv("Ban permission:", "YES" if has_ban else "NO"),
                            ]

                            dtbl = Table(show_header=False, box=None, pad_edge=False)
                            dtbl.add_column(justify="left")
                            for r in rows:
                                dtbl.add_row(r)
                            console.print(Align.center(dtbl))
            elif choice == "03":
                from core.deleteroles import delete_roles
                guilds = client.list_guilds()
                if not guilds:
                    console.print(glow_text("No guilds or insufficient permissions.", strength=1.1))
                else:
                    if is_windows:
                        import msvcrt
                        typed = ""

                        def pick_table():
                            tbl = Table(show_header=False, box=None, pad_edge=False)
                            tbl.add_column(justify="left")
                            for i, g in enumerate(guilds, start=1):
                                tbl.add_row(_guild_pick_line(i, g.get("id"), g.get("name")))
                            return tbl

                        ascii_static = Align.center(logo_block())
                        tbl_static = pick_table()
                        prompt_cached = glow_text(build_prompt(), strength=1.2)
                        pad_left = max(0, (console.size.width // 2) - 43) + 8

                        def render_pick_view(msg: RText | None = None):
                            disclaimer = RText("Disclaimer: Only roles below the bot's highest role will be deleted.", style="bold #f1c40f")
                            instruction = RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a")
                            input_line = RText(" " * pad_left)
                            input_line.append(prompt_cached)
                            if typed:
                                input_line.append(RText(typed, style="bold white"))
                            input_line.append(RText("|", style="white"))
                            parts = [ascii_static, RText(), Align.center(disclaimer), RText(), Align.center(instruction), RText(), Align.center(tbl_static)]
                            if msg is not None:
                                parts += [RText(), Align.center(msg)]
                            parts += [RText(), Align.left(input_line)]
                            return Group(*parts)

                        def draw(msg: RText | None = None):
                            live.update(render_pick_view(msg))

                        draw()
                        while True:
                            if msvcrt.kbhit():
                                enter = False
                                while msvcrt.kbhit():
                                    ch = msvcrt.getwch()
                                    if ch in ("\r", "\n"):
                                        enter = True
                                    elif ch in ("\b", "\x08"):
                                        if typed:
                                            typed = typed[:-1]
                                        draw()
                                    else:
                                        typed += ch
                                        draw()
                                if enter:
                                    sel = typed.strip()
                                    typed = ""
                                    if sel.lower() == "back":
                                        break
                                    if not sel.isdigit():
                                        draw(RText("Invalid selection.", style="bold white on #e53935"))
                                        continue
                                    idx = int(sel)
                                    if idx < 1 or idx > len(guilds):
                                        draw(RText("Out of range.", style="bold white on #e53935"))
                                        continue
                                    g = guilds[idx - 1]
                                    gid = str(g.get("id"))

                                    confirm_typed = ""
                                    logs: list[RText] = []
                                    

                                    def render_confirm_view():
                                        disclaimer2 = RText("Disclaimer: Only roles below the bot's highest role will be deleted.", style="bold #f1c40f")
                                        instruction = RText(f"Confirm delete all roles for '{g.get('name')}'? (Y/N)", style="bold #ff4a4a")
                                        input_line = RText(" " * pad_left)
                                        input_line.append(glow_text("Confirm (Y/N): ", strength=1.1))
                                        if confirm_typed:
                                            input_line.append(RText(confirm_typed, style="bold white"))
                                        input_line.append(RText("|", style="white"))
                                        parts = [ascii_static, RText(), Align.center(disclaimer2), RText(), Align.center(instruction), RText(), Align.left(input_line)]
                                        if logs:
                                            log_table = Table(show_header=False, box=None, pad_edge=False)
                                            log_table.add_column(justify="left")
                                            for ln in logs[-20:]:
                                                log_table.add_row(ln)
                                            parts += [RText(), Align.center(log_table)]
                                        return Group(*parts)

                                    live.update(render_confirm_view())
                                    while True:
                                        if msvcrt.kbhit():
                                            enter2 = False
                                            while msvcrt.kbhit():
                                                ch2 = msvcrt.getwch()
                                                if ch2 in ("\r", "\n"):
                                                    enter2 = True
                                                elif ch2 in ("\b", "\x08"):
                                                    if confirm_typed:
                                                        confirm_typed = confirm_typed[:-1]
                                                    live.update(render_confirm_view())
                                                else:
                                                    confirm_typed += ch2
                                                    live.update(render_confirm_view())
                                            if enter2:
                                                resp = confirm_typed.strip().lower()
                                                confirm_typed = ""
                                                if resp.startswith("y"):
                                                    from threading import Thread
                                                    from ui.styles import format_log
                                                    from threading import Thread
                                                    from queue import Queue

                                                    logq: Queue[RText] = Queue()

                                                    def sink(kind: str, message: str):
                                                        logq.put(format_log(kind, message))

                                                    def runner():
                                                        delete_roles(console, client, gid, reason="panel-deleteroles", log_sink=sink)

                                                    t = Thread(target=runner, daemon=True)
                                                    t.start()

                                                    while t.is_alive():
                                                        updated = False
                                                        while not logq.empty():
                                                            logs.append(logq.get_nowait())
                                                            updated = True
                                                        if updated:
                                                            live.update(render_confirm_view())
                                                        time.sleep(0.03)

                                                    while not logq.empty():
                                                        logs.append(logq.get_nowait())
                                                    logs.append(format_log("finalized", "Press Enter to back..."))
                                                    live.update(render_confirm_view())
                                                    waiting = True
                                                    while waiting:
                                                        if msvcrt.kbhit():
                                                            ch3 = msvcrt.getwch()
                                                            if ch3 in ("\r", "\n"):
                                                                waiting = False
                                                        else:
                                                            time.sleep(0.01)
                                                    typed = ""
                                                    draw()
                                                    break
                                                elif resp.startswith("n") or resp == "":
                                                    draw(RText("Cancelled.", style="bold #ff4a4a"))
                                                    break
                                                else:
                                                    live.update(render_confirm_view())
                                                    time.sleep(0.05)
                                        else:
                                            time.sleep(0.002)
                                else:
                                    draw()
                            else:
                                time.sleep(0.001)
                    else:
                        console.print(RText("Disclaimer: Only roles below the bot's highest role will be deleted.", style="bold #f1c40f"))
                        console.print(RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a"))
                        for i, g in enumerate(guilds, start=1):
                            console.print(_guild_pick_line(i, g.get("id"), g.get("name")))
                        while True:
                            inp = console.input(glow_text(build_prompt(), strength=1.2)).strip()
                            if inp.lower() == "back":
                                break
                            if not inp.isdigit():
                                console.print(RText("Invalid selection.", style="bold white on #e53935"))
                                continue
                            idx = int(inp)
                            if idx < 1 or idx > len(guilds):
                                console.print(RText("Out of range.", style="bold white on #e53935"))
                                continue
                            g = guilds[idx - 1]
                            gid = str(g.get("id"))
                            confirm = console.input(glow_text(f"Confirm delete all roles for '{g.get('name')}'? (Y/N): ", strength=1.1)).strip().lower()
                            if confirm.startswith("y"):
                                from ui.styles import format_log

                                def sink(kind: str, message: str):
                                    console.print(format_log(kind, message))

                                delete_roles(console, client, gid, reason="panel-deleteroles", log_sink=sink)
                                console.print(format_log("finalized", "Press Enter to back..."))
                                console.input("\n")
                                break
                            else:
                                console.print(glow_text("Cancelled.", strength=1.1))
            elif choice == "04":
                from core.deletechannels import delete_channels
                guilds = client.list_guilds()
                if not guilds:
                    console.print(glow_text("No guilds or insufficient permissions.", strength=1.1))
                else:
                    if is_windows:
                        import msvcrt
                        typed = ""

                        def pick_table():
                            tbl = Table(show_header=False, box=None, pad_edge=False)
                            tbl.add_column(justify="left")
                            for i, g in enumerate(guilds, start=1):
                                tbl.add_row(_guild_pick_line(i, g.get("id"), g.get("name")))
                            return tbl

                        ascii_static = Align.center(logo_block())
                        tbl_static = pick_table()
                        prompt_cached = glow_text(build_prompt(), strength=1.2)
                        pad_left = max(0, (console.size.width // 2) - 45) + 8

                        def render_pick_view(msg: RText | None = None):
                            disclaimer = RText("Disclaimer: Only channels the bot can manage will be deleted.", style="bold #f1c40f")
                            instruction = RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a")
                            input_line = RText(" " * pad_left)
                            input_line.append(prompt_cached)
                            if typed:
                                input_line.append(RText(typed, style="bold white"))
                            input_line.append(RText("|", style="white"))
                            parts = [ascii_static, RText(), Align.center(disclaimer), RText(), Align.center(instruction), RText(), Align.center(tbl_static)]
                            if msg is not None:
                                parts += [RText(), Align.center(msg)]
                            parts += [RText(), Align.left(input_line)]
                            return Group(*parts)

                        def draw(msg: RText | None = None):
                            live.update(render_pick_view(msg))

                        draw()
                        while True:
                            if msvcrt.kbhit():
                                enter = False
                                while msvcrt.kbhit():
                                    ch = msvcrt.getwch()
                                    if ch in ("\r", "\n"):
                                        enter = True
                                    elif ch in ("\b", "\x08"):
                                        if typed:
                                            typed = typed[:-1]
                                        draw()
                                    else:
                                        typed += ch
                                        draw()
                                if enter:
                                    sel = typed.strip()
                                    typed = ""
                                    if sel.lower() == "back":
                                        break
                                    if not sel.isdigit():
                                        draw(RText("Invalid selection.", style="bold white on #e53935"))
                                        continue
                                    idx = int(sel)
                                    if idx < 1 or idx > len(guilds):
                                        draw(RText("Out of range.", style="bold white on #e53935"))
                                        continue
                                    g = guilds[idx - 1]
                                    gid = str(g.get("id"))

                                    confirm_typed = ""
                                    logs: list[RText] = []
                                    from threading import Thread
                                    from queue import Queue
                                    from ui.styles import format_log

                                    def render_confirm_view():
                                        disclaimer2 = RText("Disclaimer: Only channels the bot can manage will be deleted.", style="bold #f1c40f")
                                        instruction = RText(f"Confirm delete all channels for '{g.get('name')}'? (Y/N)", style="bold #ff4a4a")
                                        input_line = RText(" " * pad_left)
                                        input_line.append(glow_text("Confirm (Y/N): ", strength=1.1))
                                        if confirm_typed:
                                            input_line.append(RText(confirm_typed, style="bold white"))
                                        input_line.append(RText("|", style="white"))
                                        parts = [ascii_static, RText(), Align.center(disclaimer2), RText(), Align.center(instruction), RText(), Align.left(input_line)]
                                        if logs:
                                            log_table = Table(show_header=False, box=None, pad_edge=False)
                                            log_table.add_column(justify="left")
                                            for ln in logs[-20:]:
                                                log_table.add_row(ln)
                                            parts += [RText(), Align.center(log_table)]
                                        return Group(*parts)

                                    logq: Queue[RText] = Queue()

                                    while True:
                                        live.update(render_confirm_view())
                                        if msvcrt.kbhit():
                                            enter2 = False
                                            while msvcrt.kbhit():
                                                ch2 = msvcrt.getwch()
                                                if ch2 in ("\r", "\n"):
                                                    enter2 = True
                                                elif ch2 in ("\b", "\x08"):
                                                    if confirm_typed:
                                                        confirm_typed = confirm_typed[:-1]
                                                    live.update(render_confirm_view())
                                                else:
                                                    confirm_typed += ch2
                                                    live.update(render_confirm_view())
                                            if enter2:
                                                resp = confirm_typed.strip().lower()
                                                confirm_typed = ""
                                                if resp.startswith("y"):
                                                    def sink(kind: str, message: str):
                                                        logq.put(format_log(kind, message))

                                                    def runner():
                                                        delete_channels(console, client, gid, reason="panel-deletechannels", log_sink=sink)

                                                    t = Thread(target=runner, daemon=True)
                                                    t.start()

                                                    while t.is_alive():
                                                        updated = False
                                                        while not logq.empty():
                                                            logs.append(logq.get_nowait())
                                                            updated = True
                                                        if updated:
                                                            live.update(render_confirm_view())
                                                        time.sleep(0.01)
                                                    while not logq.empty():
                                                        logs.append(logq.get_nowait())
                                                    logs.append(format_log("finalized", "Press Enter to back..."))
                                                    live.update(render_confirm_view())
                                                    waiting = True
                                                    while waiting:
                                                        if msvcrt.kbhit():
                                                            ch3 = msvcrt.getwch()
                                                            if ch3 in ("\r", "\n"):
                                                                waiting = False
                                                        else:
                                                            time.sleep(0.01)
                                                    typed = ""
                                                    draw()
                                                    break
                                                elif resp.startswith("n") or resp == "":
                                                    draw(RText("Cancelled.", style="bold #ff4a4a"))
                                                    break
                                                else:
                                                    live.update(render_confirm_view())
                                                    time.sleep(0.05)
                                        else:
                                            time.sleep(0.002)
                                else:
                                    draw()
                            else:
                                time.sleep(0.001)
                    else:
                        console.print(RText("Disclaimer: Only channels the bot can manage will be deleted.", style="bold #f1c40f"))
                        console.print(RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a"))
                        for i, g in enumerate(guilds, start=1):
                            console.print(_guild_pick_line(i, g.get("id"), g.get("name")))
                        while True:
                            inp = console.input(glow_text(build_prompt(), strength=1.2)).strip()
                            if inp.lower() == "back":
                                break
                            if not inp.isdigit():
                                console.print(RText("Invalid selection.", style="bold white on #e53935"))
                                continue
                            idx = int(inp)
                            if idx < 1 or idx > len(guilds):
                                console.print(RText("Out of range.", style="bold white on #e53935"))
                                continue
                            g = guilds[idx - 1]
                            gid = str(g.get("id"))
                            confirm = console.input(glow_text(f"Confirm delete all channels for '{g.get('name')}'? (Y/N): ", strength=1.1)).strip().lower()
                            if confirm.startswith("y"):
                                from ui.styles import format_log
                                from queue import Queue
                                logq: Queue[RText] = Queue()

                                def sink(kind: str, message: str):
                                    logq.put(format_log(kind, message))

                                from threading import Thread
                                def runner():
                                    delete_channels(console, client, gid, reason="panel-deletechannels", log_sink=sink)

                                t = Thread(target=runner, daemon=True)
                                t.start()
                                while t.is_alive():
                                    while not logq.empty():
                                        console.print(logq.get_nowait())
                                    time.sleep(0.03)
                                while not logq.empty():
                                    console.print(logq.get_nowait())
                                console.print(format_log("finalized", "Press Enter to back..."))
                                console.input("\n")
                                break
                            else:
                                console.print(glow_text("Cancelled.", strength=1.1))
            elif choice == "05":
                from core.deleteemojis import delete_emojis
                guilds = client.list_guilds()
                if not guilds:
                    console.print(glow_text("No guilds or insufficient permissions.", strength=1.1))
                else:
                    if is_windows:
                        import msvcrt
                        typed = ""

                        def pick_table():
                            tbl = Table(show_header=False, box=None, pad_edge=False)
                            tbl.add_column(justify="left")
                            for i, g in enumerate(guilds, start=1):
                                tbl.add_row(_guild_pick_line(i, g.get("id"), g.get("name")))
                            return tbl

                        ascii_static = Align.center(logo_block())
                        tbl_static = pick_table()
                        prompt_cached = glow_text(build_prompt(), strength=1.2)
                        pad_left = max(0, (console.size.width // 2) - 45) + 8

                        def render_pick_view(msg: RText | None = None):
                            disclaimer = RText("Disclaimer: Only emojis the bot can manage will be deleted.", style="bold #f1c40f")
                            instruction = RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a")
                            input_line = RText(" " * pad_left)
                            input_line.append(prompt_cached)
                            if typed:
                                input_line.append(RText(typed, style="bold white"))
                            input_line.append(RText("|", style="white"))
                            parts = [ascii_static, RText(), Align.center(disclaimer), RText(), Align.center(instruction), RText(), Align.center(tbl_static)]
                            if msg is not None:
                                parts += [RText(), Align.center(msg)]
                            parts += [RText(), Align.left(input_line)]
                            return Group(*parts)

                        def draw(msg: RText | None = None):
                            live.update(render_pick_view(msg))

                        draw()
                        while True:
                            if msvcrt.kbhit():
                                enter = False
                                while msvcrt.kbhit():
                                    ch = msvcrt.getwch()
                                    if ch in ("\r", "\n"):
                                        enter = True
                                    elif ch in ("\b", "\x08"):
                                        if typed:
                                            typed = typed[:-1]
                                    else:
                                        typed += ch
                                if enter:
                                    sel = typed.strip()
                                    typed = ""
                                    if sel.lower() == "back":
                                        break
                                    if not sel.isdigit():
                                        draw(RText("Invalid selection.", style="bold white on #e53935"))
                                        continue
                                    idx = int(sel)
                                    if idx < 1 or idx > len(guilds):
                                        draw(RText("Out of range.", style="bold white on #e53935"))
                                        continue
                                    g = guilds[idx - 1]
                                    gid = str(g.get("id"))

                                    confirm_typed = ""
                                    logs: list[RText] = []
                                    from threading import Thread
                                    from queue import Queue
                                    from ui.styles import format_log

                                    def render_confirm_view():
                                        disclaimer2 = RText("Disclaimer: Only emojis the bot can manage will be deleted.", style="bold #f1c40f")
                                        instruction = RText(f"Confirm delete all emojis for '{g.get('name')}'? (Y/N)", style="bold #ff4a4a")
                                        input_line = RText(" " * pad_left)
                                        input_line.append(glow_text("Confirm (Y/N): ", strength=1.1))
                                        if confirm_typed:
                                            input_line.append(RText(confirm_typed, style="bold white"))
                                        input_line.append(RText("|", style="white"))
                                        parts = [ascii_static, RText(), Align.center(disclaimer2), RText(), Align.center(instruction), RText(), Align.left(input_line)]
                                        if logs:
                                            log_table = Table(show_header=False, box=None, pad_edge=False)
                                            log_table.add_column(justify="left")
                                            for ln in logs[-20:]:
                                                log_table.add_row(ln)
                                            parts += [RText(), Align.center(log_table)]
                                        return Group(*parts)

                                    logq: Queue[RText] = Queue()

                                    while True:
                                        live.update(render_confirm_view())
                                        if msvcrt.kbhit():
                                            enter2 = False
                                            while msvcrt.kbhit():
                                                ch2 = msvcrt.getwch()
                                                if ch2 in ("\r", "\n"):
                                                    enter2 = True
                                                elif ch2 in ("\b", "\x08"):
                                                    if confirm_typed:
                                                        confirm_typed = confirm_typed[:-1]
                                                    live.update(render_confirm_view())
                                                else:
                                                    confirm_typed += ch2
                                                    live.update(render_confirm_view())
                                            if enter2:
                                                resp = confirm_typed.strip().lower()
                                                confirm_typed = ""
                                                if resp.startswith("y"):
                                                    def sink(kind: str, message: str):
                                                        logq.put(format_log(kind, message))

                                                    def runner():
                                                        delete_emojis(console, client, gid, reason="panel-deleteemojis", log_sink=sink)

                                                    t = Thread(target=runner, daemon=True)
                                                    t.start()
                                                    while t.is_alive():
                                                        updated = False
                                                        while not logq.empty():
                                                            logs.append(logq.get_nowait())
                                                            updated = True
                                                        if updated:
                                                            live.update(render_confirm_view())
                                                        time.sleep(0.01)
                                                    while not logq.empty():
                                                        logs.append(logq.get_nowait())
                                                    logs.append(format_log("finalized", "Press Enter to back..."))
                                                    live.update(render_confirm_view())
                                                    waiting = True
                                                    while waiting:
                                                        if msvcrt.kbhit():
                                                            ch3 = msvcrt.getwch()
                                                            if ch3 in ("\r", "\n"):
                                                                waiting = False
                                                        else:
                                                            time.sleep(0.01)
                                                    typed = ""
                                                    draw()
                                                    break
                                                elif resp.startswith("n") or resp == "":
                                                    draw(RText("Cancelled.", style="bold #ff4a4a"))
                                                    break
                                                else:
                                                    live.update(render_confirm_view())
                                                    time.sleep(0.05)
                                        else:
                                            time.sleep(0.001)
                                else:
                                    draw()
                            else:
                                time.sleep(0.001)
                    else:
                        console.print(RText("Disclaimer: Only emojis the bot can manage will be deleted.", style="bold #f1c40f"))
                        console.print(RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a"))
                        for i, g in enumerate(guilds, start=1):
                            console.print(_guild_pick_line(i, g.get("id"), g.get("name")))
                        while True:
                            inp = console.input(glow_text(build_prompt(), strength=1.2)).strip()
                            if inp.lower() == "back":
                                break
                            if not inp.isdigit():
                                console.print(RText("Invalid selection.", style="bold white on #e53935"))
                                continue
                            idx = int(inp)
                            if idx < 1 or idx > len(guilds):
                                console.print(RText("Out of range.", style="bold white on #e53935"))
                                continue
                            g = guilds[idx - 1]
                            gid = str(g.get("id"))
                            confirm = console.input(glow_text(f"Confirm delete all emojis for '{g.get('name')}'? (Y/N): ", strength=1.1)).strip().lower()
                            if confirm.startswith("y"):
                                from ui.styles import format_log
                                from queue import Queue
                                logq: Queue[RText] = Queue()

                                def sink(kind: str, message: str):
                                    logq.put(format_log(kind, message))

                                from threading import Thread
                                def runner():
                                    delete_emojis(console, client, gid, reason="panel-deleteemojis", log_sink=sink)

                                t = Thread(target=runner, daemon=True)
                                t.start()
                                while t.is_alive():
                                    while not logq.empty():
                                        console.print(logq.get_nowait())
                                    time.sleep(0.01)
                                while not logq.empty():
                                    console.print(logq.get_nowait())
                                console.print(format_log("finalized", "Press Enter to back..."))
                                console.input("\n")
                                break
                            else:
                                console.print(glow_text("Cancelled.", strength=1.1))
            elif choice == "06":
                from core.clean_guild import clean_guild
                guilds = client.list_guilds()
                if not guilds:
                    console.print(glow_text("No guilds or insufficient permissions.", strength=1.1))
                else:
                    if is_windows:
                        import msvcrt
                        typed = ""

                        ascii_logo = Align.center(logo_block())
                        pad_left0 = max(0, (console.size.width // 2) - 32)
                        preset_typed = ""
                        _cfg0 = load_clean_config() or write_default_clean_config()
                        first_run = not bool(_cfg0.get("initialized"))
                        preset_choice = "m" if first_run else "y" 

                        def render_preset_choice():
                            instruction = RText("Modify template? (Y/N)", style="bold #ff4a4a")
                            line = RText(" " * pad_left0)
                            line.append(glow_text("Choice (Y/N): ", strength=1.1))
                            if preset_typed:
                                line.append(RText(preset_typed, style="bold white"))
                            line.append(RText("|", style="white"))
                            return Group(ascii_logo, RText(), Align.center(instruction), RText(), Align.left(line))

                        if not first_run:
                            live.update(render_preset_choice())
                            while True:
                                if msvcrt.kbhit():
                                    enter0 = False
                                    while msvcrt.kbhit():
                                        ch0 = msvcrt.getwch()
                                        if ch0 in ("\r", "\n"):
                                            enter0 = True
                                        elif ch0 in ("\b", "\x08"):
                                            if preset_typed:
                                                preset_typed = preset_typed[:-1]
                                            live.update(render_preset_choice())
                                        else:
                                            preset_typed += ch0
                                            live.update(render_preset_choice())
                                    if enter0:
                                        resp0 = (preset_typed or "").strip().lower()
                                        if resp0.startswith("y"):
                                            preset_choice = "m"
                                        else:
                                            preset_choice = "y"
                                        break
                                else:
                                    time.sleep(0.02)

                        cfg = None
                        if preset_choice == "m":
                            cfg = load_clean_config() or write_default_clean_config()
                            initial_content = str(cfg.get("content", "@everyone - discord invite") or "@everyone - discord invite")
                            embeds = cfg.get("embeds") or []
                            emb0 = embeds[0] if embeds and isinstance(embeds[0], dict) else {}
                            initial_desc = str(emb0.get("description", "") or "")
                            image = emb0.get("image") or {}
                            initial_img = str(image.get("url", "") or "")
                            footer = emb0.get("footer") if isinstance(emb0, dict) else None
                            initial_wh_name = str(cfg.get("webhook_name", "Krysten") or "Krysten")
                            initial_wh_icon = str(cfg.get("webhook_icon_spec", "https://cdn.discordapp.com/attachments/1307514165866532874/1465166630521671863/logo.png?ex=69781e42&is=6976ccc2&hm=dc7aad33e93bbbb24900fa3bfbe51f4c67d7825cd4f00fbcce44fb68b1bffe12") or "")

                            fields = [
                                ("Custom content (e.g. @everyone - discord invite):", "content", initial_content),
                                ("Cleaner name for bold (default krysten):", "cleaner_name", "krysten"),
                                ("Invite URL for [here](...):", "invite_url", ""),
                                ("Image URL (leave blank to keep):", "image_url", initial_img),
                                ("Webhook name:", "wh_name", initial_wh_name),
                                ("Webhook icon URL:", "wh_icon", initial_wh_icon),
                            ]
                            idxf = 0
                            typedf = ""

                            def render_edit_view():
                                parts = [ascii_logo, RText()]
                                prompt_lbl = RText(fields[idxf][0], style="bold #ff4a4a")
                                line = RText(" " * pad_left0)
                                line.append(glow_text("Input: ", strength=1.1))
                                if typedf:
                                    line.append(RText(typedf, style="bold white"))
                                line.append(RText("|", style="white"))
                                parts += [Align.center(prompt_lbl), Align.left(line)]
                                return Group(*parts)

                            live.update(render_edit_view())
                            answers_edit = {"content": initial_content, "cleaner_name": "krysten", "invite_url": "", "image_url": initial_img, "wh_name": initial_wh_name, "wh_icon": initial_wh_icon}
                            while idxf < len(fields):
                                if msvcrt.kbhit():
                                    chx = msvcrt.getwch()
                                    if chx in ("\r", "\n"):
                                        key = fields[idxf][1]
                                        val = typedf.strip()
                                        if val:
                                            answers_edit[key] = val
                                        typedf = ""
                                        idxf += 1
                                        if idxf < len(fields):
                                            live.update(render_edit_view())
                                        continue
                                    elif chx in ("\b", "\x08"):
                                        if typedf:
                                            typedf = typedf[:-1]
                                        live.update(render_edit_view())
                                    else:
                                        typedf += chx
                                        live.update(render_edit_view())
                                else:
                                    time.sleep(0.02)

                            new_desc = initial_desc
                            cleaner = (answers_edit.get("cleaner_name") or "krysten").strip()
                            if cleaner:
                                marker = "by **"
                                i1 = new_desc.find(marker)
                                if i1 != -1:
                                    i1 += len(marker)
                                    i2 = new_desc.find("**", i1)
                                    if i2 != -1:
                                        new_desc = new_desc[:i1] + cleaner + new_desc[i2:]
                            invite_url = answers_edit.get("invite_url", "").strip()
                            if invite_url:
                                start = new_desc.find("[here](")
                                if start != -1:
                                    start_paren = new_desc.find("(", start)
                                    end_paren = new_desc.find(")", start_paren)
                                    if start_paren != -1 and end_paren != -1 and end_paren > start_paren:
                                        new_desc = new_desc[: start_paren + 1] + invite_url + new_desc[end_paren:]
                            cfg = {
                                "content": answers_edit.get("content", initial_content),
                                "embeds": [
                                    {
                                        "description": new_desc,
                                        "color": emb0.get("color", 3225146),
                                        "footer": footer if isinstance(footer, dict) else emb0.get("footer"),
                                        "image": {"url": answers_edit.get("image_url", initial_img) or initial_img},
                                    }
                                ],
                                "webhook_name": answers_edit.get("wh_name", initial_wh_name),
                                "webhook_icon_spec": answers_edit.get("wh_icon", initial_wh_icon),
                            }
                            cfg["initialized"] = True
                            save_clean_config(cfg)
                            preset_choice = "y"  

                        def pick_table():
                            tbl = Table(show_header=False, box=None, pad_edge=False)
                            tbl.add_column(justify="left")
                            for i, g in enumerate(guilds, start=1):
                                tbl.add_row(_guild_pick_line(i, g.get("id"), g.get("name")))
                            return tbl

                        ascii_static = Align.center(logo_block())
                        tbl_static = pick_table()
                        prompt_cached = glow_text(build_prompt(), strength=1.2)
                        pad_left = max(0, (console.size.width // 2) - 45) + 8

                        def render_pick_view(msg: RText | None = None, show_cursor: bool = True):
                            instruction = RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a")
                            input_line = RText(" " * pad_left)
                            input_line.append(prompt_cached)
                            if typed:
                                input_line.append(RText(typed, style="bold white"))
                            if show_cursor:
                                input_line.append(RText("|", style="white"))
                            parts = [ascii_static, RText(), Align.center(instruction), RText(), Align.center(tbl_static)]
                            if msg is not None:
                                parts += [RText(), Align.center(msg)]
                            parts += [RText(), Align.left(input_line)]
                            return Group(*parts)

                        _pending_msg: RText | None = None
                        _dirty = True
                        _last_render = time.time()
                        _cursor_on = True
                        _last_cursor_toggle = time.time()

                        def draw(msg: RText | None = None):
                            nonlocal _pending_msg, _dirty
                            _pending_msg = msg
                            _dirty = True

                        live.update(render_pick_view(None, _cursor_on))
                        while True:
                            if msvcrt.kbhit():
                                enter = False
                                while msvcrt.kbhit():
                                    ch = msvcrt.getwch()
                                    if ch in ("\r", "\n"):
                                        enter = True
                                    elif ch in ("\b", "\x08"):
                                        if typed:
                                            typed = typed[:-1]
                                        draw()
                                    else:
                                        typed += ch
                                        draw()
                                if enter:
                                    sel = typed.strip()
                                    typed = ""
                                    if sel.lower() == "back":
                                        break
                                    if not sel.isdigit():
                                        draw(RText("Invalid selection.", style="bold white on #e53935"))
                                        continue
                                    idx = int(sel)
                                    if idx < 1 or idx > len(guilds):
                                        draw(RText("Out of range.", style="bold white on #e53935"))
                                        continue
                                    g = guilds[idx - 1]
                                    gid = str(g.get("id"))

                                    answers = {
                                        "icon": "",
                                        "name": "",
                                        "ch_count": "5",
                                        "base": "general",
                                        "mode": "none",
                                        "emb_reps": "1",
                                        "msg_reps": "1",
                                        "del_emojis": "n",
                                    }
                                    steps = [
                                        ("Icon Server URL/emoji/file (or 'skip'/'remove'):", "icon"),
                                        ("New server name (or 'skip'):", "name"),
                                        ("Channels to create (max 50, default 5):", "ch_count"),
                                        ("Base channel name:", "base"),
                                        ("Announcement mode [none/webhook/message/both]:", "mode"),
                                        ("Embed repeats per channel [1-100, default 1]:", "emb_reps"),
                                        ("Text repeats per channel [1-100, default 1]:", "msg_reps"),
                                        ("Delete emojis after? (Y/N):", "del_emojis"),
                                    ]
                                    step_i = 0
                                    typed2 = ""

                                    _dirty2 = True
                                    _last_render2 = time.time()
                                    _cursor_on2 = True
                                    _last_cursor_toggle2 = time.time()

                                    def render_inputs_view(show_cursor: bool = True):
                                        prompt_lbl, key = steps[step_i]
                                        parts = [ascii_static, RText()]
                                        instruction = RText(prompt_lbl, style="bold #ff4a4a")
                                        line = RText(" " * pad_left)
                                        line.append(glow_text("Input: ", strength=1.1))
                                        if typed2:
                                            line.append(RText(typed2, style="bold white"))
                                        if show_cursor:
                                            line.append(RText("|", style="white"))
                                        parts += [Align.center(instruction), Align.left(line)]
                                        return Group(*parts)

                                    live.update(render_inputs_view(_cursor_on2))
                                    while step_i < len(steps):
                                        cur_key = steps[step_i][1]
                                        mode_val = (answers.get("mode") or "").lower()
                                        if cur_key in ("wb_name", "wb_icon") and mode_val not in ("webhook", "both"):
                                            if cur_key == "wb_name":
                                                answers["wb_name"] = answers.get("wb_name") or "Krysten"
                                            else:
                                                answers["wb_icon"] = answers.get("wb_icon") or "https://cdn.discordapp.com/attachments/1307514165866532874/1465166630521671863/logo.png?ex=69781e42&is=6976ccc2&hm=dc7aad33e93bbbb24900fa3bfbe51f4c67d7825cd4f00fbcce44fb68b1bffe12"
                                            step_i += 1
                                            _dirty2 = True
                                            continue
                                        if cur_key in ("emb_title", "emb_desc", "emb_reps") and mode_val not in ("webhook", "both"):
                                            answers[cur_key] = answers.get(cur_key, "")
                                            step_i += 1
                                            _dirty2 = True
                                            continue
                                        if cur_key in ("msg_text", "msg_reps") and mode_val == "none":
                                            answers[cur_key] = answers.get(cur_key, "")
                                            step_i += 1
                                            _dirty2 = True
                                            continue
                                        if msvcrt.kbhit():
                                            ch2 = msvcrt.getwch()
                                            if ch2 in ("\r", "\n"):
                                                answers[steps[step_i][1]] = typed2.strip()
                                                typed2 = ""
                                                step_i += 1
                                                if step_i < len(steps):
                                                    _dirty2 = True
                                                continue
                                            elif ch2 in ("\b", "\x08"):
                                                if typed2:
                                                    typed2 = typed2[:-1]
                                                _dirty2 = True
                                            else:
                                                typed2 += ch2
                                                _dirty2 = True
                                        else:
                                            time.sleep(sleep_idle)
                                        now2 = time.time()
                                        if _dirty2 or (now2 - _last_render2) >= hb_interval:
                                            live.update(render_inputs_view(True))
                                            _dirty2 = False
                                            _last_render2 = now2

                                    logs: list[RText] = []
                                    confirm_typed = ""

                                    _dirty3 = True
                                    _last_render3 = time.time()
                                    _cursor_on3 = True
                                    _last_cursor_toggle3 = time.time()

                                    def render_confirm_view(show_cursor: bool = True):
                                        instruction = RText(f"Proceed clean on '{g.get('name')}'? (Y/N)", style="bold #ff4a4a")
                                        input_line = RText(" " * pad_left)
                                        input_line.append(glow_text("Confirm (Y/N): ", strength=1.1))
                                        if confirm_typed:
                                            input_line.append(RText(confirm_typed, style="bold white"))
                                        if show_cursor:
                                            input_line.append(RText("|", style="white"))
                                        parts = [ascii_static, RText(), Align.center(instruction), RText(), Align.left(input_line)]
                                        return Group(*parts)

                                    def render_logs_view(show_back: bool = False):
                                        parts = []
                                        if logs:
                                            log_table = Table(show_header=False, box=None, pad_edge=False)
                                            log_table.add_column(justify="left")
                                            for ln in logs[-20:]:
                                                log_table.add_row(ln)
                                            parts += [Align.left(log_table)]
                                        if show_back:
                                            from ui.styles import format_log
                                            parts += [RText(), Align.left(format_log("finalized", "Press Enter to back..."))]
                                        return Group(*parts)
                                    live.update(render_confirm_view(_cursor_on3))
                                    while True:
                                        if msvcrt.kbhit():
                                            enter3 = False
                                            while msvcrt.kbhit():
                                                ch3 = msvcrt.getwch()
                                                if ch3 in ("\r", "\n"):
                                                    enter3 = True
                                                elif ch3 in ("\b", "\x08"):
                                                    if confirm_typed:
                                                        confirm_typed = confirm_typed[:-1]
                                                    _dirty3 = True
                                                else:
                                                    confirm_typed += ch3
                                                    _dirty3 = True
                                            if enter3:
                                                resp = confirm_typed.strip().lower()
                                                confirm_typed = ""
                                                if not resp or resp.startswith("n"):
                                                    draw(RText("Cancelled.", style="bold #ff4a4a"))
                                                    break
                                                if resp.startswith("y"):
                                                    from threading import Thread
                                                    from queue import Queue
                                                    from ui.styles import format_log
                                                    logq: Queue[RText] = Queue()

                                                    def sink(kind: str, message: str):
                                                        logq.put(format_log(kind, message))

                                                    def parse_int(val: str, dv: int) -> int:
                                                        try:
                                                            return int(val)
                                                        except Exception:
                                                            return dv

                                                    def runner():
                                                        cfg_run = load_clean_config() or write_default_clean_config()
                                                        emb_run = (cfg_run.get("embeds") or [{}])[0] if isinstance(cfg_run.get("embeds"), list) else {}
                                                        img_url = ((emb_run.get("image") or {}).get("url") or "") if isinstance(emb_run, dict) else ""
                                                        ftr = emb_run.get("footer") if isinstance(emb_run, dict) else None
                                                        ftr_text = (ftr.get("text") if isinstance(ftr, dict) else None) or None
                                                        ftr_icon = (ftr.get("icon_url") if isinstance(ftr, dict) else None) or None
                                                        clean_guild(
                                                            console,
                                                            client,
                                                            gid,
                                                            desired_name=answers.get("name"),
                                                            desired_icon_spec=answers.get("icon"),
                                                            channel_count=parse_int(answers.get("ch_count") or "5", 5),
                                                            channel_base_name=answers.get("base") or "general",
                                                            announce_mode=(answers.get("mode") or "none").lower(),
                                                            embed_title=None,
                                                            embed_description=str(emb_run.get("description", "") if isinstance(emb_run, dict) else ""),
                                                            embed_image_url=img_url,
                                                            embed_footer_text=ftr_text,
                                                            embed_footer_icon_url=ftr_icon,
                                                            message_text=str(cfg_run.get("content", "") or ""),
                                                            embed_repeats=max(1, min(parse_int(answers.get("emb_reps") or "1", 1), 100)),
                                                            message_repeats=max(1, min(parse_int(answers.get("msg_reps") or "1", 1), 100)),
                                                            webhook_name=str(cfg_run.get("webhook_name", "Krysten") or "Krysten"),
                                                            webhook_icon_spec=str(cfg_run.get("webhook_icon_spec", "") or ""),
                                                            delete_emojis_after=(answers.get("del_emojis") or "n").lower().startswith("y"),
                                                            log_sink=sink,
                                                        )

                                                    t = Thread(target=runner, daemon=True)
                                                    t.start()

                                                    while t.is_alive():
                                                        updated = False
                                                        while not logq.empty():
                                                            logs.append(logq.get_nowait())
                                                            updated = True
                                                        if updated:
                                                            live.update(render_logs_view(False))
                                                        time.sleep(0.01)
                                                    while not logq.empty():
                                                        logs.append(logq.get_nowait())
                                                    live.update(render_logs_view(True))
                                                    waiting = True
                                                    while waiting:
                                                        if msvcrt.kbhit():
                                                            ch4 = msvcrt.getwch()
                                                            if ch4 in ("\r", "\n"):
                                                                waiting = False
                                                        else:
                                                            time.sleep(sleep_idle)
                                                    typed = ""
                                                    draw()
                                                    break
                                        else:
                                            time.sleep(sleep_idle)
                                        now3 = time.time()
                                        if _dirty3 or (now3 - _last_render3) >= hb_interval:
                                            live.update(render_confirm_view(True))
                                            _dirty3 = False
                                            _last_render3 = now3
                                else:
                                    draw()
                            else:
                                time.sleep(sleep_idle)

                            now = time.time()
                            if _dirty or (now - _last_render) >= hb_interval:
                                live.update(render_pick_view(_pending_msg, True))
                                _dirty = False
                                _last_render = now
                    else:
                        pc = console.input(glow_text("Use saved config? (Y/M/N): ", strength=1.1)).strip().lower()
                        preset_choice = "y" if pc.startswith("y") else ("m" if pc.startswith("m") else "n")
                        cfg = None
                        if preset_choice == "m":
                            cfg = load_clean_config() or write_default_clean_config()
                            emb = (cfg.get("embeds") or [{}])[0] if isinstance(cfg.get("embeds"), list) else {}
                            cur_content = cfg.get("content") or "@everyone - discord invite"
                            cur_desc = emb.get("description") or ""
                            cur_img = (emb.get("image") or {}).get("url") or ""
                            cur_footer = emb.get("footer") if isinstance(emb, dict) else None
                            cur_wh_name = cfg.get("webhook_name") or "Krysten"
                            cur_wh_icon = cfg.get("webhook_icon_spec") or "https://cdn.discordapp.com/attachments/1307514165866532874/1465166630521671863/logo.png?ex=69781e42&is=6976ccc2&hm=dc7aad33e93bbbb24900fa3bfbe51f4c67d7825cd4f00fbcce44fb68b1bffe12"
                            new_content = console.input(glow_text(f"Content [{cur_content}]: ", strength=1.1)).strip() or cur_content
                            cleaner = console.input(glow_text("Cleaner name for bold [krysten]: ", strength=1.1)).strip() or "krysten"
                            invite = console.input(glow_text("Invite URL for [here](...): ", strength=1.1)).strip()
                            new_desc = cur_desc
                            if cleaner:
                                marker = "by **"
                                i1 = new_desc.find(marker)
                                if i1 != -1:
                                    i1 += len(marker)
                                    i2 = new_desc.find("**", i1)
                                    if i2 != -1:
                                        new_desc = new_desc[:i1] + cleaner + new_desc[i2:]
                            if invite:
                                s = new_desc.find("[here](")
                                if s != -1:
                                    sp = new_desc.find("(", s)
                                    ep = new_desc.find(")", sp)
                                    if sp != -1 and ep != -1 and ep > sp:
                                        new_desc = new_desc[: sp + 1] + invite + new_desc[ep:]
                            new_img = console.input(glow_text(f"Image URL [{cur_img}]: ", strength=1.1)).strip() or cur_img
                            new_wh_name = console.input(glow_text(f"Webhook name [{cur_wh_name}]: ", strength=1.1)).strip() or cur_wh_name
                            new_wh_icon = console.input(glow_text(f"Webhook icon URL [{cur_wh_icon}]: ", strength=1.1)).strip() or cur_wh_icon
                            cfg = {
                                "content": new_content,
                                "embeds": [{"description": new_desc, "color": emb.get("color", 3225146), "footer": cur_footer if isinstance(cur_footer, dict) else emb.get("footer"), "image": {"url": new_img}}],
                                "webhook_name": new_wh_name,
                                "webhook_icon_spec": new_wh_icon,
                            }
                            save_clean_config(cfg)
                            preset_choice = "y"

                        console.print(RText("Select a guild by number (type 'back' to return):", style="bold #ff4a4a"))
                        for i, g in enumerate(guilds, start=1):
                            console.print(_guild_pick_line(i, g.get("id"), g.get("name")))
                        while True:
                            inp = console.input(glow_text(build_prompt(), strength=1.2)).strip()
                            if inp.lower() == "back":
                                break
                            if not inp.isdigit():
                                console.print(RText("Invalid selection.", style="bold white on #e53935"))
                                continue
                            idx = int(inp)
                            if idx < 1 or idx > len(guilds):
                                console.print(RText("Out of range.", style="bold white on #e53935"))
                                continue
                            g = guilds[idx - 1]
                            gid = str(g.get("id"))
                            if preset_choice == "y":
                                cfg = cfg or load_clean_config() or write_default_clean_config()
                                confirm = console.input(glow_text(f"Proceed clean on '{g.get('name')}' with saved config? (Y/N): ", strength=1.1)).strip().lower()
                                if not confirm.startswith("y"):
                                    console.print(glow_text("Cancelled.", strength=1.1))
                                    break
                                from ui.styles import format_log
                                from queue import Queue
                                logq: Queue[RText] = Queue()
                                def sink(kind: str, message: str):
                                    logq.put(format_log(kind, message))
                                from threading import Thread
                                def runner():
                                    emb = (cfg.get("embeds") or [{}])[0]
                                    img_url = ((emb.get("image") or {}).get("url") or "") if isinstance(emb, dict) else ""
                                    ftr = emb.get("footer") if isinstance(emb, dict) else None
                                    ftr_text = (ftr.get("text") if isinstance(ftr, dict) else None) or None
                                    ftr_icon = (ftr.get("icon_url") if isinstance(ftr, dict) else None) or None
                                    clean_guild(
                                        console,
                                        client,
                                        gid,
                                        desired_name=None,
                                        desired_icon_spec=None,
                                        channel_count=5,
                                        channel_base_name="general",
                                        announce_mode="webhook",
                                        embed_title=None,
                                        embed_description=str(emb.get("description", "") if isinstance(emb, dict) else ""),
                                        embed_image_url=img_url,
                                        embed_footer_text=ftr_text,
                                        embed_footer_icon_url=ftr_icon,
                                        message_text=str(cfg.get("content", "") or ""),
                                        embed_repeats=1,
                                        message_repeats=1,
                                        webhook_name=str(cfg.get("webhook_name", "Krysten") or "Krysten"),
                                        webhook_icon_spec=str(cfg.get("webhook_icon_spec", "") or ""),
                                        delete_emojis_after=False,
                                        log_sink=sink,
                                    )
                                t = Thread(target=runner, daemon=True)
                                t.start()
                                while t.is_alive():
                                    while not logq.empty():
                                        console.print(logq.get_nowait())
                                    time.sleep(0.02)
                                while not logq.empty():
                                    console.print(logq.get_nowait())
                                from ui.styles import format_log
                                console.print(format_log("finalized", "Press Enter to back..."))
                                console.input("\n")
                                break

                            icon_spec = console.input(glow_text("Icon URL/emoji/file (or 'skip'/'remove'): ", strength=1.1)).strip()
                            new_name = console.input(glow_text("New server name (or 'skip'): ", strength=1.1)).strip()
                            try:
                                ch_count = int(console.input(glow_text("Channels to create (max 50, default 5): ", strength=1.1)).strip() or "5")
                            except Exception:
                                ch_count = 5
                            base_name = console.input(glow_text("Base channel name: ", strength=1.1)).strip() or "general"
                            mode = console.input(glow_text("Announcement mode [none/webhook/message/both]: ", strength=1.1)).strip().lower() or "none"
                            if mode in ("webhook", "both"):
                                try:
                                    emb_reps = int(console.input(glow_text("Embed repeats per channel [1-100, default 1]: ", strength=1.1)).strip() or "1")
                                except Exception:
                                    emb_reps = 1
                            else:
                                emb_reps = 1
                            if mode in ("message", "both"):
                                try:
                                    msg_reps = int(console.input(glow_text("Text repeats per channel [1-100, default 1]: ", strength=1.1)).strip() or "1")
                                except Exception:
                                    msg_reps = 1
                            else:
                                msg_reps = 1
                            del_emojis = console.input(glow_text("Delete emojis after? (Y/N): ", strength=1.1)).strip().lower()
                            confirm = console.input(glow_text(f"Proceed clean on '{g.get('name')}'? (Y/N): ", strength=1.1)).strip().lower()
                            if not confirm.startswith("y"):
                                console.print(glow_text("Cancelled.", strength=1.1))
                                break
                            from ui.styles import format_log
                            from queue import Queue
                            logq: Queue[RText] = Queue()
                            def sink(kind: str, message: str):
                                logq.put(format_log(kind, message))
                            from threading import Thread
                            def runner():
                                ftr = cur_footer if isinstance(cur_footer, dict) else None
                                ftr_text = (ftr.get("text") if isinstance(ftr, dict) else None) or None
                                ftr_icon = (ftr.get("icon_url") if isinstance(ftr, dict) else None) or None
                                clean_guild(
                                    console,
                                    client,
                                    gid,
                                    desired_name=new_name,
                                    desired_icon_spec=icon_spec,
                                    channel_count=ch_count,
                                    channel_base_name=base_name,
                                    announce_mode=mode,
                                    embed_title=None,
                                    embed_description=new_desc,
                                    embed_image_url=new_img,
                                    embed_footer_text=ftr_text,
                                    embed_footer_icon_url=ftr_icon,
                                    message_text=new_content,
                                    embed_repeats=emb_reps,
                                    message_repeats=msg_reps,
                                    webhook_name=new_wh_name,
                                    webhook_icon_spec=new_wh_icon,
                                    delete_emojis_after=del_emojis.startswith("y"),
                                    log_sink=sink,
                                )
                            t = Thread(target=runner, daemon=True)
                            t.start()
                            while t.is_alive():
                                while not logq.empty():
                                    console.print(logq.get_nowait())
                                time.sleep(0.01)
                            while not logq.empty():
                                console.print(logq.get_nowait())
                            from ui.styles import format_log
                            console.print(format_log("finalized", "Press Enter to back..."))
                            console.input("\n")
                            break
            elif choice == "07":
                console.print(glow_text("Option 07 is disabled for now.", strength=1.1))
            else:
                pass