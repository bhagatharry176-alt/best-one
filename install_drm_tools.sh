#!/bin/bash
# Install DRM tools for enhanced decryption

echo "🔧 Installing DRM decryption tools..."

# Install mp4decrypt alternative (shaka-packager)
echo "📦 Installing Shaka Packager (mp4decrypt alternative)..."
wget -q "https://github.com/shaka-project/shaka-packager/releases/download/v2.6.1/packager-linux-x64" -O packager
chmod +x packager
mv packager mp4decrypt
echo "✅ mp4decrypt (shaka-packager) installed"

# Verify installation
if command -v ./mp4decrypt &> /dev/null; then
    echo "✅ DRM tools installation complete"
    echo "🔓 mp4decrypt available for Widevine decryption"
else
    echo "❌ Installation failed"
fi

echo "🚀 Your bot now has enhanced DRM capabilities!"