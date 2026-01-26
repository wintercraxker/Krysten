import requests
from typing import List, Optional, Dict, Any

API_BASE = "https://discord.com/api/v9"


class DiscordClient:
    def __init__(self, token: str):
        self.token = token.strip()
        self.headers = {"Authorization": f"Bot {self.token}"}
        self.session = requests.Session()
        try:
            from requests.adapters import HTTPAdapter
            adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
        except Exception:
            pass

    def get_me(self) -> Optional[Dict[str, Any]]:
        try:
            r = self.session.get(f"{API_BASE}/users/@me", headers=self.headers, timeout=6)
            if r.status_code == 200:
                return r.json()
            return None
        except requests.RequestException:
            return None

    def is_connected(self) -> bool:
        return self.get_me() is not None

    def list_guilds(self) -> List[Dict[str, Any]]:
        try:
            r = self.session.get(f"{API_BASE}/users/@me/guilds", headers=self.headers, timeout=8)
            if r.status_code == 200:
                return r.json() or []
            return []
        except requests.RequestException:
            return []

    def list_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        try:
            r = self.session.get(f"{API_BASE}/guilds/{guild_id}/channels", headers=self.headers, timeout=8)
            if r.status_code == 200:
                return r.json() or []
            return []
        except requests.RequestException:
            return []

    def delete_channel(self, channel_id: str, reason: str = "") -> bool:
        headers = dict(self.headers)
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        try:
            r = self.session.delete(
                f"{API_BASE}/channels/{channel_id}",
                headers=headers,
                timeout=10,
            )
            if r.status_code in (200, 204):
                return True
            if r.status_code == 429:
                try:
                    after = float(r.headers.get("Retry-After", "1"))
                except Exception:
                    after = 1.0
                import time
                time.sleep(after)
                r2 = self.session.delete(
                    f"{API_BASE}/channels/{channel_id}",
                    headers=headers,
                    timeout=10,
                )
                return r2.status_code in (200, 204)
            return False
        except requests.RequestException:
            return False

    def create_channel(self, guild_id: str, name: str, type: int = 0, reason: str = "") -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {"name": name, "type": type}
        headers = {**self.headers, "Content-Type": "application/json"}
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        try:
            r = self.session.post(
                f"{API_BASE}/guilds/{guild_id}/channels",
                headers=headers,
                json=payload,
                timeout=10,
            )
            if r.status_code in (200, 201):
                return r.json()
            if r.status_code == 429:
                try:
                    after = float(r.headers.get("Retry-After", "1"))
                except Exception:
                    after = 1.0
                import time
                time.sleep(after)
                r2 = self.session.post(
                    f"{API_BASE}/guilds/{guild_id}/channels",
                    headers=headers,
                    json=payload,
                    timeout=10,
                )
                return r2.json() if r2.status_code in (200, 201) else None
            return None
        except requests.RequestException:
            return None

    def create_webhook(self, channel_id: str, name: str, avatar_data_uri: Optional[str] = None, reason: str = "") -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {"name": name}
        if avatar_data_uri is not None and avatar_data_uri != "":
            payload["avatar"] = avatar_data_uri
        headers = {**self.headers, "Content-Type": "application/json"}
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        try:
            attempts = 4
            for i in range(attempts):
                r = self.session.post(
                    f"{API_BASE}/channels/{channel_id}/webhooks",
                    headers=headers,
                    json=payload,
                    timeout=10,
                )
                if r.status_code in (200, 201):
                    return r.json()
                if r.status_code == 429:
                    try:
                        after = float(r.headers.get("Retry-After", "1"))
                    except Exception:
                        after = 1.0
                    import time, random
                    time.sleep(after + random.uniform(0.2, 0.6))
                    continue
                if 500 <= r.status_code < 600 and i < attempts - 1:
                    import time, random
                    time.sleep(0.5 + random.uniform(0.2, 0.6))
                    continue
                return {"error_status": r.status_code, "error_text": r.text}
            return {"error_status": r.status_code, "error_text": r.text}
        except requests.RequestException as e:
            return {"error_status": -1, "error_text": str(e)}

    def send_webhook_message(self, webhook_id: str, token: str, content: str = "", embeds: Optional[list] = None, wait: bool = True) -> bool:
        payload: Dict[str, Any] = {"content": content or ""}
        if embeds:
            payload["embeds"] = embeds
        try:
            url = f"{API_BASE}/webhooks/{webhook_id}/{token}" + ("?wait=true" if wait else "")
            r = self.session.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=10,
            )
            if r.status_code in (200, 201, 204):
                try:
                    if r.status_code == 204:
                        return True
                    data = r.json()
                    return bool(data and data.get("id"))
                except Exception:
                    return r.status_code == 204
            if r.status_code == 429:
                try:
                    after = float(r.headers.get("Retry-After", "1"))
                    try:
                        j = r.json()
                        after = float(j.get("retry_after", after))
                    except Exception:
                        pass
                except Exception:
                    after = 1.0
                import time, random
                time.sleep(after + random.uniform(0.2, 0.6))
                url2 = f"{API_BASE}/webhooks/{webhook_id}/{token}" + ("?wait=true" if wait else "")
                r2 = self.session.post(
                    url2,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=10,
                )
                if r2.status_code in (200, 201, 204):
                    try:
                        if r2.status_code == 204:
                            return True
                        data2 = r2.json()
                        return bool(data2 and data2.get("id"))
                    except Exception:
                        return r2.status_code == 204
                return False
            return False
        except requests.RequestException:
            return False
    def send_message(self, channel_id: str, content: str) -> bool:
        payload = {"content": content}
        try:
            r = self.session.post(
                f"{API_BASE}/channels/{channel_id}/messages",
                headers={**self.headers, "Content-Type": "application/json"},
                json=payload,
                timeout=8,
            )
            if r.status_code in (200, 201):
                try:
                    data = r.json()
                    return bool(data and data.get("id") and str(data.get("channel_id")) == str(channel_id))
                except Exception:
                    return False
            if r.status_code == 429:
                try:
                    after = float(r.headers.get("Retry-After", "1"))
                except Exception:
                    after = 1.0
                import time
                time.sleep(after)
                r2 = self.session.post(
                    f"{API_BASE}/channels/{channel_id}/messages",
                    headers={**self.headers, "Content-Type": "application/json"},
                    json=payload,
                    timeout=8,
                )
                if r2.status_code in (200, 201):
                    try:
                        data2 = r2.json()
                        return bool(data2 and data2.get("id") and str(data2.get("channel_id")) == str(channel_id))
                    except Exception:
                        return False
                return False
            return False
        except requests.RequestException:
            return False

    def list_members(self, guild_id: str, limit: int = 1000, after: str = None):
        params = {"limit": str(limit)}
        if after:
            params["after"] = after
        try:
            r = self.session.get(
                f"{API_BASE}/guilds/{guild_id}/members",
                headers=self.headers,
                params=params,
                timeout=10,
            )
            if r.status_code == 200:
                return r.json() or []
            return []
        except requests.RequestException:
            return []

    def get_guild(self, guild_id: str, with_counts: bool = True):
        try:
            params = {"with_counts": "true"} if with_counts else None
            r = self.session.get(
                f"{API_BASE}/guilds/{guild_id}",
                headers=self.headers,
                params=params,
                timeout=8,
            )
            if r.status_code == 200:
                return r.json()
            return None
        except requests.RequestException:
            return None

    def ban_member(self, guild_id: str, user_id: str, delete_message_seconds: int = 0, reason: str = "") -> bool:
        payload = {"delete_message_seconds": delete_message_seconds}
        headers = {**self.headers, "Content-Type": "application/json"}
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        try:
            r = self.session.put(
                f"{API_BASE}/guilds/{guild_id}/bans/{user_id}",
                headers=headers,
                json=payload,
                timeout=10,
            )
            if r.status_code in (200, 201, 204):
                return True
            if r.status_code == 429:
                try:
                    after = float(r.headers.get("Retry-After", "1"))
                except Exception:
                    after = 1.0
                import time
                time.sleep(after)
                r2 = self.session.put(
                    f"{API_BASE}/guilds/{guild_id}/bans/{user_id}",
                    headers=headers,
                    json=payload,
                    timeout=10,
                )
                return r2.status_code in (200, 201, 204)
            return False
        except requests.RequestException:
            return False

    def get_member(self, guild_id: str, user_id: str):
        try:
            r = self.session.get(
                f"{API_BASE}/guilds/{guild_id}/members/{user_id}",
                headers=self.headers,
                timeout=8,
            )
            if r.status_code == 200:
                return r.json()
            return None
        except requests.RequestException:
            return None

    def get_roles(self, guild_id: str):
        try:
            r = self.session.get(
                f"{API_BASE}/guilds/{guild_id}/roles",
                headers=self.headers,
                timeout=8,
            )
            if r.status_code == 200:
                return r.json() or []
            return []
        except requests.RequestException:
            return []

    def get_emojis(self, guild_id: str):
        try:
            r = self.session.get(
                f"{API_BASE}/guilds/{guild_id}/emojis",
                headers=self.headers,
                timeout=8,
            )
            if r.status_code == 200:
                return r.json() or []
            return []
        except requests.RequestException:
            return []

    def delete_emoji(self, guild_id: str, emoji_id: str, reason: str = "") -> bool:
        headers = dict(self.headers)
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        try:
            r = self.session.delete(
                f"{API_BASE}/guilds/{guild_id}/emojis/{emoji_id}",
                headers=headers,
                timeout=10,
            )
            if r.status_code in (200, 204):
                return True
            if r.status_code == 429:
                try:
                    after = float(r.headers.get("Retry-After", "1"))
                except Exception:
                    after = 1.0
                import time
                time.sleep(after)
                r2 = self.session.delete(
                    f"{API_BASE}/guilds/{guild_id}/emojis/{emoji_id}",
                    headers=headers,
                    timeout=10,
                )
                return r2.status_code in (200, 204)
            return False
        except requests.RequestException:
            return False

    def patch_guild(self, guild_id: str, payload: Dict[str, Any], reason: str = "") -> bool:
        headers = {**self.headers, "Content-Type": "application/json"}
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        try:
            r = self.session.patch(
                f"{API_BASE}/guilds/{guild_id}",
                headers=headers,
                json=payload,
                timeout=12,
            )
            if r.status_code == 200 or r.status_code == 204:
                return True
            if r.status_code == 429:
                try:
                    after = float(r.headers.get("Retry-After", "1"))
                except Exception:
                    after = 1.0
                import time
                time.sleep(after)
                r2 = self.session.patch(
                    f"{API_BASE}/guilds/{guild_id}",
                    headers=headers,
                    json=payload,
                    timeout=12,
                )
                return r2.status_code == 200 or r2.status_code == 204
            return False
        except requests.RequestException:
            return False

    def delete_role(self, guild_id: str, role_id: str, reason: str = "") -> bool:
        headers = dict(self.headers)
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        try:
            r = self.session.delete(
                f"{API_BASE}/guilds/{guild_id}/roles/{role_id}",
                headers=headers,
                timeout=10,
            )
            if r.status_code in (200, 204):
                return True
            if r.status_code == 429:
                try:
                    after = float(r.headers.get("Retry-After", "1"))
                except Exception:
                    after = 1.0
                import time
                time.sleep(after)
                r2 = self.session.delete(
                    f"{API_BASE}/guilds/{guild_id}/roles/{role_id}",
                    headers=headers,
                    timeout=10,
                )
                return r2.status_code in (200, 204)
            return False
        except requests.RequestException:
            return False

    def is_in_guild(self, guild_id: str) -> bool:
        me = self.get_me()
        if not me:
            return False
        return self.get_member(guild_id, me.get("id")) is not None

    def permissions_for_member(self, guild_id: str, user_id: str) -> int:
        roles = self.get_roles(guild_id)
        roles_by_id = {str(r.get("id")): int(r.get("permissions", "0")) for r in roles}
        member = self.get_member(guild_id, user_id)
        if not member:
            return 0
        perm = 0
        base_role_perm = roles_by_id.get(str(guild_id), 0)
        perm |= base_role_perm
        for rid in member.get("roles", []):
            perm |= roles_by_id.get(str(rid), 0)
        return perm

    def has_ban_permissions(self, guild_id: str) -> bool:
        me = self.get_me()
        if not me:
            return False
        perm = self.permissions_for_member(guild_id, me.get("id"))
        BAN_MEMBERS = 1 << 2
        ADMINISTRATOR = 1 << 3
        return (perm & BAN_MEMBERS) != 0 or (perm & ADMINISTRATOR) != 0