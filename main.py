import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import json
import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, List
import aiohttp

from aiotorrent import Torrent

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# Configuration
DISCORD_TOKEN = ""
CLIENT_ID = ""
CLIENT_SECRET = ""
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Storage settings
MAX_DISK_SPACE = 3 * 1024 * 1024 * 1024  # 3GB
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB for resumable upload
PART_SIZE = 2 * 1024 * 1024 * 1024  # 2GB for file splitting
LARGE_FILE_THRESHOLD = 16 * 1024 * 1024 * 1024  # 16GB

# File paths
TOKEN_FILE = "user_tokens.json"
TEMP_DIR = "temp_downloads"

# OAuth redirect service - using a public OAuth redirect service
OAUTH_REDIRECT_BASE = "https://oauth.pstmn.io/v1/callback"

class TokenManager:
    """Manages user OAuth tokens with persistence"""
    
    def __init__(self, token_file: str):
        self.token_file = token_file
        self.tokens: Dict[int, dict] = self._load_tokens()
    
    def _load_tokens(self) -> Dict[int, dict]:
        """Load tokens from file"""
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as f:
                return {int(k): v for k, v in json.load(f).items()}
        return {}
    
    def _save_tokens(self):
        """Save tokens to file"""
        with open(self.token_file, 'w') as f:
            json.dump({str(k): v for k, v in self.tokens.items()}, f, indent=2)
    
    def save_token(self, user_id: int, token_data: dict):
        """Save user token"""
        self.tokens[user_id] = token_data
        self._save_tokens()
    
    def get_token(self, user_id: int) -> Optional[dict]:
        """Get user token"""
        return self.tokens.get(user_id)
    
    def remove_token(self, user_id: int):
        """Remove user token"""
        if user_id in self.tokens:
            del self.tokens[user_id]
            self._save_tokens()
    
    def get_all_tokens(self) -> List[dict]:
        """Get all valid tokens for multi-user uploads"""
        return list(self.tokens.values())

class OAuthManager:
    """Handles OAuth flow with manual code entry (no localhost needed)"""
    
    def __init__(self, client_id: str, client_secret: str, scopes: List[str]):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes
        self.pending_flows: Dict[int, Flow] = {}
    
    def create_auth_url(self, user_id: int) -> str:
        """Create OAuth authorization URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.scopes,
            redirect_uri=OAUTH_REDIRECT_BASE
        )
        
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            access_type='offline'
        )
        
        self.pending_flows[user_id] = flow
        return auth_url
    
    async def exchange_code(self, user_id: int, auth_code: str) -> Optional[dict]:
        """Exchange authorization code for tokens"""
        if user_id not in self.pending_flows:
            return None
        
        flow = self.pending_flows[user_id]
        
        try:
            # Exchange code for credentials
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            token_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            del self.pending_flows[user_id]
            return token_data
        except Exception as e:
            if user_id in self.pending_flows:
                del self.pending_flows[user_id]
            raise e

class GoogleDriveManager:
    """Manages Google Drive operations with user OAuth"""
    
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
    
    def _get_credentials(self, user_id: int) -> Optional[Credentials]:
        """Get and refresh user credentials"""
        token_data = self.token_manager.get_token(user_id)
        if not token_data:
            return None
        
        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            scopes=SCOPES
        )
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            self.token_manager.save_token(user_id, {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            })
        
        return creds
    
    async def upload_file(self, user_id: int, file_path: str, file_name: str, 
                         progress_callback=None) -> Optional[str]:
        """Upload file to user's Drive with chunked upload"""
        creds = self._get_credentials(user_id)
        if not creds:
            return None
        
        def _upload():
            service = build('drive', 'v3', credentials=creds)
            
            file_metadata = {'name': file_name}
            media = MediaFileUpload(
                file_path,
                resumable=True,
                chunksize=CHUNK_SIZE
            )
            
            request = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )
            
            response = None
            last_progress = 0
            
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if progress != last_progress and progress_callback:
                        progress_callback(progress)
                        last_progress = progress
            
            return response.get('id')
        
        return await asyncio.to_thread(_upload)
    
    async def upload_large_file_parts(self, file_path: str, file_name: str,
                                     user_tokens: List[dict], progress_callback=None) -> List[str]:
        """Split and upload large files as parts"""
        file_size = os.path.getsize(file_path)
        num_parts = (file_size + PART_SIZE - 1) // PART_SIZE
        part_ids = []
        
        for part_num in range(num_parts):
            part_name = f"{file_name}.part{part_num + 1:03d}"
            part_path = f"{file_path}.part{part_num + 1:03d}"
            
            # Create part file
            await asyncio.to_thread(self._create_part_file, file_path, part_path, 
                                   part_num, PART_SIZE)
            
            try:
                # Round-robin through available tokens
                token_idx = part_num % len(user_tokens)
                user_id = list(self.token_manager.tokens.keys())[token_idx]
                
                if progress_callback:
                    progress_callback(f"Uploading part {part_num + 1}/{num_parts}...")
                
                file_id = await self.upload_file(user_id, part_path, part_name, 
                                                progress_callback)
                if file_id:
                    part_ids.append(file_id)
            finally:
                # Clean up part file
                if os.path.exists(part_path):
                    os.remove(part_path)
        
        return part_ids
    
    def _create_part_file(self, source_path: str, part_path: str, 
                         part_num: int, part_size: int):
        """Create a part file using buffered reading"""
        offset = part_num * part_size
        
        with open(source_path, 'rb') as source:
            source.seek(offset)
            with open(part_path, 'wb') as part:
                remaining = part_size
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    chunk = source.read(chunk_size)
                    if not chunk:
                        break
                    part.write(chunk)
                    remaining -= len(chunk)

