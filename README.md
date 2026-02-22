# 🟢 Kick Channel Points Miner

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> [🇷🇺 **Читать на русском языке**](README_RU.md)

A powerful, asynchronous bot for automatically farming channel points on **Kick.com**. Features a modern Web Dashboard, advanced Telegram control, and Cloudflare protection bypass.

---

## ✨ Features

*   **👥 Multi-Account Support:** Farm points with up to 10+ accounts simultaneously, each with its own streamer list and limits.
*   **🎯 Priority System:** Streamers are prioritized by their position in the config. Higher-priority streamers automatically replace lower-priority ones when they go live.
*   **🔒 Concurrent Limits:** Set `max_concurrent` per account to control how many streamers are watched at once – prevents 403 rate-limiting.
*   **🌐 SOCKS5/HTTP Proxy:** Global or per-account proxy support to avoid IP blocks.
*   **🛡️ Cloudflare Bypass:** Built-in `curl_cffi` based session management with automatic retry on 403.
*   **🖥️ Web Dashboard:** Beautiful real-time dashboard showing all accounts, priorities, points, and streamer statuses with direct links to streams.
*   **📱 Telegram Bot:**
    *   **Owner/Guest System:** Owner has full control, guests can only view status.
    *   **Multi-Account Views:** `/status`, `/balance`, `/accounts` commands show data per account.
    *   **Live Notifications:** Updates on points farmed and errors.
    *   **Remote Control:** Restart the miner via Telegram.
*   **🌐 Multi-language:** Support for English and Russian.
*   **📉 Smart Logging:** Clean console output with optional Debug mode.
*   **♻️ Memory-Safe:** Sessions are reused and properly closed – no memory leaks during long runs.

---

## 🚀 Installation

1.  **Clone or Download** the repository:
    ```bash
    git clone https://github.com/Baillora/Kick_Channel_Points_Miner.git
    cd Kick_Channel_Points_Miner
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure**: Rename `config.example.json` to `config.json` and fill it out (see below)

---

## ⚙️ Configuration (`config.json`)

### Multi-Account Format (Recommended)

```json
{
  "Language": "en",
  "Debug": false,

  "WebDashboard": {
    "enabled": true,
    "port": 5000
  },

  "Telegram": {
    "enabled": false,
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "chat_id": "YOUR_TELEGRAM_USER_ID",
    "allowed_users": [123456789]
  },

  "Discord": {
    "enabled": false,
    "webhook_url": "https://discord.com/api/webhooks/XXXX/YYYY",
    "username": "Baillora KickMiner",
    "avatar_url": "",
    "notify_points": true,
    "notify_status_change": true,
    "notify_errors": true,
    "notify_startup": true,
    "min_points_gain": 10,
    "color_success": 3461464,
    "color_info": 5793266,
    "color_warning": 16763904,
    "color_error": 15746887
  },
  
  "Proxy": {
    "enabled": false,
    "url": "socks5://user:password@host:port"
  },

  "Accounts": [
    {
      "alias": "Main Account",
      "token": "YOUR_KICK_TOKEN_1",
      "proxy": null,
      "streamers": ["streamer1", "streamer2", "streamer3"],
      "max_concurrent": 2
    },
    {
      "alias": "Second Account",
      "token": "YOUR_KICK_TOKEN_2",
      "proxy": "socks5://user:pass@proxy2:1080",
      "streamers": ["streamer2", "streamer3", "streamer4"],
      "max_concurrent": 1
    }
  ],

  "Check_interval": 120,
  "Reconnect_cooldown": 600,
  "Connection_stagger_min": 3,
  "Connection_stagger_max": 8
}
```

### Legacy Format (Still Supported)
The old single-account format is automatically converted:

```json
{
  "Language": "en",
  "Debug": false,
  "WebDashboard": { "enabled": true, "port": 5000 },
  "Telegram": { "enabled": false, "bot_token": "", "chat_id": "", "allowed_users": [] },
  "Private": { "token": "YOUR_KICK_TOKEN" },
  "Streamers": ["stream1", "stream2", "stream3"],
  "Max_active_channels": 5
}
```

---

### Parameters description:

*   **`Language`**: Set to `"en"` or `"ru"`.
*   **`Debug`**: Set `"true"` for detailed logs, `"false"` for clean output.
*   **`WebDashboard`**:
    *   `enabled`: Set to `true` to turn on the web panel.
    *   `port`: Port to access stats (default: `http://localhost:5000`).
