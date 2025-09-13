import random
import time
import math
import os
import glob
import shutil
import gc
import psutil
from vars import CREDIT
from pyrogram.errors import FloodWait
from datetime import datetime, timedelta

# Render Free Tier Memory Management
class RenderMemoryManager:
    def __init__(self, max_memory_mb=400):  # 400MB limit for safety (Render has 512MB)
        self.max_memory_mb = max_memory_mb
        
    def get_memory_usage(self):
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except:
            return 0
    
    def is_memory_safe(self):
        """Check if memory usage is safe for aggressive downloads"""
        current_memory = self.get_memory_usage()
        return current_memory < self.max_memory_mb
    
    def force_cleanup(self):
        """Aggressive memory cleanup for Render"""
        try:
            gc.collect()
            # Clear temp files
            import tempfile
            temp_dirs = ["/tmp", tempfile.gettempdir()]
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for f in glob.glob(os.path.join(temp_dir, "yt-dlp*")):
                        try:
                            os.remove(f)
                        except:
                            pass
            print(f"🧹 Memory cleanup: {self.get_memory_usage():.1f}MB")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

# Global memory manager
render_memory = RenderMemoryManager()

def get_render_aggressive_ydl_opts(output_path: str):
    """Get aggressive yt-dlp options optimized for Render free tier"""
    
    # Base aggressive settings
    base_opts = {
        'format': 'best[height<=1080][filesize<100M]/best[height<=720]/best',  # Increased limits for better quality/speed
        'outtmpl': output_path,
        'no_warnings': True,
        'extract_flat': False,
        'writethumbnail': False,
        'writeinfojson': False,
        'ignoreerrors': True,
        # Enhanced download settings for maximum speed
        'http_chunk_size': 16777216,  # 16MB chunks for much faster downloads (doubled)
        'fragment_retries': 25,       # More retries for reliability
        'retries': 15,
        'concurrent_fragments': 20,   # Increased concurrent fragments for faster speed
        # Memory optimization
        'buffersize': 65536,         # 64KB buffer
        'socket_timeout': 20,
        'default_search': 'auto',
        # Speed optimizations
        'prefer_ffmpeg': False,      # Use native downloaders when possible
        'keepvideo': False,          # Don't keep original files
        'noplaylist': True,
    }
    
    # Use built-in downloader for reliability
    print("🚀 Using optimized built-in downloader for stability")
        
    return base_opts

def detect_hls_stream(url: str) -> bool:
    """
    Properly detect HLS/live streams using yt-dlp extraction
    
    Args:
        url: The video URL to check
        
    Returns:
        bool: True if HLS/live stream, False otherwise
    """
    try:
        import yt_dlp
        # Quick URL-based check first for obvious cases
        if '.m3u8' in url.lower() or 'm3u8' in url.lower():
            return True
            
        # Use yt-dlp to properly detect stream type
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                # Check if it's a live stream or has HLS protocol
                if info.get('is_live', False):
                    return True
                    
                # Check formats for HLS/m3u8 protocols
                formats = info.get('formats', [])
                for fmt in formats:
                    protocol = fmt.get('protocol', '').lower()
                    url_fmt = fmt.get('url', '').lower()
                    if ('m3u8' in protocol or 'hls' in protocol or 
                        'm3u8' in url_fmt or 'hls' in url_fmt):
                        return True
            except:
                pass  # If extraction fails, fall back to URL check
    except ImportError:
        pass
    
    # Fallback to basic URL pattern matching
    return ('.m3u8' in url.lower() or 'm3u8' in url.lower() or 
            'live' in url.lower() or 'livestream' in url.lower())

