#!/usr/bin/env python3
"""
Speed Restoration Script - Install missing performance dependencies
Run this to restore your bot's upload speed performance
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install {package}: {e}")
        return False

def main():
    """Install all performance-enhancing dependencies"""
    
    logging.info("🚀 Starting Speed Restoration Process...")
    
    # Critical performance packages
    performance_packages = [
        "uvloop==0.19.0",      # 2-4x speed boost for async operations
        "aiofiles==23.2.1",   # Async file I/O
        "aiodns==3.1.1",      # Faster DNS resolution  
        "psutil==5.9.8",      # System monitoring for optimization
    ]
    
    success_count = 0
    total_packages = len(performance_packages)
    
    for package in performance_packages:
        package_name = package.split("==")[0]
        logging.info(f"📦 Installing {package_name}...")
        
        if install_package(package):
            logging.info(f"✅ {package_name} installed successfully")
            success_count += 1
        else:
            logging.error(f"❌ Failed to install {package_name}")
    
    logging.info("-" * 50)
    logging.info(f"📊 Installation Results: {success_count}/{total_packages} packages installed")
    
    if success_count == total_packages:
        logging.info("🎉 ALL performance packages installed successfully!")
        logging.info("🚀 Your bot speed should be significantly improved now")
        logging.info("⚠️  Remember to restart your bot to activate the performance improvements")
    else:
        failed_count = total_packages - success_count
        logging.warning(f"⚠️  {failed_count} packages failed to install")
        logging.info("💡 Try running this script again or install manually")
    
    logging.info("-" * 50)

if __name__ == "__main__":
    main()