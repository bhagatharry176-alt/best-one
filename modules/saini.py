import os
import re
import time
import mmap
import datetime
import aiohttp
import asyncio
import logging
import requests

# Optional aiofiles import
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    aiofiles = None
import tgcrypto
import subprocess
import concurrent.futures
from math import ceil
from .utils import progress_bar
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types import Message
from io import BytesIO
from pathlib import Path  
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

def duration(filename):
    try:
        # Check if file exists first
        if not os.path.exists(filename):
            print(f"⚠️ File not found for duration check: {filename}")
            return 0.0
            
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Separate stderr from stdout
            text=True)  # Get string output instead of bytes
        
        if result.returncode != 0:
            print(f"⚠️ FFprobe error for {filename}: {result.stderr}")
            return 0.0
            
        # Clean and validate the output
        duration_str = result.stdout.strip()
        if duration_str and duration_str.replace('.', '').isdigit():
            return float(duration_str)
        else:
            print(f"⚠️ Invalid duration output for {filename}: {duration_str}")
            return 0.0
            
    except Exception as e:
        print(f"⚠️ Duration calculation failed for {filename}: {str(e)}")
        return 0.0

def get_mps_and_keys(api_url):
    """Extract MPD manifest and decryption keys from API (like original repository)"""
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        mpd = response_json.get('MPD')
        keys = response_json.get('KEYS')
        print(f"✅ Successfully extracted MPD and keys from API")
        return mpd, keys
    except Exception as e:
        print(f"❌ Failed to get MPD and keys: {e}")
        return None, None
   