class AsyncTorrentDownloader:
    """Pure Python async torrent downloader using aiotorrent"""
    
    def __init__(self, temp_dir: str):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        self.active_downloads: Dict[str, Torrent] = {}
    
    async def download_torrent(self, magnet_or_file: str, is_file: bool = False,
                              progress_callback=None) -> Optional[str]:
        """Download torrent and return path to downloaded file/folder"""
        session_id = str(uuid.uuid4())
        download_dir = self.temp_dir / session_id
        download_dir.mkdir(exist_ok=True)
        
        try:
            if progress_callback:
                await progress_callback("Initializing torrent download...")
            
            # Create torrent instance
            if is_file:
                # Add torrent from file
                torrent = Torrent(magnet="MAGNET_LINK")  # Magnet ile
                await torrent.download_all()
            else:
                # Add torrent from magnet link
                torrent = Torrent(torrent_file="dosya.torrent")
                await torrent.download_all()
            
            self.active_downloads[session_id] = torrent
            
            if progress_callback:
                await progress_callback(f"Downloading: {torrent.name}")
            
            # Create progress monitoring task
            monitor_task = asyncio.create_task(
                self._monitor_progress(session_id, torrent, progress_callback)
            )
            
            # Download all files
            try:
                for file in torrent.files:
                    file_path = download_dir / file.name
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    await torrent.download(file, str(file_path))
                
                if progress_callback:
                    await progress_callback("Download complete!")
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            if session_id in self.active_downloads:
                del self.active_downloads[session_id]
            
            # Return path to downloaded content
            downloaded_items = list(download_dir.iterdir())
            if not downloaded_items:
                raise Exception("No files downloaded")
            
            if len(downloaded_items) == 1:
                return str(downloaded_items[0])
            else:
                return str(download_dir)
        
        except Exception as e:
            if session_id in self.active_downloads:
                del self.active_downloads[session_id]
            if download_dir.exists():
                shutil.rmtree(download_dir)
            raise e
    
    async def _monitor_progress(self, session_id: str, torrent: Torrent, 
                               progress_callback):
        """Monitor download progress"""
        last_progress = 0
        
        while session_id in self.active_downloads:
            try:
                if torrent.files:
                    total_size = sum(f.size for f in torrent.files)
                    downloaded = sum(f.get_bytes_downloaded() for f in torrent.files)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        
                        if abs(progress - last_progress) >= 1:
                            if progress_callback:
                                await progress_callback(
                                    f"Progress: {progress:.1f}% "
                                    f"({downloaded / 1024 / 1024:.1f}MB / "
                                    f"{total_size / 1024 / 1024:.1f}MB)"
                                )
                            last_progress = progress
            except Exception:
                pass
            
            await asyncio.sleep(2)

