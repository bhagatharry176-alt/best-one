# SAINI DRM Bot

## Overview

The SAINI DRM Bot is a sophisticated Telegram bot designed for downloading and processing DRM-protected video content from various platforms. The bot features advanced DRM decryption capabilities, YouTube downloading functionality, HTML content extraction, and broadcast messaging. It's built with a modular architecture using Pyrogram as the Telegram client framework and includes optimization features for deployment on cloud platforms like Render, Heroku, and Koyeb.

The bot supports multiple content sources including YouTube, ClassPlus, OTT platforms, and general web content with DRM protection. It includes user authorization systems, broadcast capabilities, and various content processing utilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### September 13, 2025 - Successful Render Migration
- **Status**: ✅ Bot successfully running on Render with full functionality
- **Fixed Flask templating issues**: Downgraded to Flask 2.2.5 for compatibility
- **Resolved Pyrogram conflicts**: Removed PyroFork, clean install of Pyrogram 2.0.106
- **Eliminated circular import**: Removed top-level aiofiles imports causing startup failures
- **Standardized imports**: Using public API imports for better stability
- **Enhanced error handling**: Added comprehensive diagnostics in render_start.py
- **Updated dependencies**: Fixed aiofiles version (24.1.0) and dependency conflicts

## System Architecture

### Core Framework
- **Telegram Client**: Pyrogram with TgCrypto for secure and efficient Telegram API interactions
- **Web Server**: Flask application for health checks and deployment compatibility
- **Async Processing**: Asyncio-based architecture for concurrent operations

### Modular Design Pattern
The application follows a modular architecture with separate handlers for different functionalities:
- Authorization module for user access control
- Broadcast module for mass messaging
- DRM handler for encrypted content processing
- YouTube handler for video downloads
- HTML handler for web content extraction
- Text handler for document conversion
- Utils module for common utilities

### Authentication & Authorization
- Owner-based access control with configurable authorized users
- Environment variable-based configuration for security
- Support for both individual user authorization and broadcast user lists

### Content Processing Pipeline
- Multi-format video download support (YouTube, DRM-protected content)
- Quality selection and optimization
- Temporary file management with automatic cleanup
- Progress tracking and user feedback

### Memory Management
- Render-optimized memory management for 512MB RAM environments
- Aggressive cleanup mechanisms to prevent memory leaks
- Temporary file cleanup after processing

### Download Optimization
- Aria2c integration for enhanced download speeds
- Concurrent fragment downloads
- Retry mechanisms and error handling
- Platform-specific optimizations for Railway and Render

## External Dependencies

### Core Dependencies
- **Pyrogram**: Telegram MTProto API client
- **TgCrypto**: Cryptographic operations for Telegram
- **PyroMod**: Extended functionality for Pyrogram
- **yt-dlp**: Video downloading from various platforms
- **Flask**: Web server for deployment health checks

### Content Processing
- **BeautifulSoup4**: HTML parsing and extraction
- **M3U8**: HLS playlist processing
- **CloudScraper**: Cloudflare bypass capabilities
- **PyCryptodome**: Advanced cryptographic operations
- **FFmpeg-python**: Video processing and manipulation

### Platform Integration
- **aiohttp**: Async HTTP client for API interactions
- **aiofiles**: Async file operations
- **requests**: HTTP library for synchronous operations

### Deployment Support
- **psutil**: System resource monitoring
- **gunicorn**: WSGI server for production deployment

### Media Processing
- **Pytube**: YouTube-specific downloading (fallback)
- **Pillow**: Image processing capabilities

### Database & Storage
- **Motor**: Async MongoDB driver
- **SQLAlchemy**: SQL toolkit (for future database features)

The architecture prioritizes modularity, performance optimization for resource-constrained environments, and extensive platform compatibility for various deployment scenarios.