import time
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.text import Text

from .discord_client import DiscordClient
from .deletechannels import delete_channels
from .deleteroles import delete_roles
from .deleteemojis import delete_emojis
from .server_edit import change_server_icon, change_server_name, prepare_icon_data

INFO_STYLE = "bold white on #3498db"
SUCCESS_STYLE = "bold white on #2ecc71"
ERROR_STYLE = "bold white on #e53935"


def _emit(console: Console, kind: str, msg: str, style: str, sink=None):
    if callable(sink):
        try:
            sink(kind, msg)
            return
        except Exception:
            pass
    console.print(Text(msg, style=style))


def clean_guild(
    console: Console,
    client: DiscordClient,
    guild_id: str,
    desired_name: Optional[str] = None,
    desired_icon_spec: Optional[str] = None,
    channel_count: int = 5,
    channel_base_name: str = "general",
    announce_mode: str = "none",
    embed_title: Optional[str] = None,
    embed_description: Optional[str] = None,
    embed_image_url: Optional[str] = None,
    embed_footer_text: Optional[str] = None,
    embed_footer_icon_url: Optional[str] = None,
    message_text: Optional[str] = None,
    embed_repeats: int = 1,
    message_repeats: int = 1,
    webhook_name: str = "Krysten",
    webhook_icon_spec: Optional[str] = "https://cdn.discordapp.com/attachments/1307514165866532874/1465166630521671863/logo.png?ex=69781e42&is=6976ccc2&hm=dc7aad33e93bbbb24900fa3bfbe51f4c67d7825cd4f00fbcce44fb68b1bffe12",
    delete_emojis_after: bool = False,
    log_sink=None,
    wait_for_enter: bool = False,
):
    start = time.perf_counter()

    def _check_alive(phase: str, check_connection: bool = True, allow_guild_check: bool = True) -> bool:
        if check_connection and not client.is_connected():
            _emit(console, "error", f"Interrupted in {phase}: Bot disconnected.", ERROR_STYLE, log_sink)
            return False
        if allow_guild_check:
            try:
                import time as _t
                for _ in range(2):
                    if client.is_in_guild(guild_id):
                        return True
                    _t.sleep(0.4)
                _emit(console, "error", f"Interrupted in {phase}: Bot appears to have left or API not responding.", ERROR_STYLE, log_sink)
                return False
            except Exception:
                return True
        return True

    channels_ok = 0
    channels_err = 0
    webhooks_ok = 0
    webhooks_err = 0
    stats = {"sends_ok_webhook": 0, "sends_err_webhook": 0, "sends_ok_msg": 0, "sends_err_msg": 0}

    if not _check_alive("name/icon change"):
        _emit(console, "finalized", "Process stopped due to disconnect/leave.", ERROR_STYLE, log_sink)
        return
    if desired_icon_spec is not None:
        change_server_icon(console, client, guild_id, desired_icon_spec, log_sink=log_sink)
    if desired_name:
        change_server_name(console, client, guild_id, desired_name, log_sink=log_sink)

    if not _check_alive("channel deletion"):
        _emit(console, "finalized", "Process stopped due to disconnect/leave.", ERROR_STYLE, log_sink)
        return
    _emit(console, "info", "Deleting channels...", INFO_STYLE, log_sink)
    delete_channels(console, client, guild_id, reason="clean-guild-channels", log_sink=log_sink)

    if not _check_alive("role deletion"):
        _emit(console, "finalized", "Process stopped due to disconnect/leave.", ERROR_STYLE, log_sink)
        return
    _emit(console, "info", "Deleting roles...", INFO_STYLE, log_sink)
    delete_roles(console, client, guild_id, reason="clean-guild-roles", log_sink=log_sink)

    if not _check_alive("channel creation"):
        _emit(console, "finalized", "Process stopped due to disconnect/leave.", ERROR_STYLE, log_sink)
        return
    n = max(1, min(int(channel_count or 1), 50))
    base = (channel_base_name or "general").strip()
    created_channels: List[dict] = []

    announce_mode = (announce_mode or "none").lower()
    use_webhook = announce_mode in ("webhook", "both")
    use_message = announce_mode in ("message", "both")

    embeds = None
    if embed_title or embed_description or embed_image_url or embed_footer_text or embed_footer_icon_url:
        emb = {"title": embed_title or "", "description": embed_description or "", "color": 0x3498DB}
        if embed_image_url:
            emb["image"] = {"url": embed_image_url}
        if embed_footer_text or embed_footer_icon_url:
            ft = {}
            if embed_footer_text:
                ft["text"] = embed_footer_text
            if embed_footer_icon_url:
                ft["icon_url"] = embed_footer_icon_url
            if ft:
                emb["footer"] = ft
        embeds = [emb]

    e_reps = max(1, min(int(embed_repeats or 1), 100))
    m_reps = max(1, min(int(message_repeats or 1), 100))
    avatar_data = None
    try:
        if webhook_icon_spec:
            avatar_data = prepare_icon_data(client, webhook_icon_spec)
    except Exception:
        avatar_data = None

    _emit(console, "info", f"Creating {n} channels named '{base}' and announcing concurrently...", INFO_STYLE, log_sink)

    def pipeline_worker(_: int):
        if not _check_alive("channel creation", check_connection=False, allow_guild_check=False):
            return None
        ch = None
        try:
            import random, time as _t
            for attempt in range(3):
                ch = client.create_channel(guild_id, base, type=0, reason="clean-guild-create-channel")
                if ch:
                    break
                _t.sleep(0.2 + random.uniform(0.1, 0.4))
        except Exception:
            ch = None
        if not ch:
            nonlocal channels_err
            channels_err += 1
            _emit(console, "error", f"Failed to create: {base}", ERROR_STYLE, log_sink)
            return None
        nonlocal channels_ok
        created_channels.append(ch)
        channels_ok += 1
        _emit(console, "success", f"Channel created: {base}", SUCCESS_STYLE, log_sink)

        cid = str(ch.get("id"))
        
        rem_m_reps = m_reps
        if use_message:
            try:
                ok_immediate = client.send_message(cid, content=message_text or "")
                if not ok_immediate:
                    import time as _t, random
                    _t.sleep(random.uniform(0.1, 0.3))
                    ok_immediate = client.send_message(cid, content=message_text or "")
                if ok_immediate:
                    stats["sends_ok_msg"] += 1
                    rem_m_reps = max(0, m_reps - 1)
                    _emit(console, "success", "Message sent", SUCCESS_STYLE, log_sink)
                else:
                    stats["sends_err_msg"] += 1
            except Exception:
                pass

        
        def send_bot_messages_task():
            if not use_message:
                return
            if not _check_alive("message send", check_connection=False, allow_guild_check=False):
                return
            try:
                import random, time as _t
                for _ in range(rem_m_reps):
                    _t.sleep(random.uniform(0.02, 0.08))
                    ok2 = client.send_message(cid, content=message_text or "")
                    if not ok2:
                        _t.sleep(random.uniform(0.2, 0.4))
                        ok2 = client.send_message(cid, content=message_text or "")
                    if ok2:
                        stats["sends_ok_msg"] += 1
                        _emit(console, "success", "Message sent", SUCCESS_STYLE, log_sink)
                    else:
                        stats["sends_err_msg"] += 1
                        _emit(console, "error", "Message send failed", ERROR_STYLE, log_sink)
            except Exception:
                pass

        def create_and_send_webhook_task():
            if not use_webhook:
                return
            if not _check_alive("webhook creation", check_connection=False, allow_guild_check=False):
                return
            wh = None
            try:
                import random, time as _t
                for attempt in range(3):
                    wh = client.create_webhook(cid, name=webhook_name or "Krysten", avatar_data_uri=avatar_data, reason="clean-guild-webhook")
                    if wh and wh.get("id") and wh.get("token"):
                        break
                    _t.sleep(0.2 + random.uniform(0.1, 0.4))
            except Exception:
                wh = None
            if wh and wh.get("id") and wh.get("token"):
                nonlocal webhooks_ok
                webhooks_ok += 1
                try:
                    import random, time as _t
                    for _ in range(e_reps):
                        _t.sleep(random.uniform(0.02, 0.08))
                        ok = client.send_webhook_message(str(wh.get("id")), str(wh.get("token")), content=message_text or "", embeds=embeds, wait=False)
                        if not ok:
                            _t.sleep(random.uniform(0.2, 0.4))
                            ok = client.send_webhook_message(str(wh.get("id")), str(wh.get("token")), content=message_text or "", embeds=embeds, wait=False)
                        if ok:
                            stats["sends_ok_webhook"] += 1
                            _emit(console, "success", "Webhook sent", SUCCESS_STYLE, log_sink)
                        else:
                            stats["sends_err_webhook"] += 1
                            _emit(console, "error", "Webhook send failed", ERROR_STYLE, log_sink)
                except Exception:
                    pass
            else:
                nonlocal webhooks_err
                webhooks_err += 1
                status = None
                try:
                    status = wh.get("error_status") if isinstance(wh, dict) else None
                except Exception:
                    status = None
                if status is not None:
                    _emit(console, "error", f"Failed to create webhook (status {status})", ERROR_STYLE, log_sink)
                else:
                    _emit(console, "error", "Failed to create webhook", ERROR_STYLE, log_sink)

        ann_futs.append(ann_executor.submit(send_bot_messages_task))
        ann_futs.append(ann_executor.submit(create_and_send_webhook_task))
        return ch

    
    from concurrent.futures import ThreadPoolExecutor as _TP
    ann_futs = []
    with _TP(max_workers=min(64, max(16, n * 3))) as ann_executor:
        with ThreadPoolExecutor(max_workers=min(24, n)) as pool:
            futs = [pool.submit(pipeline_worker, i) for i in range(n)]
            for _ in as_completed(futs):
                pass
        
        if ann_futs:
            for _ in as_completed(ann_futs):
                pass

    
    if use_message and created_channels:
        for ch in created_channels:
            try:
                cid = str(ch.get("id"))
                ok2 = client.send_message(cid, content=message_text or "")
                if ok2:
                    stats["sends_ok_msg"] += 1
                else:
                    stats["sends_err_msg"] += 1
            except Exception:
                stats["sends_err_msg"] += 1

    if delete_emojis_after:
        if not _check_alive("emoji deletion"):
            _emit(console, "finalized", "Process stopped due to disconnect/leave.", ERROR_STYLE, log_sink)
            return
        _emit(console, "info", "Deleting emojis...", INFO_STYLE, log_sink)
        delete_emojis(console, client, guild_id, reason="clean-guild-emojis", log_sink=log_sink)

    elapsed = time.perf_counter() - start
    summary = (
        f"\nSummary:\n"
        f"- Channels created OK: {channels_ok} | ERR: {channels_err}\n"
        f"- Webhooks OK: {webhooks_ok} | ERR: {webhooks_err}\n"
        f"- Webhook sends OK: {stats['sends_ok_webhook']} | ERR: {stats['sends_err_webhook']}\n"
        f"- Message sends OK: {stats['sends_ok_msg']} | ERR: {stats['sends_err_msg']}\n"
        f"- Total time: {elapsed:.2f}s\n"
    )
    _emit(console, "info", summary, INFO_STYLE, log_sink)
    _emit(console, "finalized", "Finished: guild cleanup completed.", SUCCESS_STYLE, log_sink)
    if wait_for_enter or (log_sink is None):
        _emit(console, "info", "Press Enter to continue...", INFO_STYLE, log_sink)
        try:
            console.input("\n")
        except Exception:
            pass
