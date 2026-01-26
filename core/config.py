import json
import os
from typing import Optional, Dict, Any

def save_token(token: str):
    data = _read_config()
    data["BOT_TOKEN"] = token or ""
    _write_config(data)

def load_token() -> Optional[str]:
    if not os.path.exists("config.json"):
        return None

 
    try:
        with open("config.json", "r") as f:
            data = json.load(f)
        token = data.get("BOT_TOKEN")
        if isinstance(token, str):
            token = token.strip()
            if token:
                return token
        return None
    except (json.JSONDecodeError, OSError):
        return None


def _read_config() -> Dict[str, Any]:
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f) or {}
    except Exception:
        pass
    return {}


def _write_config(data: Dict[str, Any]):
    tmp = dict(data or {})
    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(tmp, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def load_clean_config() -> Optional[Dict[str, Any]]:
    data = _read_config()
    preset = data.get("clean_preset")
    if isinstance(preset, dict):
        return preset
    return None


def write_default_clean_config() -> Dict[str, Any]:
    data = _read_config()
    default_preset: Dict[str, Any] = {
        "content": "@everyone - discord invite",
        "embeds": [
            {
                "description": "ㅤㅤㅤㅤㅤㅤㅤyour server has been clean by **krysten**\nㅤㅤㅤㅤㅤㅤㅤㅤto **retrieve your server** join [here](https://discohook.app/discord)",
                "color": 3225146,
                "footer": {
                    "text": "krysten bot ; zSpoofing",
                    "icon_url": "https://media.discordapp.net/attachments/1307514165866532874/1465166630521671863/logo.png?ex=6978c702&is=69777582&hm=d0bc66a7ad591f6c979753dca48904a4a0969ac63506ee9eb65e88d8c467a4a0&=&format=webp&quality=lossless&width=572&height=572"
                },
                "image": {
                    "url": "https://media.discordapp.net/attachments/1445253902084866099/1465376717605568572/pony-gang-vc-pony-gang.gif?ex=6978e1ea&is=6977906a&hm=7dd7100b4d3819d2672d7bd5beafb05016700a18bd685ba94ae5a88d781da10a&="
                },
            }
        ],
        "webhook_name": "Krysten",
        "webhook_icon_spec": "https://cdn.discordapp.com/attachments/1307514165866532874/1465166630521671863/logo.png?ex=69781e42&is=6976ccc2&hm=dc7aad33e93bbbb24900fa3bfbe51f4c67d7825cd4f00fbcce44fb68b1bffe12",
    }
    data["clean_preset"] = default_preset
    _write_config(data)
    return default_preset


def save_clean_config(preset: Dict[str, Any]) -> Dict[str, Any]:
    data = _read_config()
    data["clean_preset"] = preset or {}
    _write_config(data)
    return data["clean_preset"]

