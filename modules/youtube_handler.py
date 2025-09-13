import os
import re
import requests
import subprocess
import asyncio
import yt_dlp
from pytube import YouTube
from pyromod import listen
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from vars import CREDIT, cookies_file_path, AUTH_USERS
from . import globals
from .utils import cleanup_temp_files, final_cleanup

#==============================================================================================================================

def extract_youtube_urls(text):
    """Extract YouTube URLs from text using regex"""
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
        r'https?://(?:www\.)?youtube-nocookie\.com/embed/[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'youtube\.com/watch\?v=[\w-]+',
        r'youtube\.com/embed/[\w-]+',
        r'youtube-nocookie\.com/embed/[\w-]+',
        r'youtu\.be/[\w-]+'
    ]
    
    urls = []
    for pattern in youtube_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        urls.extend(matches)
    
    return urls

def sanitize_filename(filename):
    """Sanitize filename to prevent command injection and file system issues"""
    # Remove shell metacharacters and problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*\'"`$;&(){}[\]]', '', filename)
    # Replace spaces with underscores and limit length
    sanitized = sanitized.replace(' ', '_')[:100]
    return sanitized

async def cookies_handler(client: Client, m: Message):
    editable = await m.reply_text(
        "**Please upload the YouTube Cookies file (.txt format).**",
        quote=True
    )

    try:
        # Wait for the user to send the cookies file
        input_message: Message = await client.listen(m.chat.id)

        # Validate the uploaded file
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return

        # Download the cookies file
        downloaded_path = await input_message.download()

        # Read the content of the uploaded file
        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()

        # Replace the content of the target cookies file
        with open(cookies_file_path, "w") as target_file:
            target_file.write(cookies_content)

        await editable.delete()
        await input_message.delete()
        await m.reply_text(
            "✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`."
        )

    except Exception as e:
        await m.reply_text(f"__**Failed Reason**__\n<blockquote>{str(e)}</blockquote>")
        
#==============================================================================================================================
async def getcookies_handler(client: Client, m: Message):
    try:
        # Send the cookies file to the user
        await client.send_document(
            chat_id=m.chat.id,
            document=cookies_file_path,
            caption="Here is the `youtube_cookies.txt` file."
        )
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")     

#==========================================================================================================================================================================================
async def ytm_handler(bot: Client, m: Message):
    # Clean up all temporary files before starting new download
    cleaned_count = cleanup_temp_files()
    if cleaned_count > 0:
        print(f"🧹 Cleaned {cleaned_count} temporary files before starting YouTube music download")
    
    globals.processing_request = True
    globals.cancel_requested = False
    editable = await m.reply_text("**Input Type**\n\n<blockquote><b>01 •Send me the .txt file containing YouTube links\n02 •Send Single link or Set of YouTube multiple links</b></blockquote>")
    input: Message = await bot.listen(editable.chat.id)
    if input.document and input.document.file_name.endswith(".txt"):
        x = await input.download()
        file_name, ext = os.path.splitext(os.path.basename(x))
        playlist_name = file_name.replace('_', ' ')
        try:
            with open(x, "r") as f:
                content = f.read()
            
            # Extract YouTube URLs from the content using regex
            youtube_urls = extract_youtube_urls(content)
            links = []
            
            for url in youtube_urls:
                # Ensure URL has protocol
                if not url.startswith('http'):
                    url = 'https://' + url
                
                # Split into protocol and rest for compatibility with existing code
                if "://" in url:
                    parts = url.split("://", 1)
                    links.append(parts)
            
            os.remove(x)
            
            if not links:
                await m.reply_text("**No valid YouTube URLs found in the file.**")
                return
        except:
             await m.reply_text("**Invalid file input.**")
             os.remove(x)
             return

        await editable.edit(f"**•ᴛᴏᴛᴀʟ 🔗 ʟɪɴᴋs ғᴏᴜɴᴅ ᴀʀᴇ --__{len(links)}__--\n•sᴇɴᴅ ғʀᴏᴍ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ...")
        try:
            input0: Message = await bot.listen(editable.chat.id, timeout=20)
            raw_text = input0.text
            await input0.delete(True)
        except asyncio.TimeoutError:
            raw_text = '1'
        
        await editable.delete()
        arg = int(raw_text)
        count = int(raw_text)
        try:
            if raw_text == "1":
                playlist_message = await m.reply_text(f"<blockquote><b>⏯️Playlist : {playlist_name}</b></blockquote>")
                await bot.pin_chat_message(m.chat.id, playlist_message.id)
                message_id = playlist_message.id
                pinning_message_id = message_id + 1
                await bot.delete_messages(m.chat.id, pinning_message_id)
        except Exception as e:
            pass
    
    elif input.text:
        content = input.text.strip()
        
        # Extract YouTube URLs from the content using regex
        youtube_urls = extract_youtube_urls(content)
        links = []
        
        for url in youtube_urls:
            # Ensure URL has protocol
            if not url.startswith('http'):
                url = 'https://' + url
            
            # Split into protocol and rest for compatibility with existing code
            if "://" in url:
                parts = url.split("://", 1)
                links.append(parts)
        
        if not links:
            await m.reply_text("**No valid YouTube URLs found in the text.**")
            return
            
        count = 1
        arg = 1
        await editable.delete()
        await input.delete(True)
    else:
        await m.reply_text("**Invalid input. Send either a .txt file or YouTube links set**")
        return
 
    try:
        for i in range(arg-1, len(links)):  # Iterate over each link
            if globals.cancel_requested:
                await m.reply_text("🚦**STOPPED**🚦")
                globals.processing_request = False
                globals.cancel_requested = False
                return
            # Handle embedded YouTube links properly
            link_part = links[i][1]
            
            # Handle various embedded YouTube formats
            if "youtube.com/embed/" in link_part or "youtube-nocookie.com/embed/" in link_part:
                # Extract video ID from embed URL
                if "/embed/" in link_part:
                    video_id = link_part.split("/embed/")[1].split("?")[0].split("&")[0]
                    Vxy = f"youtu.be/{video_id}"
                else:
                    Vxy = link_part
            elif "watch?v=" in link_part:
                # Regular YouTube watch URL
                Vxy = link_part
            elif "youtu.be/" in link_part:
                # Already shortened URL
                Vxy = link_part
            else:
                # Handle other cases or fallback
                Vxy = link_part.replace("www.youtube-nocookie.com/embed", "youtu.be")
            
            url = "https://" + Vxy
            
            # Improved error handling for oEmbed
            try:
                oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
                response = requests.get(oembed_url, timeout=10)
                if response.status_code == 200:
                    audio_title = response.json().get('title', 'YouTube Video')
                else:
                    audio_title = 'YouTube Video'
            except Exception:
                audio_title = 'YouTube Video'
            
            audio_title = audio_title.replace("_", " ")
            # Sanitize filename to prevent command injection
            safe_title = sanitize_filename(audio_title)
            name = f'{safe_title[:60]}_{CREDIT}'        
            name1 = f'{audio_title} {CREDIT}'

            if "youtube.com" in url or "youtu.be" in url:
                prog = await m.reply_text(f"<i><b>Audio Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>")
                
                # Use subprocess.run instead of os.system for security
                cmd = ['yt-dlp', '-x', '--audio-format', 'mp3', '--cookies', cookies_file_path, url, '-o', f'{name}.mp3']
                print(f"Running command: {' '.join(cmd)}")
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    success = result.returncode == 0
                except subprocess.TimeoutExpired:
                    success = False
                    print("yt-dlp command timed out")
                except Exception as e:
                    success = False
                    print(f"Error running yt-dlp: {e}")
                if success and os.path.exists(f'{name}.mp3'):
                    await prog.delete(True)
                    print(f"File {name}.mp3 exists, attempting to send...")
                    try:
                        await bot.send_document(chat_id=m.chat.id, document=f'{name}.mp3', caption=f'**🎵 Title : **[{str(count).zfill(3)}] - {name1}.mp3\n\n🔗**Video link** : {url}\n\n🌟** Extracted By **: {CREDIT}')
                        os.remove(f'{name}.mp3')
                        count+=1
                    except Exception as e:
                        await m.reply_text(f'⚠️**Upload Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {url}', disable_web_page_preview=True)
                        count+=1
                else:
                    await prog.delete(True)
                    error_msg = result.stderr if 'result' in locals() and result.stderr else "Unknown error"
                    await m.reply_text(f'⚠️**Download Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {url}\n**Error** =>> {error_msg[:100]}...', disable_web_page_preview=True)
                    count+=1
                               
    except Exception as e:
        await m.reply_text(f"<b>Failed Reason:</b>\n<blockquote><b>{str(e)}</b></blockquote>")
    finally:
        await m.reply_text("<blockquote><b>All YouTube Music Download Successfully</b></blockquote>")
        
        # Mark processing as complete before final cleanup
        globals.processing_request = False
        
        # Final cleanup after completing all downloads
        final_cleaned = final_cleanup()
        if final_cleaned > 0:
            print(f"🧹 Final cleanup: Removed {final_cleaned} temporary files after YouTube music downloads")

