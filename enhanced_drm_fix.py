#!/usr/bin/env python3
"""
Enhanced DRM Handler - Based on Original Repository Logic
Adds sophisticated DRM handling similar to the original saini-txt-direct
"""

import os
import subprocess
import requests
from pathlib import Path

class EnhancedDRMHandler:
    """Enhanced DRM handler with Widevine support like original repository"""
    
    def __init__(self):
        self.temp_dir = Path("temp_drm")
        self.temp_dir.mkdir(exist_ok=True)
    
    def get_mps_and_keys(self, api_url):
        """
        Extract MPD and keys from API (like original repository)
        This would connect to your DRM key extraction service
        """
        try:
            response = requests.get(api_url, timeout=30)
            response_json = response.json()
            mpd = response_json.get('MPD')
            keys = response_json.get('KEYS')
            return mpd, keys
        except Exception as e:
            print(f"Failed to get MPD and keys: {e}")
            return None, None
    
    async def decrypt_and_merge_video(self, mpd_url, keys_string, output_path, output_name, quality="720"):
        """
        Complete DRM decryption pipeline (like original repository)
        Downloads encrypted content and decrypts using mp4decrypt
        """
        try:
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)

            # Step 1: Download encrypted streams (enhanced command like original)
            cmd1 = f'''yt-dlp -f "bv[height<={quality}]+ba/b" \
                      -o "{output_path}/file.%(ext)s" \
                      --allow-unplayable-format \
                      --no-check-certificate \
                      --external-downloader aria2c \
                      --external-downloader-args "aria2c:--max-connection-per-server=16 --split=16" \
                      --concurrent-fragments 16 \
                      --fragment-retries 25 \
                      "{mpd_url}"'''
            
            print(f"🔄 Downloading encrypted streams...")
            result = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Download failed: {result.stderr}")
                return None

            # Step 2: Find downloaded files
            av_files = list(output_path.iterdir())
            print(f"📁 Downloaded files: {av_files}")
            
            # Step 3: Decrypt video and audio separately
            video_decrypted = False
            audio_decrypted = False
            
            for file_path in av_files:
                if file_path.suffix == ".mp4" and not video_decrypted:
                    # Decrypt video
                    cmd2 = f'mp4decrypt {keys_string} --show-progress "{file_path}" "{output_path}/video.mp4"'
                    print(f"🔓 Decrypting video...")
                    result = subprocess.run(cmd2, shell=True)
                    if result.returncode == 0 and (output_path / "video.mp4").exists():
                        video_decrypted = True
                        file_path.unlink()  # Remove encrypted file
                
                elif file_path.suffix == ".m4a" and not audio_decrypted:
                    # Decrypt audio
                    cmd3 = f'mp4decrypt {keys_string} --show-progress "{file_path}" "{output_path}/audio.m4a"'
                    print(f"🔓 Decrypting audio...")
                    result = subprocess.run(cmd3, shell=True)
                    if result.returncode == 0 and (output_path / "audio.m4a").exists():
                        audio_decrypted = True
                        file_path.unlink()  # Remove encrypted file

            if not video_decrypted or not audio_decrypted:
                print("❌ Decryption failed: missing video or audio")
                return None

            # Step 4: Merge decrypted streams
            final_output = output_path / f"{output_name}.mp4"
            cmd4 = f'ffmpeg -i "{output_path}/video.mp4" -i "{output_path}/audio.m4a" -c copy "{final_output}"'
            print(f"🔗 Merging streams...")
            result = subprocess.run(cmd4, shell=True)
            
            # Cleanup temporary files
            if (output_path / "video.mp4").exists():
                (output_path / "video.mp4").unlink()
            if (output_path / "audio.m4a").exists():
                (output_path / "audio.m4a").unlink()
                
            if result.returncode == 0 and final_output.exists():
                print(f"✅ DRM decryption successful: {final_output}")
                return str(final_output)
            else:
                print("❌ Failed to merge streams")
                return None
                
        except Exception as e:
            print(f"❌ DRM decryption error: {e}")
            return None
    
    def enhanced_ytdlp_command(self, url, output_name, quality="720"):
        """
        Enhanced yt-dlp command with 2025 DRM bypass techniques
        """
        # Modern YouTube DRM bypass (like original but updated for 2025)
        cmd = f'''yt-dlp \
                  --extractor-arg "youtube:player-client=web" \
                  --cookies-from-browser chrome \
                  --allow-unplayable-formats \
                  --external-downloader aria2c \
                  --external-downloader-args "aria2c:--max-connection-per-server=16 --split=16 --min-split-size=1M" \
                  --concurrent-fragments 16 \
                  --fragment-retries 25 \
                  --http-chunk-size 10M \
                  --buffer-size 16K \
                  -f "bv[height<={quality}]+ba/b[height<={quality}]/bv+ba" \
                  -o "{output_name}.%(ext)s" \
                  "{url}"'''
        
        return cmd.replace('\n', ' ').replace('  ', ' ')
    
    def cleanup_temp_files(self):
        """Clean up temporary DRM files"""
        try:
            for file in self.temp_dir.glob("*"):
                file.unlink()
            print("🧹 Cleaned up DRM temporary files")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

# Usage example:
if __name__ == "__main__":
    drm_handler = EnhancedDRMHandler()
    
    # Example: Enhanced YouTube download with DRM bypass
    url = "https://example.com/video"
    cmd = drm_handler.enhanced_ytdlp_command(url, "test_video", "720")
    print(f"Enhanced command: {cmd}")