class TorrentDriveBot(commands.Bot):
    """Main Discord bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.token_manager = TokenManager(TOKEN_FILE)
        self.drive_manager = GoogleDriveManager(self.token_manager)
        self.torrent_downloader = AsyncTorrentDownloader(TEMP_DIR)
        self.oauth_manager = OAuthManager(CLIENT_ID, CLIENT_SECRET, SCOPES)
    
    async def setup_hook(self):
        await self.tree.sync()
        print(f"Bot ready! Logged in as {self.user}")

bot = TorrentDriveBot()

@bot.tree.command(name="login", description="Authorize bot to access your Google Drive")
async def login(interaction: discord.Interaction):
    """Start OAuth flow for user"""
    user_id = interaction.user.id
    
    # Create OAuth URL
    auth_url = bot.oauth_manager.create_auth_url(user_id)
    
    embed = discord.Embed(
        title="🔐 Google Drive Authorization",
        description="Follow these steps to authorize the bot:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Step 1: Authorize",
        value=f"[Click here to authorize]({auth_url})",
        inline=False
    )
    embed.add_field(
        name="Step 2: Copy the Code",
        value="After authorizing, you'll be redirected to a page. Copy the **entire URL** from your browser's address bar.",
        inline=False
    )
    embed.add_field(
        name="Step 3: Submit Code",
        value="Use `/callback <code>` and paste the full URL (or just the code parameter).",
        inline=False
    )
    embed.set_footer(text="The URL will look like: https://...callback?code=YOUR_CODE_HERE")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="callback", description="Complete OAuth with the authorization code")
@app_commands.describe(code="The full callback URL or just the code from Google")
async def callback(interaction: discord.Interaction, code: str):
    """Handle OAuth callback"""
    user_id = interaction.user.id
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Extract code from URL if user pasted the full URL
        if "code=" in code:
            code = code.split("code=")[1].split("&")[0]
        
        # Exchange code for tokens
        token_data = await bot.oauth_manager.exchange_code(user_id, code)
        
        if not token_data:
            await interaction.followup.send(
                "❌ No pending authorization found. Please use `/login` first.",
                ephemeral=True
            )
            return
        
        bot.token_manager.save_token(user_id, token_data)
        
        await interaction.followup.send(
            "✅ Successfully authorized! You can now use `/torrent` to upload torrents to your Drive.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Authorization failed: {str(e)}\n\nMake sure you copied the full URL or code correctly.",
            ephemeral=True
        )

@bot.tree.command(name="torrent", description="Download torrent and upload to Google Drive")
@app_commands.describe(
    magnet="Magnet link",
    file="Torrent file attachment"
)
async def torrent(interaction: discord.Interaction, magnet: Optional[str] = None,
                 file: Optional[discord.Attachment] = None):
    """Handle torrent download and upload"""
    user_id = interaction.user.id
    
    # Check authorization
    if not bot.token_manager.get_token(user_id):
        await interaction.response.send_message(
            "❌ Please authorize first using `/login`",
            ephemeral=True
        )
        return
    
    if not magnet and not file:
        await interaction.response.send_message(
            "❌ Please provide either a magnet link or torrent file",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    progress_msg = None
    temp_file = None
    download_path = None
    
    try:
        async def update_progress(msg: str):
            nonlocal progress_msg
            if progress_msg is None:
                progress_msg = await interaction.followup.send(f"⏳ {msg}")
            else:
                await progress_msg.edit(content=f"⏳ {msg}")
        
        # Download torrent
        if file:
            temp_file = f"{TEMP_DIR}/{uuid.uuid4()}.torrent"
            await file.save(temp_file)
            download_path = await bot.torrent_downloader.download_torrent(
                temp_file, is_file=True, progress_callback=update_progress
            )
        else:
            download_path = await bot.torrent_downloader.download_torrent(
                magnet, is_file=False, progress_callback=update_progress
            )
        
        if not download_path:
            await update_progress("❌ Download failed")
            return
        
        # Check if it's a file or directory
        if os.path.isfile(download_path):
            file_size = os.path.getsize(download_path)
            file_name = os.path.basename(download_path)
            files_to_upload = [(download_path, file_name, file_size)]
        else:
            files_to_upload = []
            for root, dirs, files in os.walk(download_path):
                for f in files:
                    file_path = os.path.join(root, f)
                    rel_path = os.path.relpath(file_path, download_path)
                    file_size = os.path.getsize(file_path)
                    files_to_upload.append((file_path, rel_path, file_size))
        
        total_size = sum(size for _, _, size in files_to_upload)
        
        await update_progress(
            f"📤 Uploading {len(files_to_upload)} file(s) ({total_size / 1024**3:.2f}GB) to Google Drive..."
        )
        
        # Upload files
        uploaded_count = 0
        for file_path, file_name, file_size in files_to_upload:
            if file_size > LARGE_FILE_THRESHOLD:
                await update_progress(
                    f"📤 File {file_name} is {file_size / 1024**3:.2f}GB. Splitting into parts..."
                )
                
                all_tokens = bot.token_manager.get_all_tokens()
                if not all_tokens:
                    await update_progress("❌ No authorized users available for upload")
                    return
                
                part_ids = await bot.drive_manager.upload_large_file_parts(
                    file_path, file_name, all_tokens, update_progress
                )
                uploaded_count += len(part_ids)
            else:
                file_id = await bot.drive_manager.upload_file(
                    user_id, file_path, file_name,
                    lambda p: asyncio.create_task(update_progress(f"📤 Uploading {file_name}: {p}%"))
                )
                if file_id:
                    uploaded_count += 1
        
        await update_progress(
            f"✅ Successfully uploaded {uploaded_count} file(s) to Google Drive!\n"
            f"Total size: {total_size / 1024**3:.2f}GB"
        )
    
    except Exception as e:
        if progress_msg:
            await progress_msg.edit(content=f"❌ Error: {str(e)}")
        else:
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    finally:
        # Clean up temporary files
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        
        if download_path:
            if os.path.isfile(download_path):
                parent_dir = os.path.dirname(download_path)
            else:
                parent_dir = download_path
            
            if parent_dir.startswith(TEMP_DIR) and os.path.exists(parent_dir):
                shutil.rmtree(parent_dir)

@bot.tree.command(name="logout", description="Remove your Google Drive authorization")
async def logout(interaction: discord.Interaction):
    """Remove user authorization"""
    user_id = interaction.user.id
    bot.token_manager.remove_token(user_id)
    await interaction.response.send_message(
        "✅ Successfully logged out. Your authorization has been removed.",
        ephemeral=True
    )

@bot.tree.command(name="status", description="Check your authorization status")
async def status(interaction: discord.Interaction):
    """Check authorization status"""
    user_id = interaction.user.id
    token = bot.token_manager.get_token(user_id)
    
    if token:
        await interaction.response.send_message(
            "✅ You are authorized! You can use `/torrent` to upload files.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ Not authorized. Use `/login` to connect your Google Drive.",
            ephemeral=True
        )

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)