<h1 align="center">TorrentDriveBot 🚀</h1>

<p align="center">
  <b>An advanced Discord bot that automates torrent downloads and uploads them directly to your Google Drive.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Discord.py-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
  <img src="https://img.shields.io/badge/Google_Drive-4285F4?style=for-the-badge&logo=google-drive&logoColor=white" />
</p>

---

## 📖 About

**TorrentDriveBot** is designed to automate torrent workflows. It helps bypass Google Drive's storage limits by chunking large files and allows you to track the entire process directly via Discord.

---

## ✨ Key Features

- **Direct Download:** Full support for Magnet links and `.torrent` files.
- **Drive Integration:** Transfers files directly to your Drive via API.
- **Auto-Chunking:** Automatically splits files larger than **16GB** to ensure successful uploads.
- **Live Progress:** Real-time download/upload status updates in Discord.
- **Secure:** User-based authentication via OAuth2.

---

# ⚙️ Setup Guide

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
```

</details>

---

# 📦 Installation

Install the required libraries:

```bash
pip install discord.py aiotorrent google-api-python-client google-auth-oauthlib
```

---

# ▶️ Running the Bot

Start the bot with:

```bash
python bot.py
```

---

# ⌨️ Commands

| Command | Description |
|---------|-------------|
| `/login` | Starts the Google Drive authorization process. |
| `/callback <code>` | Links the authorization code to the bot. |
| `/torrent <link>` | Starts the torrent download and uploads it to Google Drive. |
| `/status` | Checks your current Google Drive authorization status. |
| `/logout` | Removes your Google Drive authorization. |

---

## 📄 License

This project is provided for educational and personal use. Make sure you comply with your local laws and the terms of service of any platform you use.
