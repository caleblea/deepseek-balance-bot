# DeepSeek Balance Monitor Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-Platform-4F46E5)](https://platform.deepseek.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://t.me/botfather)

Periodically queries your [DeepSeek platform](https://platform.deepseek.com/) account balance and pushes it as a pinned Telegram message, along with system uptime and service health. Built entirely on the Python standard library — zero third-party dependencies.

```
💰 ¥12.34 | 14:30
🆙 3d 2h  | 🟢SS 🟢Bot
```

---

## Features

- 🚀 **Zero dependencies** — pure Python stdlib, no `pip install`
- 📌 **Auto-pin** — balance message is always pinned to the top
- 🔄 **Auto-recovery** — finds and reuses the last pinned message after restart
- 🛡️ **Singleton lock** — PID file prevents concurrent instances
- 📡 **Service monitoring** — optionally track other systemd services
- ⏱️ **Uptime display** — shows how long the system has been running
- 🔁 **Retry on failure** — configurable retries for balance queries

---

## Quick Start

### 1. Prerequisites

- **Linux** server (Debian / Ubuntu recommended)
- **Python ≥ 3.8**
- **systemd** (for auto-start on boot)

### 2. Create a Telegram Bot

Message [@BotFather](https://t.me/botfather) on Telegram:

```
/newbot
```

Follow the prompts to name your bot (e.g. "DeepSeek Balance Monitor"). On success you'll receive a **Token** like:

```
123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

#### Get the Chat ID

Add the bot to the target chat (private or group), send any message, then visit:

```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

The `chat.id` field in the JSON response is your target ID.

### 3. Clone & Configure

```bash
git clone https://github.com/YOUR_USER/deepseek-balance-bot.git
cd deepseek-balance-bot
cp .env.example .env
```

Edit `.env` with your settings:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek platform API Key | — |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token | — |
| `TELEGRAM_CHAT_ID` | ✅ | Target chat ID (numeric) | — |
| `INTERVAL_SECONDS` | ❌ | Polling interval (seconds) | `300` (5 min) |
| `TIMEZONE_OFFSET` | ❌ | Timezone offset (hours) | `8` (CST) |
| `MONITOR_SERVICES` | ❌ | systemd services to monitor | `SS:shadowsocks-rust,Bot:deepseek-balance-bot` |
| `RETRY_COUNT` | ❌ | Balance query retries | `3` |
| `RETRY_INTERVAL` | ❌ | Retry delay (seconds) | `5` |

> Get your DeepSeek API Key at [platform.deepseek.com](https://platform.deepseek.com/) → **API Keys**. Keys are only shown once at creation — save it immediately.

### 4. Test Run

```bash
python3 balance_bot.py --once
```

Expected output:

```
No saved message ID found, will create a new one.
Creating a new pinned message...
New message created, ID: 456
```

Check Telegram — you should see the first balance message pinned.

### 5. Register as a System Service

```bash
sudo cp deepseek-balance-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable deepseek-balance-bot
sudo systemctl start deepseek-balance-bot
```

**Verify status:**

```bash
sudo systemctl status deepseek-balance-bot
```

---

## Operations

### View Logs

```bash
# Follow live
sudo journalctl -u deepseek-balance-bot -f

# Last 50 lines
sudo journalctl -u deepseek-balance-bot -n 50 --no-pager
```

### Common Commands

```bash
# Push balance once manually
python3 balance_bot.py --once

# Restart the service
sudo systemctl restart deepseek-balance-bot

# Stop the service
sudo systemctl stop deepseek-balance-bot

# Update code (auto-restarts if post-merge hook is installed)
git pull
```

### Git Auto-Restart Hook

The repo includes a post-merge hook that restarts the service automatically after `git pull`:

```bash
ln -sf ../../githook-post-merge.sh .git/hooks/post-merge
chmod +x .git/hooks/post-merge
```

---

## Service Monitoring

Configure `MONITOR_SERVICES` in `.env` to track systemd services — each one shows a 🟢/🔴 status in the message footer:

```ini
MONITOR_SERVICES=SS:shadowsocks-rust,Bot:deepseek-balance-bot,Nginx:nginx
```

Format: `Label:service-name,Label:service-name`

---

## Project Structure

```
deepseek-balance-bot/
├── balance_bot.py                # Main script
├── deepseek-balance-bot.service  # systemd unit file
├── githook-post-merge.sh         # Git auto-restart hook
├── .env.example                  # Environment template
├── tg_msg_id.txt                 # Message ID cache (auto-generated)
├── balance_bot.pid               # PID lock file (auto-generated)
└── balance_bot.log               # Log file (auto-generated)
```

---

## FAQ

<details>
<summary><b>"Another instance is already running" on startup</b></summary>

Remove the stale PID file:

```bash
sudo rm -f /opt/deepseek-balance-bot/balance_bot.pid
```

</details>

<details>
<summary><b>Message always shows "❌ Error"</b></summary>

Check:
1. DeepSeek API Key — expired or out of credit?
2. Can the server reach `https://api.deepseek.com`?
3. Is `.env` formatted correctly (no stray quotes/spaces)?

</details>

<details>
<summary><b>Telegram message not updating</b></summary>

Check:
1. Bot token and chat ID are correct
2. Bot is still in the group / not blocked by the user
3. Can the server reach `https://api.telegram.org`?

</details>

<details>
<summary><b>How to change polling frequency?</b></summary>

Update `INTERVAL_SECONDS` in `.env`, then restart:

```ini
INTERVAL_SECONDS=600   # every 10 minutes
INTERVAL_SECONDS=3600  # every hour
```

```bash
sudo systemctl restart deepseek-balance-bot
```

</details>

---

## License

[MIT](LICENSE)