#========================================================================================================================================================================================================
async def y2t_handler(bot: Client, message: Message):
    # Clean up all temporary files before starting new conversion
    cleaned_count = cleanup_temp_files()
    if cleaned_count > 0:
        print(f"🧹 Cleaned {cleaned_count} temporary files before starting YouTube to text conversion")
    
    user_id = str(message.from_user.id)
    
    editable = await message.reply_text(
        f"<blockquote><b>Send YouTube Website/Playlist link for convert in .txt file</b></blockquote>"
    )

    input_message: Message = await bot.listen(message.chat.id)
    youtube_link = input_message.text.strip()
    await input_message.delete(True)
    await editable.delete(True)

    # Fetch the YouTube information using yt-dlp with cookies
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': True,
        'forcejson': True,
        'cookies': 'youtube_cookies.txt'  # Specify the cookies file
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(youtube_link, download=False)
            if 'entries' in result:
                title = result.get('title', 'youtube_playlist')
            else:
                title = result.get('title', 'youtube_video')
        except yt_dlp.utils.DownloadError as e:
            await message.reply_text(
                f"<blockquote>{str(e)}</blockquote>"
            )
            return

    # Extract the YouTube links
    videos = []
    if 'entries' in result:
        for entry in result['entries']:
            video_title = entry.get('title', 'No title')
            url = entry['url']
            videos.append(f"{video_title}: {url}")
    else:
        video_title = result.get('title', 'No title')
        url = result['url']
        videos.append(f"{video_title}: {url}")

    # Create and save the .txt file with the custom name
    txt_file = os.path.join("downloads", f'{title}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)  # Ensure the directory exists
    with open(txt_file, 'w') as f:
        f.write('\n'.join(videos))

    # Send the generated text file to the user with a pretty caption
    await message.reply_document(
        document=txt_file,
        caption=f'<a href="{youtube_link}">__**Click Here to Open Link**__</a>\n<blockquote>{title}.txt</blockquote>\n'
    )

    # Remove the temporary text file after sending
    os.remove(txt_file)
    
    # Final cleanup after completing conversion and sending results
    final_cleaned = final_cleanup()
    if final_cleaned > 0:
        print(f"🧹 Final cleanup: Removed {final_cleaned} temporary files after YouTube to text conversion")
