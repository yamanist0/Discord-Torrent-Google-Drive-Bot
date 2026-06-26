# TorrentDriveBot

TorrentDriveBot is an advanced Discord bot that allows you to transfer torrent files and magnet links directly to your Google Drive account. With its automatic file chunking feature, it helps you bypass Drive's storage limits for large files.

## 🚀 Features
- **Direct Download:** Full support for Magnet links and .torrent files.
- **Drive Integration:** Saves files directly to your Google Drive via API.
- **Auto-Chunking:** Automatically splits files larger than 16GB to ensure successful uploads.
- **Live Tracking:** Displays download and upload progress percentages directly in Discord.
- **Secure:** User-based authentication via OAuth2.

## ⚙️ Setup & Prerequisites

### 1. Google Drive API Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2. Enable the **Google Drive API** from the "APIs & Services" menu.
3. Configure the "OAuth consent screen".
4. Create an **OAuth 2.0 Client ID** (select "Desktop App" as the application type) in the "Credentials" tab.
5. Save your `Client ID` and `Client Secret`.

### 2. Discord Bot Setup
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new application and obtain your **Token** from the "Bot" tab.
3. Enable the **Message Content Intent** under the "Privileged Gateway Intents" section.

### 3. Configuration
Fill in the placeholders in your code with your credentials:

```python
DISCORD_TOKEN = "YOUR_BOT_TOKEN_HERE"
CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
