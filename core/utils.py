from datetime import datetime, timezone

DISCORD_EPOCH_MS = 1420070400000

def snowflake_timestamp_ms(snowflake_id: int) -> int:
    return ((int(snowflake_id) >> 22) + DISCORD_EPOCH_MS)

def snowflake_to_iso(snowflake_id: int) -> str:
    ts_ms = snowflake_timestamp_ms(snowflake_id)
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