def exec(cmd):
        process = subprocess.run(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output = process.stdout.decode()
        print(output)
        return output
        #err = process.stdout.decode()
def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        fut = executor.map(exec,cmds)
async def aio(url,name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(k, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return k


async def download(url,name):
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka

async def pdf_download(url, file_name, chunk_size=1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name   
   

def parse_vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = []
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except:
                pass
    return new_info


def vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = dict()
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    
                    # temp.update(f'{i[2]}')
                    # new_info.append((i[2], i[0]))
                    #  mp4,mkv etc ==== f"({i[1]})" 
                    
                    new_info.update({f'{i[2]}':f'{i[0]}'})

            except:
                pass
    return new_info


# DUPLICATE FUNCTION REMOVED - Using secure version below

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode == 1:
        return False
    if stdout:
        return f'[stdout]\n{stdout.decode()}'
    if stderr:
        return f'[stderr]\n{stderr.decode()}'

    

def old_download(url, file_name, chunk_size = 1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name


def human_readable_size(size, decimal_places=2):
    unit = 'B'  # Initialize unit
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"


# Initialize global counter
failed_counter = 0

async def decrypt_and_merge_video(mpd_url, keys_string, output_path, output_name, quality="720"):
    """Complete DRM decryption pipeline (like original repository)"""
    try:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # SECURITY FIX: Use secure command list instead of shell=True
        cmd_args = [
            'yt-dlp', '-f', f'bv[height<={quality}]+ba/b', 
            '-o', f'{output_path}/file.%(ext)s',
            '--concurrent-fragments', '16',
            '--fragment-retries', '10', 
            '--http-chunk-size', '10M',
            '--buffer-size', '16K',
            '--allow-unplayable-format',
            '--no-check-certificate',
            '--concurrent-fragments', '8',
            '--fragment-retries', '10',
            str(mpd_url)  # Safely convert to string
        ]
        print(f"🔄 Running secure DRM download")
        result = subprocess.run(cmd_args, shell=False, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ DRM download failed: {result.stderr}")
            return None
        
        avDir = list(output_path.iterdir())
        print(f"📁 Downloaded encrypted files: {avDir}")
        print("🔓 Starting decryption process...")

        video_decrypted = False
        audio_decrypted = False

        for data in avDir:
            if data.suffix == ".mp4" and not video_decrypted:
                # SECURITY FIX: Use subprocess.run with shell=False to prevent command injection
                cmd_args = ['./mp4decrypt'] + keys_string.split() + ['--show-progress', str(data), str(output_path / "video.mp4")]
                print(f"🔓 Decrypting video with secure command")
                result = subprocess.run(cmd_args, shell=False)
                if result.returncode == 0 and (output_path / "video.mp4").exists():
                    video_decrypted = True
                    data.unlink()
            elif data.suffix == ".m4a" and not audio_decrypted:
                # SECURITY FIX: Use subprocess.run with shell=False to prevent command injection
                cmd_args = ['./mp4decrypt'] + keys_string.split() + ['--show-progress', str(data), str(output_path / "audio.m4a")]
                print(f"🔓 Decrypting audio with secure command")
                result = subprocess.run(cmd_args, shell=False)
                if result.returncode == 0 and (output_path / "audio.m4a").exists():
                    audio_decrypted = True
                    data.unlink()

        if not video_decrypted or not audio_decrypted:
            print("❌ Decryption failed: missing video or audio")
            return None

        # Merge decrypted streams with secure command
        final_output = output_path / f"{output_name}.mp4"
        cmd_args = ['ffmpeg', '-i', str(output_path / "video.mp4"), '-i', str(output_path / "audio.m4a"), '-c', 'copy', str(final_output)]
        print(f"🔗 Merging streams securely")
        result = subprocess.run(cmd_args, shell=False)
        
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
        print(f"❌ DRM decryption error: {str(e)}")
        return None

async def download_video(url,cmd, name):
    """Enhanced download with sophisticated DRM bypass and speed optimization"""
    # Import speed optimizer to prevent degradation
    try:
        from .speed_optimizer import optimize_download_speed, get_optimized_command
        optimize_download_speed()  # Run optimization before each download
    except ImportError:
        print("⚠️ Speed optimizer not available, using basic optimization")
    
    # Add modern DRM bypass techniques (like original repository but updated for 2025)
    if 'yt-dlp' in cmd:
        # Add 2025 YouTube DRM bypass (removed chrome cookies for cloud deployment)
        if 'youtu' in url and '--extractor-arg' not in cmd:
            cmd = cmd.replace('yt-dlp', 'yt-dlp --extractor-arg "youtube:player-client=web"')
        
        # Use optimized built-in downloader parameters to prevent speed degradation
        try:
            from .speed_optimizer import get_optimized_command
            cmd = get_optimized_command(cmd)
        except ImportError:
            # Fallback optimization
            # Use built-in downloader optimizations instead
            builtin_args = ' --concurrent-fragments 8 --fragment-retries 10 --retries 5 --socket-timeout 15 --http-chunk-size 4M'
            cmd = f'{cmd}{builtin_args}'
            
        # Add DRM bypass flags
        if '--allow-unplayable-format' not in cmd:
            cmd = f'{cmd} --allow-unplayable-format'
            
        print(f"✅ Enhanced command with DRM bypass and speed optimization")
    
    download_cmd = f'{cmd} -R 25 --fragment-retries 25'
    global failed_counter
    print(f"🔄 Running secure download command")
    logging.info("Running secure download command")
    # SECURITY FIX: Parse command safely and use shell=False
    try:
        import shlex
        cmd_args = shlex.split(download_cmd)
        k = subprocess.run(cmd_args, shell=False)
    except Exception as e:
        print(f"⚠️ Fallback to shell mode due to parsing error: {e}")
        k = subprocess.run(download_cmd, shell=True)
    if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
        failed_counter += 1
        await asyncio.sleep(5)
        await download_video(url, cmd, name)
    failed_counter = 0
    
    # CRITICAL FIX: Only return file path if file actually exists
    try:
        if os.path.isfile(name) and os.path.getsize(name) > 0:
            return name
        elif os.path.isfile(f"{name}.webm") and os.path.getsize(f"{name}.webm") > 0:
            return f"{name}.webm"
        
        name_base = name.split(".")[0]
        if os.path.isfile(f"{name_base}.mkv") and os.path.getsize(f"{name_base}.mkv") > 0:
            return f"{name_base}.mkv"
        elif os.path.isfile(f"{name_base}.mp4") and os.path.getsize(f"{name_base}.mp4") > 0:
            return f"{name_base}.mp4"
        elif os.path.isfile(f"{name_base}.mp4.webm") and os.path.getsize(f"{name_base}.mp4.webm") > 0:
            return f"{name_base}.mp4.webm"

        # Clean up failed downloads to prevent disk space issues that cause speed degradation
        for ext in [".part", ".tmp", ".download"]:
            temp_file = f"{name_base}{ext}"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"🧹 Cleaned up temp file: {temp_file}")
                except:
                    pass

        print(f"❌ Download failed: No valid file found for {name}")
        return None
        
    except Exception as exc:
        print(f"❌ Download error: {exc}")
        return None
    finally:
        # Memory cleanup to prevent speed degradation in Render
        import gc
        gc.collect()


async def send_doc(bot: Client, m: Message, cc, ka, cc1, prog, count, name, channel_id):
    reply = await bot.send_message(channel_id, f"Downloading pdf:\n<pre><code>{name}</code></pre>")
    time.sleep(1)
    start_time = time.time()
    await bot.send_document(channel_id, ka, caption=cc1)
    count+=1
    await reply.delete (True)
    time.sleep(1)
    os.remove(ka)
    time.sleep(3) 


def decrypt_file(file_path, key):  
    if not os.path.exists(file_path): 
        return False  

    with open(file_path, "r+b") as f:  
        num_bytes = min(28, os.path.getsize(file_path))  
        with mmap.mmap(f.fileno(), length=num_bytes, access=mmap.ACCESS_WRITE) as mmapped_file:  
            for i in range(num_bytes):  
                mmapped_file[i] ^= ord(key[i]) if i < len(key) else i 
    return True  

async def download_and_decrypt_video(url, cmd, name, key):  
    video_path = await download_video(url, cmd, name)  
    
    if video_path:  
        decrypted = decrypt_file(video_path, key)  
        if decrypted:  
            print(f"File {video_path} decrypted successfully.")  
            return video_path  
        else:  
            print(f"Failed to decrypt {video_path}.")  
            return None  

async def send_vid(bot: Client, m: Message, cc, filename, vidwatermark, thumb, name, prog, channel_id):
    # CRITICAL FIX: Validate file before processing
    if not filename or not os.path.exists(filename) or os.path.getsize(filename) == 0:
        await bot.send_message(channel_id, 
            f'⚠️**Video Processing Failed**⚠️\n'
            f'**Name** =>> `{name}`\n'
            f'**Reason** =>> Invalid or empty video file\n'
            f'<blockquote><i><b>The downloaded file is corrupted or doesn\'t exist</b></i></blockquote>', 
            disable_web_page_preview=True)
        return
    subprocess.run(f'ffmpeg -i "{filename}" -ss 00:00:10 -vframes 1 "{filename}.jpg"', shell=True)
    await prog.delete (True)
    reply1 = await bot.send_message(channel_id, f"**📩 Uploading Video 📩:-**\n<blockquote>**{name}**</blockquote>")
    reply = await m.reply_text(f"**Generate Thumbnail:**\n<blockquote>**{name}**</blockquote>")
    # Initialize variables with defaults
    thumbnail = f"{filename}.jpg"
    w_filename = filename
    
    try:
        if thumb == "/d":
            thumbnail = f"{filename}.jpg"
        else:
            thumbnail = thumb  
        
        if vidwatermark == "/d":
            w_filename = f"{filename}"
        else:
            w_filename = f"w_{filename}"
            font_path = "vidwater.ttf"
            # SECURITY FIX: Use secure command args instead of shell=True
            cmd_args = [
                'ffmpeg', '-i', str(filename),
                '-vf', f'drawtext=fontfile={font_path}:text=\'{vidwatermark}\':fontcolor=white@0.3:fontsize=h/6:x=(w-text_w)/2:y=(h-text_h)/2',
                '-codec:a', 'copy', str(w_filename)
            ]
            subprocess.run(cmd_args, shell=False)
            
    except Exception as e:
        await m.reply_text(str(e))

    dur = int(duration(w_filename))
    start_time = time.time()

    try:
        await bot.send_video(channel_id, w_filename, caption=cc, supports_streaming=True, height=720, width=1280, thumb=thumbnail, duration=dur, progress=progress_bar, progress_args=(reply, start_time))
    except Exception:
        await bot.send_document(channel_id, w_filename, caption=cc, progress=progress_bar, progress_args=(reply, start_time))
    os.remove(w_filename)
    await reply.delete(True)
    await reply1.delete(True)
    os.remove(f"{filename}.jpg")
