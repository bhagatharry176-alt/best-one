# ENHANCED YOUTUBE DOWNLOADER WITH EMBEDDED LINK SUPPORT
# ======================================================
# Complete solution for downloading embedded YouTube videos and improving the bot

import yt_dlp
import re
import requests
import json
import asyncio
import aiohttp
import os
import subprocess
import time
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class EnhancedYouTubeDownloader:
    """
    ENHANCED YOUTUBE DOWNLOADER WITH EMBEDDED LINK SUPPORT
    =====================================================
    
    Features:
    - Extracts embedded YouTube videos from any website
    - Handles all YouTube URL formats (embedded, shorts, regular)
    - Advanced error handling and retry mechanisms
    - Multiple extraction methods as fallbacks
    - High-speed downloads with optimization
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Enhanced yt-dlp options for better extraction
        self.ytdl_opts = {
            'quiet': False,
            'no_warnings': False,
            'extractaudio': False,
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'merge_output_format': 'mp4',
            'writesubtitles': False,
            'writeautomaticsub': False,
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 10,
            'http_chunk_size': 2097152,  # 2MB chunks for Railway optimization
            'concurrent_fragments': 6,   # Optimized for Railway bandwidth
            'extractor_retries': 3,
            'retry_sleep_functions': {
                'http': lambda n: min(4 ** n, 60),
                'fragment': lambda n: min(2 ** n, 30),
                'extractor': lambda n: min(2 ** n, 15)
            },
            # Advanced extraction options
            'youtube_include_dash_manifest': False,  # Faster extraction
            'extract_flat': False,
            'force_json': True,
            'dump_single_json': False,
            'simulate': False,
            'skip_download': False,
            # Error handling
            'ignoreerrors': True,
            'abort_on_unavailable_fragment': False,
            'keep_fragments': False,
        }
    
    def extract_embedded_youtube_urls(self, webpage_url):
        """
        EXTRACT EMBEDDED YOUTUBE URLS FROM ANY WEBPAGE
        ==============================================
        
        Uses multiple methods to find embedded YouTube videos:
        1. Direct iframe src extraction
        2. JavaScript embedded player detection
        3. JSON-LD structured data parsing
        4. Open Graph meta tag parsing
        5. Custom script tag analysis
        """
        
        youtube_urls = []
        
        try:
            logger.info(f"🔍 Analyzing webpage for embedded YouTube videos: {webpage_url}")
            
            # Get webpage content
            response = self.session.get(webpage_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Direct iframe src extraction
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if self._is_youtube_url(src):
                    youtube_id = self._extract_video_id(src)
                    if youtube_id:
                        youtube_urls.append(f"https://www.youtube.com/watch?v={youtube_id}")
            
            # Method 2: JavaScript embedded player detection
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string:
                    # Look for YouTube video IDs in JavaScript
                    video_ids = re.findall(r'["\']?(?:videoId|video_id)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_-]{11})["\']', script.string)
                    for video_id in video_ids:
                        youtube_urls.append(f"https://www.youtube.com/watch?v={video_id}")
                    
                    # Look for embedded YouTube URLs in JavaScript
                    embedded_urls = re.findall(r'["\']?(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^"\'>\s]+)["\']?', script.string)
                    for url in embedded_urls:
                        if self._is_youtube_url(url):
                            youtube_id = self._extract_video_id(url)
                            if youtube_id:
                                youtube_urls.append(f"https://www.youtube.com/watch?v={youtube_id}")
            
            # Method 3: JSON-LD structured data parsing
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Look for VideoObject with YouTube embedUrl
                        if data.get('@type') == 'VideoObject':
                            embed_url = data.get('embedUrl', '')
                            if self._is_youtube_url(embed_url):
                                youtube_id = self._extract_video_id(embed_url)
                                if youtube_id:
                                    youtube_urls.append(f"https://www.youtube.com/watch?v={youtube_id}")
                except json.JSONDecodeError:
                    continue
            
            # Method 4: Open Graph meta tag parsing
            og_video_tags = soup.find_all('meta', property=re.compile(r'og:video'))
            for tag in og_video_tags:
                content = tag.get('content', '')
                if self._is_youtube_url(content):
                    youtube_id = self._extract_video_id(content)
                    if youtube_id:
                        youtube_urls.append(f"https://www.youtube.com/watch?v={youtube_id}")
            
            # Method 5: Custom script tag analysis for specific embed patterns
            all_text = soup.get_text()
            
            # Pattern for Elementor and other page builders
            elementor_patterns = re.findall(r'"youtube_url":"(https?://[^"]+youtube[^"]+)"', all_text)
            for url in elementor_patterns:
                url = url.replace('\\/', '/')  # Fix escaped slashes
                if self._is_youtube_url(url):
                    youtube_id = self._extract_video_id(url)
                    if youtube_id:
                        youtube_urls.append(f"https://www.youtube.com/watch?v={youtube_id}")
            
            # Remove duplicates and return
            unique_urls = list(set(youtube_urls))
            logger.info(f"✅ Found {len(unique_urls)} embedded YouTube videos")
            
            return unique_urls
            
        except Exception as e:
            logger.error(f"❌ Error extracting embedded YouTube URLs: {e}")
            return []
    
    def _is_youtube_url(self, url):
        """Check if URL is a YouTube URL"""
        if not url:
            return False
        
        youtube_domains = [
            'youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be',
            'm.youtube.com', 'music.youtube.com'
        ]
        
        try:
            parsed = urlparse(url)
            return any(domain in parsed.netloc.lower() for domain in youtube_domains)
        except:
            return False
    
    def _extract_video_id(self, url):
        """
        EXTRACT YOUTUBE VIDEO ID FROM ANY URL FORMAT
        ============================================
        
        Supports all YouTube URL formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID
        - And many more variations
        """
        
        if not url:
            return None
        
        # Clean the URL
        url = unquote(url)
        
        # Pattern for various YouTube URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
            r'["\']?(?:videoId|video_id)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_-]{11})["\']',
            r'/(?:embed|v|watch)/([a-zA-Z0-9_-]{11})',
            r'[?&]v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def enhanced_download_with_fallback(self, url, output_path, title="video"):
        """
        ENHANCED DOWNLOAD WITH MULTIPLE FALLBACK METHODS
        ================================================
        
        Uses progressive fallback strategy:
        1. Primary yt-dlp extraction
        2. Alternative format selection
        3. Embedded URL extraction if direct fails
        4. Manual stream URL extraction
        5. Fallback quality options
        """
        
        logger.info(f"🚀 Starting enhanced download: {title}")
        
        # First, determine if this is an embedded link or direct YouTube URL
        if not self._is_youtube_url(url):
            logger.info(f"🔍 Not a direct YouTube URL, extracting embedded videos...")
            embedded_urls = self.extract_embedded_youtube_urls(url)
            
            if not embedded_urls:
                raise Exception("No YouTube videos found on the webpage")
            
            # Use the first found video
            url = embedded_urls[0]
            logger.info(f"✅ Found embedded video: {url}")
        
        # Extract video ID for validation
        video_id = self._extract_video_id(url)
        if not video_id:
            raise Exception("Could not extract video ID from URL")
        
        # Ensure we have a clean YouTube URL
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Progressive download attempts with different options
        download_attempts = [
            # Attempt 1: Best quality with merge
            {
                'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                'merge_output_format': 'mp4',
                'description': 'Best quality (720p max) with audio merge'
            },
            # Attempt 2: Single file format
            {
                'format': 'best[height<=720]',
                'description': 'Single file best quality (720p max)'
            },
            # Attempt 3: Lower quality fallback
            {
                'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                'merge_output_format': 'mp4',
                'description': 'Medium quality (480p max) with audio merge'
            },
            # Attempt 4: Any available format
            {
                'format': 'best',
                'description': 'Any available format'
            }
        ]
        
        for i, attempt in enumerate(download_attempts, 1):
            try:
                logger.info(f"📥 Download attempt {i}: {attempt['description']}")
                
                # Create custom options for this attempt
                opts = self.ytdl_opts.copy()
                opts.update({
                    'format': attempt['format'],
                    'outtmpl': output_path,
                })
                
                if 'merge_output_format' in attempt:
                    opts['merge_output_format'] = attempt['merge_output_format']
                
                # Attempt download
                with yt_dlp.YoutubeDL(opts) as ydl:
                    # First extract info to validate
                    info = ydl.extract_info(clean_url, download=False)
                    
                    if not info:
                        logger.warning(f"⚠️ No video info extracted for attempt {i}")
                        continue
                    
                    # Get video details
                    video_title = info.get('title', title)
                    duration = info.get('duration', 0)
                    view_count = info.get('view_count', 0)
                    
                    logger.info(f"📹 Video: {video_title}")
                    logger.info(f"⏱️ Duration: {duration}s")
                    logger.info(f"👀 Views: {view_count:,}")
                    
                    # Proceed with download
                    ydl.download([clean_url])
                    
                    # Check if file was created
                    if os.path.exists(output_path):
                        logger.info(f"✅ Download successful with method {i}")
                        return {
                            'success': True,
                            'file_path': output_path,
                            'title': video_title,
                            'duration': duration,
                            'view_count': view_count,
                            'method': f"Method {i}: {attempt['description']}",
                            'video_id': video_id
                        }
                
            except Exception as e:
                logger.warning(f"❌ Download attempt {i} failed: {e}")
                continue
        
        # If all attempts failed
        raise Exception("All download attempts failed")
    
    async def get_video_info_only(self, url):
        """
        GET VIDEO INFORMATION WITHOUT DOWNLOADING
        ========================================
        
        Extracts video metadata for preview purposes
        """
        
        try:
            # Handle embedded URLs
            if not self._is_youtube_url(url):
                embedded_urls = self.extract_embedded_youtube_urls(url)
                if embedded_urls:
                    url = embedded_urls[0]
                else:
                    return {'success': False, 'error': 'No YouTube videos found on webpage'}
            
            video_id = self._extract_video_id(url)
            if not video_id:
                return {'success': False, 'error': 'Could not extract video ID'}
            
            clean_url = f"https://www.youtube.com/watch?v={video_id}"
            
            opts = self.ytdl_opts.copy()
            opts.update({
                'skip_download': True,
                'quiet': True,
            })
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                
                if not info:
                    return {'success': False, 'error': 'Could not extract video information'}
                
                # Format available formats
                formats = info.get('formats', [])
                available_formats = []
                for fmt in formats:
                    if fmt.get('height'):
                        available_formats.append(f"{fmt.get('height')}p")
                
                # Remove duplicates and sort
                available_formats = sorted(list(set(available_formats)), key=lambda x: int(x[:-1]), reverse=True)
                
                return {
                    'success': True,
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', '')[:500] + '...' if len(info.get('description', '')) > 500 else info.get('description', ''),
                    'video_id': video_id,
                    'url': clean_url,
                    'available_formats': ', '.join(available_formats) if available_formats else 'Unknown'
                }
                
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {'success': False, 'error': str(e)}
    
    async def batch_extract_from_webpage(self, webpage_url):
        """
        EXTRACT ALL YOUTUBE VIDEOS FROM A WEBPAGE
        ========================================
        
        Returns detailed information about all found videos
        """
        
        try:
            youtube_urls = self.extract_embedded_youtube_urls(webpage_url)
            
            if not youtube_urls:
                return {'success': False, 'error': 'No YouTube videos found on webpage'}
            
            videos_info = []
            
            for i, url in enumerate(youtube_urls, 1):
                try:
                    info = await self.get_video_info_only(url)
                    if info['success']:
                        videos_info.append({
                            'index': i,
                            'title': info['title'],
                            'duration': info['duration'],
                            'url': info['url'],
                            'video_id': info['video_id']
                        })
                except Exception as e:
                    logger.warning(f"Could not get info for video {i}: {e}")
                    continue
            
            return {
                'success': True,
                'total_found': len(youtube_urls),
                'valid_videos': len(videos_info),
                'videos': videos_info
            }
            
        except Exception as e:
            logger.error(f"Batch extraction error: {e}")
            return {'success': False, 'error': str(e)}


class TelegramBotIntegration:
    """
    TELEGRAM BOT INTEGRATION FOR ENHANCED YOUTUBE DOWNLOADER
    =======================================================
    
    Provides seamless integration with Telegram bots
    Handles user interactions and download management
    """
    
    def __init__(self):
        self.downloader = EnhancedYouTubeDownloader()
        self.downloads_dir = "downloads"
        os.makedirs(self.downloads_dir, exist_ok=True)
    
    async def handle_url_message(self, url, user_id, chat_id):
        """
        HANDLE URL MESSAGE FROM TELEGRAM USER
        ====================================
        
        Main entry point for processing YouTube URLs
        Returns appropriate response based on URL type
        """
        
        try:
            # Check if it's a direct YouTube URL
            if self.downloader._is_youtube_url(url):
                # Direct YouTube link - download immediately
                return await self._download_single_video(url, user_id)
            else:
                # Webpage - extract embedded videos
                return await self._handle_webpage_with_videos(url, user_id)
                
        except Exception as e:
            logger.error(f"Error handling URL message: {e}")
            return f"❌ Error processing URL: {str(e)}"
    
    async def _download_single_video(self, url, user_id):
        """Download single YouTube video"""
        
        try:
            # Generate output filename
            video_id = self.downloader._extract_video_id(url)
            output_path = os.path.join(self.downloads_dir, f"{video_id}_{user_id}.%(ext)s")
            
            # Download with fallback
            result = await self.downloader.enhanced_download_with_fallback(
                url, output_path, f"video_{video_id}"
            )
            
            if result['success']:
                info_text = f"""
