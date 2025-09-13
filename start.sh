#!/bin/bash
set -e

echo "🔄 Using cached dependencies for faster startup..."

echo "🏗️ Creating clean virtual environment..."
python3 -m venv .venv --without-pip
source .venv/bin/activate

# Ensure pip doesn't use user site packages
export PIP_USER=false
export PIP_BREAK_SYSTEM_PACKAGES=1

echo "⬆️ Installing pip in virtual environment..."
python -m ensurepip --upgrade

echo "📦 Installing dependencies (smart caching)..."
if [ -f "pyproject.toml" ]; then
    python -m pip install .
elif [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt
elif [ -f "sainibots.txt" ]; then
    python -m pip install -r sainibots.txt
else
    echo "❌ No dependency file found. Installing basic dependencies..."
    python -m pip install --no-cache-dir --force-reinstall pyrogram tgcrypto aiofiles pyromod yt-dlp requests aiohttp beautifulsoup4 m3u8 cloudscraper pycryptodome flask ffmpeg-python pytube lxml pytz psutil
fi

echo "🔍 Health check..."
python -m pip check
python -c "import pyrogram.errors; import aiofiles; print('✅ All modules healthy')"

echo "🚀 Starting Telegram Bot..."
echo "🔧 Using virtual environment Python: $(.venv/bin/python --version)"
exec .venv/bin/python main.py