*   **`Telegram`**:
    *   `bot_token`: Get this from @BotFather.
    *   `chat_id`: Your personal Telegram ID (you will be the **Owner**).
    *   `allowed_users`: List of user IDs who can view status/balance (Guests).
*   **`Proxy.enabled`**: Enable global proxy for all accounts.
    *   `Proxy.url`: Global proxy URL (`socks5://`, `http://`, `https://`).
*   **`Check_interval`**: Seconds between online status checks (default: `120`).
*   **`Reconnect_cooldown`**: Seconds before reconnection attempt (default: `600`).
*   **`Connection_stagger_min/max`**: Delay range (seconds) between connecting to streamers.
*   **`👥 Account Parameters`**:
    *   `alias`: Display name for the account.
    *   `token`: Kick authentication token (Bearer token).
    *   `proxy`: Per-account proxy (overrides global). Set `null` to use global
    *   `streamers`: Ordered list of streamer names. **Position = priority** (index 0 = highest)
    *   `max_concurrent`: 	Maximum number of streamers to watch simultaneously

---

## 🎯 How Priority Works
```
Config: ["streamer1", "streamer2", "streamer3", "streamer4"]
         Priority 0    Priority 1    Priority 2    Priority 3
         (Highest)                                  (Lowest)

max_concurrent: 2
```
Time | Event | Watching
| :--- | :--- | :--- |
T0 | streamer2 & streamer3 go live | `[streamer2, streamer3]`
T1 | streamer1 goes live (higher priority) | `[streamer1, streamer2]` ← streamer3 displaced!
T2	| streamer1 goes offline | `[streamer2, streamer3]` ← streamer3 returns
T3	| streamer4 goes live | `[streamer2, streamer3]` ← streamer4 waits (limit reached)

---

### 🔑 How to get your Kick Token

1.  Log in to **Kick.com** in your browser.
2.  Press `F12` to open Developer Tools.
3.  Go to the **Network** tab.
4.  Refresh the page (`F5`).
5.  Click on any request that appears (e.g., `auth.`).
6.  On the right panel, go to the **Headers** tab and scroll down to **Request Headers**.
7.  Find the `authorization` line.
8.  Copy the long string **after** the word `Bearer`. She looks like this `123456789|************************************`.
9. Paste this string into your `config.json` in the `"token"` field.

## 🎮 Usage

Run the miner:
```bash
python main.py
```

The bot will:

1. Load all accounts from config
2. Check which streamers are online
3. Connect to the top N (by priority) for each account
4. Dynamically rebalance when streamers go online/offline
5. Automatically restart on crashes

### 📱 Telegram Commands

| Command | Description | Permission |
| :--- | :--- | :--- |
| `/start` | Initialize the bot and keyboard | Everyone |
| `/status` | View active streamers and uptime | Everyone |
| `/balance` | Check farmed points for all channels | Everyone |
| `/accounts` | Overview of all accounts | Everyone |
| `/help` | Show available commands | Everyone |
| `/restart` | **Restart the miner process** | **Owner Only** |
| `/language` | Change bot language (`en`/`ru`) | **Owner Only** |

---

### 🟣 Discord Webhook

Send real-time notifications to any Discord channel via webhooks – no bot required!

**Setup:**
1. In your Discord server, go to **Channel Settings → Integrations → Webhooks**
2. Click **New Webhook**, copy the URL
3. Paste into `config.json` → `Discord.webhook_url`

**Configuration:**
```json
{
  "Discord": {
    "enabled": true,
    "webhook_url": "https://discord.com/api/webhooks/XXXX/YYYY",
    "username": "Baillora KickMiner",
    "avatar_url": "",
    "notify_points": true,
    "notify_status_change": true,
    "notify_errors": true,
    "notify_startup": true,
    "min_points_gain": 10,
    "color_success": 3461464,
    "color_info": 5793266,
    "color_warning": 16763904,
    "color_error": 15746887
  }
}
```

