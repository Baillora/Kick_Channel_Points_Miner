# 🟢 Kick Channel Points Miner

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> [🇷🇺 **Читать на русском языке**](README_RU.md)

A powerful, asynchronous bot for automatically farming channel points on **Kick.com**. Features a modern Web Dashboard, advanced Telegram control, and Cloudflare protection bypass.

---

## ✨ Features

*   **⚡ Multi-Channel Support:** Farms points on multiple channels simultaneously.
*   **🛡️ Cloudflare Bypass:** Built-in utilities to handle protection and keep connections alive.
*   **🖥️ Web Dashboard:** Beautiful Flask-based interface to monitor progress in your browser.
*   **📱 Telegram Bot:**
    *   **Owner/Guest System:** Owner has full control, guests can only view status.
    *   **Live Notifications:** Updates on points farmed and errors.
    *   **Remote Control:** Restart the miner via Telegram.
*   **🌐 Multi-language:** Support for English and Russian.
*   **📉 Smart Logging:** Clean console output with optional Debug mode.

---

## 🚀 Installation

1.  **Clone or Download** the repository.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure**: Rename `config.example.json` to `config.json` (or create one) and fill it out.

---

## ⚙️ Configuration (`config.json`)

Here is a complete example of the configuration file:

```json
{
  "Language": "en",
  "Debug": false,
  "WebDashboard": {
    "enabled": true,
    "port": 5000
  },
  "Telegram": {
    "enabled": true,
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "chat_id": "YOUR_TELEGRAM_USER_ID",
    "allowed_users": [
        123456789
    ]
  },
  "Private": {
    "token": "YOUR_KICK_TOKEN_OR_COOKIE_STRING"
  },
  "Streamers": [
    "stream1",
    "stream2",
    "stream3"
  ]
}
```

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
*   **`Private`**:
    *   `token`: Your authentication token from Kick (usually found in browser cookies or local storage).
*   **`Streamers`**: List of channel slugs (names from the URL) to farm.

---

## 🎮 Usage

Run the miner:
```bash
python main.py
```

### 📱 Telegram Commands

| Command | Description | Permission |
| :--- | :--- | :--- |
| `/start` | Initialize the bot and keyboard | Everyone |
| `/status` | View active streamers and uptime | Everyone |
| `/balance` | Check farmed points for all channels | Everyone |
| `/help` | Show available commands | Everyone |
| `/restart` | **Restart the miner process** | **Owner Only** |
| `/language` | Change bot language (`en`/`ru`) | **Owner Only** |

---

## 🖥️ Web Dashboard

If enabled, visit **`http://localhost:5000`** in your browser.
You will see a real-time table with:
*   Active Streamers
*   Current Balance
*   Last Update Time
*   Connection Status

---

## ⚠️ Disclaimer

This software is for educational purposes only. Use it at your own risk. The developer is not responsible for any bans or account restrictions on Kick.com.
