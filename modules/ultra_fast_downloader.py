"""
Ultra-Fast Download Speed Optimization Module
Advanced optimization techniques for blazingly fast YouTube bot downloads
"""

import asyncio
import aiohttp
import tempfile
import os
import time
import gc
import subprocess
import re
import yt_dlp
import shutil
from asyncio import Semaphore
from pathlib import Path
from pyrogram.client import Client
from pyrogram.types import Message
from typing import Dict, Any, Optional, List

# Activate uvloop for performance if available
try:
    import uvloop
    uvloop.install()
    print("✅ uvloop activated for enhanced performance")
except ImportError:
    print("⚠️ uvloop not available, using default event loop")

# Check for aiofiles availability
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
    print("✅ aiofiles available for streaming downloads")
except ImportError:
    AIOFILES_AVAILABLE = False
    print("⚠️ aiofiles not available, using fallback methods")


class UltraFastDownloader:
    """Ultra-fast download manager with advanced optimization techniques"""
    
    def __init__(self):
        # Platform detection for Render optimization
        is_render = (
            os.getenv('RENDER') is not None or 
            'onrender.com' in os.getenv('RENDER_EXTERNAL_URL', '') or
            os.getenv('RENDER_SERVICE_ID') is not None
        )
        
        # Adjust concurrency based on platform
        if is_render:
            # Render: Limited resources (512MB RAM), reduce concurrency
            self.download_semaphore = Semaphore(4)  # Max 4 concurrent downloads for Render
            self.chunk_size = 4096  # Smaller chunks for Render (4KB)
            self.max_concurrent_fragments = 4  # Fewer fragments
            self.memory_threshold = 400  # MB - Render memory limit safety
            print("🔧 Optimized for Render platform: Limited concurrency (4 max, 4KB chunks)")
        else:
            # Other platforms: Higher performance settings
            self.download_semaphore = Semaphore(12)  # Max 12 concurrent downloads
            self.chunk_size = 16384  # Larger chunks (16KB)
            self.max_concurrent_fragments = 8  # More fragments
            self.memory_threshold = 1024  # MB - Higher memory usage allowed
            print("🚀 Optimized for high-performance platform: Full concurrency (12 max, 16KB chunks)")
            
        self.is_render = is_render
        self.session = None
        
    async def initialize_session(self):
        """Initialize optimized aiohttp session with aiodns if available"""
        if not self.session:
            # Configure resolver for better DNS performance
            try:
                import aiodns
                resolver = aiohttp.AsyncResolver()
                print("✅ aiodns activated for faster DNS resolution")
            except ImportError:
                resolver = None
                print("⚠️ aiodns not available, using default resolver")
                
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=900),  # 15 minute timeout
                connector=aiohttp.TCPConnector(
                    resolver=resolver,           # Use aiodns if available
                    limit=100,                   # Total connection pool size
                    limit_per_host=30,           # Max connections per host
                    keepalive_timeout=30,        # Keep connections alive
                    enable_cleanup_closed=True,  # Cleanup closed connections
                    use_dns_cache=True,          # Cache DNS lookups
                    ttl_dns_cache=300            # DNS cache TTL
                )
            )
    
    async def close_session(self):
        """Cleanup aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def optimized_ytdlp_download(self, url: str, output_path: Path, filename: str, user_id: int = None) -> Dict[str, Any]:
        """Ultra-fast download using optimized yt-dlp configuration without aria2c"""
        try:
            temp_file = output_path / filename
            
            # Use centralized configuration with platform-optimized settings
            from modules.utils import build_ydl_opts
            ydl_opts = build_ydl_opts(url, str(temp_file), user_id=user_id)
            
            # Apply platform-specific optimizations
            if self.is_render:
                ydl_opts.update({
                    'http_chunk_size': self.chunk_size,  # 4KB chunks for Render
                    'concurrent_fragments': self.max_concurrent_fragments,  # Limit fragments
                    'socket_timeout': 20,  # Shorter timeout for Render
                    'retries': 3,  # Fewer retries to save resources
                    'buffersize': 8192,  # Smaller buffer
                })
            else:
                ydl_opts.update({
                    'http_chunk_size': self.chunk_size,  # 16KB chunks for high-performance
                    'concurrent_fragments': self.max_concurrent_fragments,  # More fragments
                    'socket_timeout': 60,  # Longer timeout
                    'retries': 8,  # More retries
                    'buffersize': 32768,  # Larger buffer
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if temp_file.exists():
                    # Determine which downloader was actually used
                    downloader_used = 'ffmpeg' if '.m3u8' in url.lower() else 'yt-dlp'
                    return {
                        'success': True,
                        'filepath': str(temp_file),
                        'title': info.get('title', 'Unknown') if info else 'Unknown',
                        'tool_used': downloader_used
                    }
        except Exception as e:
            print(f"Optimized download failed: {e}")
        
        return {'success': False, 'error': 'optimized download failed'}

    async def stream_pytubefix_download(self, url: str, output_path: Path, progress_callback) -> Dict[str, Any]:
        """Stream download using pytubefix with progress tracking"""
        try:
            if progress_callback:
                await progress_callback("🔄 Trying pytubefix streaming...")
            
            # Import pytubefix dynamically (if available)
            try:
                from pytubefix import YouTube  # type: ignore
                
                yt = YouTube(url)
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                
                if not stream:
                    stream = yt.streams.filter(adaptive=True, file_extension='mp4').order_by('resolution').desc().first()
                
                if stream:
                    filename = f"video_{int(time.time())}.mp4"
                    filepath = output_path / filename
                    
                    if progress_callback:
                        await progress_callback(f"📥 Downloading {stream.resolution}p...")
                    stream.download(output_path=str(output_path), filename=filename)
                    
                    return {
                        'success': True,
                        'filepath': str(filepath),
                        'title': yt.title,
                        'tool_used': 'pytubefix'
                    }
                    
            except ImportError:
                print("pytubefix not available, skipping...")
            except Exception as e:
                print(f"pytubefix download failed: {e}")
        
        except Exception as e:
            print(f"Stream download failed: {e}")
        
        return {'success': False, 'error': 'pytubefix download failed'}

    async def basic_optimized_download(self, url: str, output_path: Path, user_id: int = None) -> Dict[str, Any]:
        """Fallback optimized yt-dlp download with centralized configuration"""
        try:
            filename = f"video_{int(time.time())}.mp4"
            temp_file = output_path / filename
            
            # Use centralized configuration with platform optimization
            from modules.utils import build_ydl_opts
            ydl_opts = build_ydl_opts(url, str(temp_file), user_id=user_id)
            
            # Apply platform-specific optimizations
            if hasattr(self, 'is_render') and self.is_render:
                ydl_opts.update({
                    'http_chunk_size': getattr(self, 'chunk_size', 4096),
                    'concurrent_fragments': getattr(self, 'max_concurrent_fragments', 4),
                    'socket_timeout': 20,
                    'retries': 3,
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if temp_file.exists():
                    # Determine which downloader was actually used
                    downloader_used = 'ffmpeg' if '.m3u8' in url.lower() else 'yt-dlp'
                    return {
                        'success': True,
                        'filepath': str(temp_file),
                        'title': info.get('title', 'Unknown') if info else 'Unknown',
                        'tool_used': downloader_used
                    }
        except Exception as e:
            print(f"Basic download failed: {e}")
        
        return {'success': False, 'error': 'basic download failed'}

    async def ultra_download(self, url: str, output_path: Path, progress_callback, user_id: int = None) -> Dict[str, Any]:
        """Try multiple download methods with fallbacks"""
        try:
            # Method 1: Try pytubefix with streaming
            result = await self.stream_pytubefix_download(url, output_path, progress_callback)
            if result['success']:
                return result
            
            # Method 2: Try optimized yt-dlp without aria2c
            result = await self.optimized_ytdlp_download(url, output_path, f"video_{int(time.time())}.mp4", user_id=user_id)
            if result['success']:
                return result
                
            # Method 3: Fallback to basic optimized download
            return await self.basic_optimized_download(url, output_path, user_id=user_id)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def download_with_semaphore(self, url: str, progress_callback=None, user_id: int = None):
        """Download with semaphore control"""
        async with self.download_semaphore:
            return await self.enhanced_download(url, progress_callback, user_id=user_id)

    async def enhanced_download(self, url: str, progress_callback=None, user_id: int = None) -> Dict[str, Any]:
        """Enhanced download with temporary directory management"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            return await self.ultra_download(url, temp_path, progress_callback, user_id=user_id)

    async def stream_download(self, url: str, filename: str) -> bool:
        """Stream download with chunked processing for maximum speed"""
        try:
            await self.initialize_session()
            
            if self.session and AIOFILES_AVAILABLE:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(filename, 'wb') as file:
                            async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
                                await file.write(chunk)
                    return True
            else:
                # Fallback to synchronous download if aiofiles not available
                print("⚠️ Using fallback download method (aiofiles unavailable)")
                return False
        except Exception as e:
            print(f"Stream download error: {e}")
        
        return False

    async def process_multiple_urls_parallel(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Process multiple URLs concurrently with semaphore control"""
        if len(urls) > 1:
            tasks = [self.download_with_semaphore(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter out exceptions and return only successful results
            return [result for result in results if isinstance(result, dict)]
        else:
            return [await self.enhanced_download(urls[0])]


class MemoryOptimizedYouTubeHandler:
    """Memory-optimized YouTube handler for Render's 512MB RAM limit"""
    
    def __init__(self):
        self.downloader = UltraFastDownloader()
        
    async def optimized_progress_callback(self, downloaded: int, total: int, speed: float, prog_message) -> None:
        """Non-blocking progress updates"""
        if downloaded % (1024 * 1024) == 0:  # Update every MB
            progress = (downloaded / total) * 100 if total > 0 else 0
            asyncio.create_task(
                self.update_progress_safe(prog_message, f"⚡ {progress:.1f}% at {speed:.1f} MB/s")
            )
    
    async def update_progress_safe(self, prog_message, text: str):
        """Safe progress update that won't block"""
        try:
            await prog_message.edit(text)
        except:
            pass  # Ignore edit errors

    async def ultra_fast_ytm_handler(self, bot: Client, m: Message, links: List[str], globals_module):
        """Ultra-fast, memory-efficient YouTube downloader with true parallel processing"""
        
        # Use temporary files that auto-cleanup
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Process downloads with TRUE PARALLEL processing when multiple URLs
            success_count = 0
            
            if len(links) > 1:
                # Parallel processing for multiple URLs
                await m.reply_text(f"🚀 **ULTRA FAST PARALLEL DOWNLOAD**\n⚡ Processing {len(links)} URLs concurrently...")
                
                # Use semaphore-controlled parallel downloads
                tasks = []
                for i, url in enumerate(links):
                    task = self.download_single_with_progress(bot, m, url, temp_path, i+1, globals_module)
                    tasks.append(task)
                
                # Execute all downloads in parallel with semaphore control
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successful downloads
                success_count = sum(1 for result in results if isinstance(result, dict) and result.get('success', False))
                
            else:
                # Single URL processing
                result = await self.download_single_with_progress(bot, m, links[0], temp_path, 1, globals_module)
                success_count = 1 if result.get('success', False) else 0
        
        await self.downloader.close_session()
        return success_count

    async def download_single_with_progress(self, bot: Client, m: Message, url: str, temp_path: Path, count: int, globals_module) -> Dict[str, Any]:
        """Download single URL with progress tracking"""
        if hasattr(globals_module, 'cancel_requested') and globals_module.cancel_requested:
            return {'success': False, 'error': 'cancelled'}
        
        # Extract user_id for authentication token support
        user_id = m.from_user.id
            
        prog = await m.reply_text(f"🚀 **ULTRA FAST DOWNLOAD** [{count:03d}]\n⚡ Optimizing speed...")
        
        async def progress_update(message):
            asyncio.create_task(self.update_progress_safe(prog, f"🚀 [{count:03d}] {message}"))
        
        # Use semaphore-controlled download with user authentication
        async with self.downloader.download_semaphore:
            result = await self.downloader.ultra_download(url, temp_path, progress_update, user_id=user_id)
        
        if result['success']:
            try:
                await prog.delete(True)
                
                # Send file (removed misleading compression message)
                file_size = os.path.getsize(result['filepath'])
                
                await bot.send_document(
                    chat_id=m.chat.id,
                    document=result['filepath'],
                    caption=f'⚡ **ULTRA FAST DOWNLOAD** [{count:03d}]\n'
                           f'🎵 **Title:** {result.get("title", "Video")}\n'
                           f'🔗 **Link:** {url}\n'
                           f'⚡ **Method:** {result.get("tool_used", "optimized")}\n'
                           f'📊 **Size:** {file_size / (1024*1024):.1f}MB'
                )
                return {'success': True}
                
            except Exception as e:
                await m.reply_text(f'⚠️ **Upload Failed** [{count:03d}]\n**Error:** {str(e)}')
                return {'success': False, 'error': str(e)}
        else:
            await prog.delete(True)
            await m.reply_text(f'❌ **Download Failed** [{count:03d}]\n**Error:** {result["error"]}')
            return result


# Initialize global instances
ultra_fast_downloader = UltraFastDownloader()
memory_optimized_handler = MemoryOptimizedYouTubeHandler()


async def ultra_fast_youtube_download(bot: Client, m: Message, urls: List[str], globals_module=None):
    """Main entry point for ultra-fast YouTube downloads"""
    return await memory_optimized_handler.ultra_fast_ytm_handler(bot, m, urls, globals_module)