| Parameter | Description |
| :--- | :--- | 
| `webhook_url` | Discord webhook URL |
| `username` | Bot display name in Discord |
| `avatar_url` | Custom avatar URL (optional) |
| `notify_points` | Send notifications when points are earned |
| `notify_status_change` | Notify when streamers go online/offline/displaced |
| `notify_errors` | Send error notifications |
| `notify_startup` | Send startup summary |
| `min_points_gain` | Minimum points gain to trigger notification |
| `color_*` | 	Embed colors in decimal (use [color converter](https://www.mathsisfun.com/hexadecimal-decimal-colors.html)) |

Notifications include:

* 🚀 Startup summary with all accounts
* 💰 Points earned (with streamer link)
* ▶️ Started watching / ⏹ Displaced by priority
* 🟢 Streamer online / 🔴 Streamer offline
* ❌ Error reports
* 🔄 Restart notifications

---

## 🖥️ Web Dashboard

If enabled, visit **`http://localhost:5000`** in your browser.
You will see a real-time table with:
*   📊 All accounts with their limits and active streamers
*   🎯 Priority badges for each streamer
*   👁 Real-time watching/online/offline status
*   💰 Points balance per streamer
*   🔗 Direct "Watch" links to open streams on Kick.com
*   🔒 Proxy status per account
*   ⚠️ Error counters

---

## 🌐  Proxy Support

| Type | Format | Example |
| :--- | :--- | :--- |
| SOCKS5 | `socks5://user:pass@host:port` | `socks5://admin:123@proxy.com:1080` |
| SOCKS5 (no auth) | `socks5://host:port` | `socks5://proxy.com:1080` |
| HTTP | `http://user:pass@host:port` | `http://admin:123@proxy.com:8080` |
| HTTPS | `https://host:port` | `https://proxy.com:8080` |

Global proxy applies to all accounts. Per-account proxy overrides the global one.

---
## 📁 Project Structure

```
Kick_Channel_Points_Miner/
├── main.py                    # Entry point
├── account_manager.py         # Multi-account orchestrator with priorities
├── config.json                # Configuration
├── web_server.py              # Flask Web Dashboard
├── localization.py            # i18n loader
├── requirements.txt           # Dependencies
├── _websockets/
│   ├── ws_connect.py          # WebSocket client with proxy support
│   └── ws_token.py            # WS token acquisition
├── utils/
│   ├── kick_utility.py        # Channel/stream ID fetching
│   └── get_points_amount.py   # Points balance checking
├── tg_bot/
│   ├── bot.py                 # Telegram bot with multi-account support
│   └── lang/
│       ├── en.lang            # English strings
│       └── ru.lang            # Russian strings
└── lang/
    ├── en.lang                # English log messages
    └── ru.lang                # Russian log messages
```
---

## 🐳 Docker & Portainer Deployment

This is the recommended way to run the miner headlessly – great for home servers, NAS devices, or any machine running **Portainer**.

### Prerequisites
* [Docker](https://docs.docker.com/get-docker/) installed (Desktop or Engine).
* A working `config.json` (copy `config.example.json` and edit it first).

---

### Option 1 – Docker CLI (quick)

```bash
# 1. Build the image (run from the project root)
docker build -t kick-channel-points-miner .

# 2. Start the container
docker run -d \
  --name kick-miner \
  --restart unless-stopped \
  -v "$(pwd)/config.json:/app/config.json:ro" \
  -p 5000:5000 \
  kick-channel-points-miner
```

Dashboard → **http://localhost:5000**

---

### Option 2 – Docker Compose

```bash
# Make sure config.json is in the same folder as docker-compose.yml
docker compose up -d
```

To stop: `docker compose down`  
View logs: `docker compose logs -f`

---

### Option 3 – Portainer (GUI, beginner-friendly)

1. Open Portainer and select your environment.
2. Go to **Stacks → Add stack**.
3. Give it a name (e.g. `kick-miner`).
4. Paste the contents of `docker-compose.yml` into the **Web editor**.
5. Scroll down to **Env variables** – no extras needed.
6. Before deploying, make sure `config.json` is on the host where Docker runs.
   Edit the `volumes` line in the compose to use the **absolute path** on your host:
   ```yaml
   volumes:
     - /home/youruser/kick-miner/config.json:/app/config.json:ro
   ```
7. Click **Deploy the stack**.
8. Once running, open `http://<your-server-ip>:5000` to see the Dashboard.

> **Tip:** Portainer will auto-restart the container on crash or server reboot thanks to `restart: unless-stopped`.

---

### Project Structure (with Docker files)

```
Kick_Channel_Points_Miner/
├── Dockerfile             # Container build instructions
├── docker-compose.yml     # Compose file for Docker / Portainer
├── .dockerignore          # Excludes config.json and dev files from image
├── config.json            # ← Created by you (bind-mounted, not baked in)
└── ...
```

> **Security note:** `config.json` is **never baked into the image**. It is always bind-mounted at runtime so your tokens stay on your host machine only.

---

## ⚠️ Disclaimer

This software is for educational purposes only. Use it at your own risk. The developer is not responsible for any bans or account restrictions on Kick.com.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
