# ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ@ BTC - Krysten Bot <img src="https://media.discordapp.net/attachments/1307514165866532874/1465166630521671863/logo.png?ex=6978c702&is=69777582&hm=d0bc66a7ad591f6c979753dca48904a4a0969ac63506ee9eb65e88d8c467a4a0&=&format=webp&quality=lossless&width=48&height=48" alt="Logo" width="32" height="32" />

<p align="center">
  <img src="https://media.discordapp.net/attachments/1307514165866532874/1465422741036335320/pony-gang-vc-pony-gang.gif?ex=69790cc7&is=6977bb47&hm=41d104e250accfeb6c594755c2e39a3ab128bcd27139a8c8404d051caedf9e0f&=" alt="Krysten animation" style="width: 500px; height: auto;" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white" alt="Language: Python" />
  <img src="https://img.shields.io/badge/Runtime-CPython%203.10%2B-3776AB?logo=python&logoColor=white" alt="Runtime: CPython 3.10+" />
  <img src="https://img.shields.io/badge/UI-Rich-8A2BE2" alt="UI: Rich" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white" alt="Platform: Windows" />
  <a href="https://i.imgur.com/gSqVako.png"><img src="https://img.shields.io/badge/Release-v1-2ecc71?logo=github" alt="Release v1" /></a>
</p>

## 〢 👀 Preview

<p align="center">
  <img src="https://i.imgur.com/gSqVako.png" alt="Preview image" style="width: 700px; height: auto;" />
</p>

## 〢 ✨ Overview

- **Clean Guild**: Creates channels and announces (bot + webhooks) in parallel; can also delete roles, emojis, and channels; optionally change server name and icon.
- **Ban All**: Concurrent banning workflow (requires appropriate permissions).
- **Delete All**: Bulk delete roles, channels, and emojis with compact feedback.
- **Check Guilds**: See key info for your servers (connection, permissions, etc.).
- **Animated Panel**: Token flow and a clear, animated command panel.

---

## 〢 ❗ Pre-requisites

- Python 3.10+ (Windows recommended for the animated UI)
- Packages: `rich`, `requests`

Install with:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install rich requests
```

---

## 〢 🚀 First Run

1. Start the program:

```bash
python main.py
```

2. If no token is present, an animated message will prompt “Token not found”. Enter your bot token; it is saved to **config.json** under `BOT_TOKEN` without overwriting other fields.
3. If the token is valid, the command panel opens.

> Your **Clean Guild** configuration persists in **config.json** under `clean_preset`.

---

## 〢 🎛️ Panel & Commands

- `01 Ban All`: Bans all members (excluding the bot). Requires `BAN_MEMBERS` or `ADMINISTRATOR`.
- `02 Check Guilds`: Lists your servers and shows connection/permissions.
- `03 Delete All Roles`: Deletes all roles in the server.
- `04 Delete All Channels`: Deletes all channels in the server.
- `05 Delete All Emojis`: Deletes all emojis in the server.
- `06 Clean Guild`: Complete cleanup + concurrent creation/announcements.
- `07–10` (soon): Reserved for future features.
- `00 Exit`: Quit the panel.

---

## 〢 🧹 Clean Guild — Details & Configuration

Clean Guild runs a per-channel pipeline with **immediate creation + announcement**, and **parallel tasks** for bot messages and webhooks. It handles `429` rate limits via jitter and short retries to keep speed high.

- **Key inputs** (from panel):
  - `Channels to create (max 50)`: Concurrent channel creation per run.
  - `Embed repeats [1-100]`: Per-channel embed sends via webhook.
  - `Text repeats [1-100]`: Per-channel bot message sends.
- **Announcements**:
  - `announce_mode`: `message`, `webhook`, `both`, `none`.
  - `message_text`: Plain text sent by the bot.
  - `embeds`: Optional title, description, image, and footer.
  - `webhook_name` and `webhook_icon_spec`: Webhook name and icon (URL or file path supported).
- **Server changes** (optional):
  - `desired_name`: Change server name.
  - `desired_icon_spec`: Change server icon (converted to data URI).
- **Post-process**:
  - `delete_emojis_after`: Delete emojis after announcements.
- **Limits**:
  - Channels: `<= 50` per run.
  - Repeats: `1..100` for embeds and messages.
- **Summary at finish**:
  - Channels created OK/ERR
  - Webhooks OK/ERR
  - Webhook sends OK/ERR
  - Bot message sends OK/ERR
  - Total time

---

## 〢 ⛔ Ban All — Notes

- Available when the bot has `BAN_MEMBERS` or `ADMINISTRATOR`.
- Automatically excludes the bot user.
- Runs concurrently and reports success/error per member.

---

## 〢 ⚙️ Configuration (`config.json`)

- `BOT_TOKEN`: Set automatically when you enter the token on first run.
- `clean_preset`: Reusable template with fields like `description`, `content`, `image_url`, `wh_name`, `wh_icon`, etc. Editable via the Clean Guild panel.

> Token saves are merged into the JSON; other settings are preserved.

---

## 〢 ⚖️ Responsibility

Use this project responsibly and in compliance with Discord's Terms of Service and Community Guidelines. Operate it only on servers where you have explicit authorization and sufficient permissions. You are solely responsible for any actions taken with this software.