✅ **Download Successful!**

📹 **Title:** {result['title']}
⏱️ **Duration:** {result['duration']//60}:{result['duration']%60:02d}
👀 **Views:** {result['view_count']:,}
🎯 **Method:** {result['method']}
💾 **File:** {os.path.basename(result['file_path'])}
"""
                
                return {
                    'type': 'video_download',
                    'success': True,
                    'file_path': result['file_path'],
                    'title': result['title'],
                    'info_text': info_text,
                    'method': result['method']
                }
            else:
                return f"❌ Download failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            logger.error(f"Single video download error: {e}")
            return f"❌ Download error: {str(e)}"
    
    async def _handle_webpage_with_videos(self, webpage_url, user_id):
        """Handle webpage containing embedded YouTube videos"""
        
        try:
            # Extract embedded videos
            youtube_urls = self.downloader.extract_embedded_youtube_urls(webpage_url)
            
            if not youtube_urls:
                return "❌ No YouTube videos found on this webpage. Please check the URL and try again."
            
            if len(youtube_urls) == 1:
                # Single embedded video - download directly
                url = youtube_urls[0]
                video_id = self.downloader._extract_video_id(url)
                output_path = os.path.join(self.downloads_dir, f"{video_id}_{user_id}.%(ext)s")
                
                result = await self.downloader.enhanced_download_with_fallback(
                    url, output_path, f"embedded_video_{video_id}"
                )
                
                if result['success']:
                    return {
                        'type': 'single_embedded_video',
                        'success': True,
                        'file_path': result['file_path'],
                        'title': result['title'],
                        'method': result['method']
                    }
                else:
                    return f"❌ Download failed: {result.get('error', 'Unknown error')}"
            
            else:
                # Multiple embedded videos - show selection
                videos_info = []
                
                for i, url in enumerate(youtube_urls[:10], 1):  # Limit to 10 videos
                    try:
                        info = await self.downloader.get_video_info_only(url)
                        if info['success']:
                            duration_formatted = f"{info['duration']//60}:{info['duration']%60:02d}"
                            videos_info.append(f"{i}. {info['title']} ({duration_formatted})")
                    except:
                        videos_info.append(f"{i}. Video {i} (info unavailable)")
                
                videos_list = "\n".join(videos_info)
                
                return {
                    'type': 'multiple_embedded_videos',
                    'total': len(youtube_urls),
                    'videos_list': videos_list,
                    'youtube_urls': youtube_urls[:10]  # Store URLs for later use
                }
                
        except Exception as e:
            logger.error(f"Webpage handling error: {e}")
            return f"❌ Error analyzing webpage: {str(e)}"