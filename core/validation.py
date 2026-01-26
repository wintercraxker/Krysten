import re
import requests

def is_valid_token(token: str) -> bool:
    if not token or not isinstance(token, str):
        return False

    token = token.strip()

    pattern = re.compile(r"^[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+$")
    if not pattern.match(token):
        return False

    parts = token.split(".")
    if len(parts[0]) < 10 or len(parts[1]) < 6 or len(parts[2]) < 20:
        return False

    headers = {"Authorization": f"Bot {token}"}
    url = "https://discord.com/api/v9/users/@me"

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return True
        if response.status_code == 401:
            return False
        return True
    except requests.RequestException:
        return True

def get_bot_name(token: str):
    if not token or not isinstance(token, str):
        return None

    headers = {"Authorization": f"Bot {token.strip()}"}
    url = "https://discord.com/api/v9/users/@me"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("username") or data.get("global_name")
    except requests.RequestException:
        pass
    return None
