<h1 align="center">TorrentDriveBot <img src="https://cdn.jsdelivr.net/npm/lucide-static/icons/rocket.svg" width="32" height="32" align="center" /></h1>

<p align="center">
  <b>Torrent to Google Drive: A smart discord bot to automatically download torrens and upload it directly to your Google Drive</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Discord.py-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
  <img src="https://img.shields.io/badge/Google_Drive-4285F4?style=for-the-badge&logo=google-drive&logoColor=white" />
</p>

---

## <img src="https://cdn.jsdelivr.net/npm/lucide-static/icons/book-open.svg" width="24" height="24" align="center" /> About

This bot is intended to be used for a torrent-ing system. To get around Google Drive's size restrictions, it splits up files and allows for direct viewing of the progress in discord.

---

## <img src="https://cdn.jsdelivr.net/npm/lucide-static/icons/sparkles.svg" width="24" height="24" align="center" /> Key Features

-Direct Download : We support magnet link, and also support download through .torrent files directly.
-Drive Integrations : Files will be directly uploaded into your drive using official Drive API.
-Auto-Chunking : Automatically chunk any files which are bigger than 16GB in order to upload successfully.
-Live Progress : Monitor download/upload live status in Discord.
-Secure : User authentication through OAuth2.

---

# <img src="https://cdn.jsdelivr.net/npm/lucide-static/icons/settings.svg" width="28" height="28" align="center" /> Setup Guide

<details>
<summary><b>1. Google Drive API Setup</b></summary>
<br>

1. Go to the **Google Cloud Console** and create a new project.
2. Enable the **Google Drive API** under **APIs & Services**.
3. Configure the **OAuth consent screen**.
4. Create an **OAuth 2.0 Client ID** (Application type: **Desktop App**).
5. Save your **Client ID** and **Client Secret** securely.

</details>

<details>
<summary><b>2. Discord Bot Setup</b></summary>
<br>

1. Go to the **Discord Developer Portal**.
2. Create a new application and obtain your bot token from the **Bot** tab.
3. Enable the **Message Content Intent** under **Privileged Gateway Intents**.

</details>

<details>
<summary><b>3. Configuration</b></summary>
<br>

Fill in the placeholders at the top of your code:

```python
DISCORD_TOKEN = "YOUR_BOT_TOKEN_HERE"
CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"

# 📦 Installation

Install the required libraries:

```bash
pip install discord.py aiotorrent google-api-python-client google-auth-oauthlib
```

---

# Running the Bot

Start the bot with:

```bash
python bot.py
```

---

# Commands

| Command | Description |
|---------|-------------|
| `/login` | Starts the Google Drive authorization process. |
| `/callback <code>` | Links the authorization code to the bot. |
| `/torrent <link>` | Starts the torrent download and uploads it to Google Drive. |
| `/status` | Checks your current Google Drive authorization status. |
| `/logout` | Removes your Google Drive authorization. |

---

## License

You can use this project freely as long as you follow local laws and the platform's terms of use.

<br>
<hr>
<p align="center">
  <small>Made with 🤍 by <a href="https://github.com/yamanist0">yamanist</a></small>
</p>