def build_ydl_opts(url: str, output_path: str, is_live: bool = None, user_id: int = None):
    """
    Centralized yt-dlp options builder that handles both regular downloads and HLS/live streams
    
    Args:
        url: The video URL to download
        output_path: Output file path template
        is_live: Optional override to force live stream handling
        user_id: User ID for retrieving platform-specific authentication tokens
        
    Returns:
        dict: Optimized yt-dlp options based on stream type with authentication
    """
    import shutil
    
    # Auto-detect HLS/live streams if not specified
    if is_live is None:
        is_live = detect_hls_stream(url)
    
    # Base options that apply to all downloads
    base_opts = {
        'outtmpl': output_path,
        'no_warnings': True,
        'extract_flat': False,
        'writethumbnail': False,
        'writeinfojson': False,
        'ignoreerrors': True,
        'retries': 15,
        'fragment_retries': 25,
        'socket_timeout': 20,
        'noplaylist': True,
        'keepvideo': False,
    }
    
    if is_live:
        # HLS/Live stream configuration - DEFAULT: ffmpeg with hls-use-mpegts
        print("🔴 Detected HLS/Live stream - Using ffmpeg downloader with MPEG-TS (DEFAULT)")
        base_opts.update({
            'format': 'best[height<=720]/best[height<=480]/best',
            # FORCE ffmpeg downloader for HLS streams (as requested)
            'external_downloader': 'ffmpeg',
            'external_downloader_args': {
                'ffmpeg': ['--hls-use-mpegts']  # DEFAULT: Use MPEG-TS for HLS
            },
            'hls_prefer_native': False,     # Don't use native HLS downloader
            'hls_use_mpegts': True,         # Use MPEG-TS segments for live streams
            'prefer_ffmpeg': True,          # Prefer ffmpeg over native downloaders
            'concurrent_fragments': 2,      # Further reduced to prevent disk quota issues
            'http_chunk_size': 2097152,     # 2MB chunks for live streams
            'buffersize': 32768,            # 32KB buffer for live
        })
    else:
        # Regular download configuration - DEFAULT: built-in downloader
        print("📥 Regular download - Using built-in downloader (DEFAULT)")
        base_opts.update({
            'format': 'best[height<=720][filesize<50M]/best[height<=480]/best',
            'concurrent_fragments': 2,      # Further reduced to prevent disk quota issues
            'http_chunk_size': 4194304,     # 4MB chunks
            'buffersize': 32768,            # 32KB buffer
        })
    
    # ========================================
    # AUTHENTICATION TOKEN INTEGRATION
    # ========================================
    
    # Apply platform-specific authentication if user_id provided
    if user_id:
        try:
            # Import token manager
            from modules.ott_downloader import ott_token_manager
            
            # Detect platform and apply authentication
            platform_configs = {
                'hotstar.com': ('hotstar', 'Authorization', 'Bearer {}'),
                'jiocinema.com': ('hotstar', 'Authorization', 'Bearer {}'),  # Hotstar/Jio integration
                'netflix.com': ('netflix', 'Authorization', 'Bearer {}'),
                'primevideo.com': ('amazon', 'X-Amzn-Authorization', 'AWS4-HMAC-SHA256 {}'),
                'disneyplus.com': ('disney', 'Authorization', 'Bearer {}'),
                'zee5.com': ('zee5', 'X-Access-Token', '{}'),
                'voot.com': ('voot', 'accesstoken', '{}')
            }
            
            # Check if URL matches any supported platform
            for domain, (platform, header_name, header_format) in platform_configs.items():
                if domain in url.lower():
                    # Get stored token for this platform
                    platform_tokens = getattr(ott_token_manager, f"{platform}_tokens", {})
                    user_token = platform_tokens.get(user_id)
                    
                    if user_token:
                        print(f"🔐 Found {platform.upper()} authentication token for user {user_id}")
                        
                        # Add authentication headers
                        if 'http_headers' not in base_opts:
                            base_opts['http_headers'] = {}
                        
                        # Apply token as HTTP header
                        if '{}' in header_format:
                            base_opts['http_headers'][header_name] = header_format.format(user_token)
                        else:
                            base_opts['http_headers'][header_name] = user_token
                        
                        # Add additional headers for better authentication
                        base_opts['http_headers'].update({
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Accept': 'application/json, text/plain, */*',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache'
                        })
                        
                        # Platform-specific configurations
                        if platform == 'hotstar':
                            # Hotstar-specific optimizations
                            base_opts['http_headers'].update({
                                'X-Country-Code': 'IN',
                                'X-Platform': 'web',
                                'X-API-Client': 'web'
                            })
                            print("🎭 Applied Hotstar-specific authentication headers")
                        
                        break
                    else:
                        print(f"⚠️ No {platform.upper()} token found for user {user_id}")
                        
        except ImportError:
            print("⚠️ Token manager not available - proceeding without authentication")
        except Exception as e:
            print(f"⚠️ Authentication setup failed: {str(e)}")
    
    return base_opts

# Removed build_aria2c_speed_opts function - aria2c no longer used

class Timer:
    def __init__(self, time_between=5):
        self.start_time = time.time()
        self.time_between = time_between

    def can_send(self):
        if time.time() > (self.start_time + self.time_between):
            self.start_time = time.time()
            return True
        return False

# lets do calculations
def hrb(value, digits=2, delim="", postfix=""):
    """Return a human-readable file size.
    """
    if value is None:
        return None
    chosen_unit = "B"
    for unit in ("KB", "MB", "GB", "TB"):
        if value > 1000:
            value /= 1024
            chosen_unit = unit
        else:
            break
    return f"{value:.{digits}f}" + delim + chosen_unit + postfix

def hrt(seconds, precision=0):
    """Return a human-readable time delta as a string.
    """
    pieces = []
    value = timedelta(seconds=seconds)

    if value.days:
        pieces.append(f"{value.days}day")

    seconds = value.seconds

    if seconds >= 3600:
        hours = int(seconds / 3600)
        pieces.append(f"{hours}hr")
        seconds -= hours * 3600

    if seconds >= 60:
        minutes = int(seconds / 60)
        pieces.append(f"{minutes}min")
        seconds -= minutes * 60

    if seconds > 0 or not pieces:
        pieces.append(f"{seconds}sec")

    if not precision:
        return "".join(pieces)

    return "".join(pieces[:precision])

timer = Timer()

async def progress_bar(current, total, reply, start):
    if timer.can_send():
        now = time.time()
        diff = now - start
        if diff < 2:  # Increased from 1 to 2 seconds for faster uploads
            return
        else:
            perc = f"{current * 100 / total:.1f}%"
            elapsed_time = round(diff)
            speed = current / elapsed_time
            remaining_bytes = total - current
            if speed > 0:
                eta_seconds = remaining_bytes / speed
                eta = hrt(eta_seconds, precision=1)
            else:
                eta = "-"
            sp = str(hrb(speed)) + "/s"
            tot = hrb(total)
            cur = hrb(current)
            bar_length = 10
            completed_length = int(current * bar_length / total)
            remaining_length = bar_length - completed_length

            symbol_pairs = [
                ("🟩", "⬜")
            ]
            chosen_pair = random.choice(symbol_pairs)
            completed_symbol, remaining_symbol = chosen_pair

            progress_bar = completed_symbol * completed_length + remaining_symbol * remaining_length

            try:
                await reply.edit(f'<blockquote>`╭──⌯═════𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐢𝐜𝐬══════⌯──╮\n├⚡ {progress_bar}\n├⚙️ Progress ➤ | {perc} |\n├🚀 Speed ➤ | {sp} |\n├📟 Processed ➤ | {cur} |\n├🧲 Size ➤ | {tot} |\n├🕑 ETA ➤ | {eta} |\n╰─═══✨🦋{CREDIT}🦋✨═══─╯`</blockquote>')
            except FloodWait as e:
                time.sleep(e.x)

def cleanup_temp_files(cleanup_type="initial"):
    """
    Ultra-robust cleanup function to remove all temporary files and assets.
    
    Args:
        cleanup_type (str): "initial" for pre-download cleanup, "final" for post-download cleanup
    
    Returns:
        int: Number of files cleaned
    """
    # Import globals to check processing state
    try:
        from . import globals
        # Prevent cleanup during active processing unless it's final cleanup
        if cleanup_type == "initial" and globals.processing_request:
            print("⏸️ Skipping cleanup - post-processing still in progress")
            return 0
    except ImportError:
        # If globals not available, proceed with cleanup
        pass
    # Comprehensive file patterns for all possible temporary files
    cleanup_patterns = [
        # Video formats
        "*.mp4", "*.mkv", "*.avi", "*.mov", "*.wmv", "*.flv", "*.webm", "*.m4v", "*.3gp", "*.ogv",
        
        # Audio formats  
        "*.mp3", "*.wav", "*.flac", "*.aac", "*.ogg", "*.m4a", "*.wma", "*.opus", "*.aiff",
        
        # Document formats
        "*.pdf", "*.doc", "*.docx", "*.txt", "*.rtf", "*.odt", "*.epub", "*.mobi",
        
        # Image formats
        "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.tiff", "*.svg", "*.ico", "*.webp",
        
        # Archive formats
        "*.zip", "*.rar", "*.7z", "*.tar", "*.gz", "*.bz2", "*.xz", "*.tar.gz", "*.tar.bz2",
        
        # Web formats
        "*.html", "*.htm", "*.css", "*.js", "*.json", "*.xml", "*.rss",
        
        # Temporary file patterns
        "*.tmp", "*.temp", "*.temporary", "*.cache", "*.log", "*.bak", "*.backup",
        "*.part", "*.partial", "*.download", "*.downloading", "*.crdownload",
        "*.temp.*", "*.tmp.*", "*temp*", "*tmp*", "*cache*", "*backup*",
        "*.temp.mp4", "*.temp.mkv", "*.temp.avi", "*.temp.webm",
        
        # Thumbnails and previews
        "thumb.*", "thumbnail.*", "preview.*", "*.thumb", "*.thumbnail", "*.preview",
        
        # Session and database temp files
        "*.session-journal", "*.db-journal", "*.sqlite-journal", "*.lock",
        
        # Media processing temp files
        "*.ytdl", "*.f4v", "*.f4a", "*.m3u8", "*.ts", "*.vtt", "*.srt", "*.ass", "*.X",
        
        # System temp files
        "*.pyc", "*.pyo", "*.pyd", "__pycache__/*", ".DS_Store", "Thumbs.db"
    ]
    
    # Directories to clean completely
    cleanup_dirs = [
        "downloads",
        "temp", 
        "tmp",
        "cache",
        "__pycache__",
        ".temp",
        "attached_assets"  # Clean attached assets as requested
    ]
    
    cleaned_files = []
    
    # Clean files in current directory using patterns
    for pattern in cleanup_patterns:
        if "/" not in pattern and "*" in pattern:  # Pattern-based cleanup
            for file_path in glob.glob(pattern):
                try:
                    if os.path.isfile(file_path):
                        # Preserve active bot session files
                        if "bot.session" in file_path and "journal" not in file_path:
                            continue
                        # Preserve youtube cookies and core config files
                        if file_path in ["youtube_cookies.txt", "vars.py", "main.py", "app.py"]:
                            continue
                            
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                except Exception:
                    continue
        elif "/" not in pattern and "*" not in pattern:  # Specific file cleanup
            try:
                if os.path.isfile(pattern):
                    os.remove(pattern)
                    cleaned_files.append(pattern)
            except Exception:
                continue
    
    # Clean directories completely
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            try:
                # Remove all files in directory
                for root, dirs, files in os.walk(dir_name):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            cleaned_files.append(file_path)
                        except Exception:
                            continue
                    
                    # Remove empty subdirectories
                    for dir_path in dirs:
                        full_dir_path = os.path.join(root, dir_path)
                        try:
                            if not os.listdir(full_dir_path):  # If directory is empty
                                os.rmdir(full_dir_path)
                        except Exception:
                            continue
                            
            except Exception:
                pass
    
    # Clean any orphaned session files (except main bot session)
    session_patterns = ["*.session*", "device_*", "*.db-*"]
    for pattern in session_patterns:
        for file_path in glob.glob(pattern):
            try:
                if (os.path.isfile(file_path) and 
                    "bot.session" not in file_path and 
                    "journal" in file_path):
                    os.remove(file_path)
                    cleaned_files.append(file_path)
            except Exception:
                continue
    
    # Recursive cleanup for hidden temp files
    try:
        for root, dirs, files in os.walk("."):
            for file in files:
                if (file.startswith('.tmp') or 
                    file.startswith('.temp') or 
                    file.endswith('.tmp') or
                    file.endswith('.temp') or
                    'temp' in file.lower() and file != 'youtube_cookies.txt'):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                    except Exception:
                        continue
    except Exception:
        pass
    
    return len(cleaned_files)

def final_cleanup():
    """
    Final cleanup after download completion - more aggressive cleanup
    """
    return cleanup_temp_files(cleanup_type="final")