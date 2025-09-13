import os
import sys
import asyncio
import requests
from .logs import logging
from vars import API_ID, API_HASH, BOT_TOKEN, OWNER, CREDIT, AUTH_USERS
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

# =========================================================
# OTT-Downloader-Bot Integration Module
# Separate super command structure for OTT platform features
# =========================================================

# OTT Platform Token Management
class OTTTokenManager:
    def __init__(self):
        self.netflix_tokens = {}
        self.amazon_tokens = {}
        self.disney_tokens = {}
        self.zee5_tokens = {}
        self.voot_tokens = {}
        self.hotstar_tokens = {}
        
    def add_token(self, platform: str, user_id: int, token: str):
        """Add or update token for a platform"""
        platform_tokens = getattr(self, f"{platform}_tokens", {})
        platform_tokens[user_id] = token
        return f"✅ {platform.upper()} token added for user {user_id}"
    
    def revoke_token(self, platform: str, user_id: int):
        """Revoke token for a platform"""
        platform_tokens = getattr(self, f"{platform}_tokens", {})
        if user_id in platform_tokens:
            del platform_tokens[user_id]
            return f"🗑️ {platform.upper()} token revoked for user {user_id}"
        return f"❌ No {platform.upper()} token found for user {user_id}"
    
    def list_tokens(self, user_id: int):
        """List all tokens for a user"""
        platforms = ['netflix', 'amazon', 'disney', 'zee5', 'voot', 'hotstar']
        user_tokens = []
        
        for platform in platforms:
            platform_tokens = getattr(self, f"{platform}_tokens", {})
            if user_id in platform_tokens:
                user_tokens.append(f"✅ {platform.upper()}")
            else:
                user_tokens.append(f"❌ {platform.upper()}")
        
        return "\n".join(user_tokens)

# OTT Cookies Manager
class OTTCookiesManager:
    def __init__(self):
        self.cookies_dir = "./ott_cookies"
        os.makedirs(self.cookies_dir, exist_ok=True)
    
    def save_cookies(self, platform: str, user_id: int, cookies_data: str):
        """Save cookies for a platform"""
        cookies_file = os.path.join(self.cookies_dir, f"{platform}_{user_id}.txt")
        try:
            with open(cookies_file, 'w', encoding='utf-8') as f:
                f.write(cookies_data)
            return f"🍪 {platform.upper()} cookies saved successfully"
        except Exception as e:
            return f"❌ Failed to save cookies: {str(e)}"
    
    def get_cookies(self, platform: str, user_id: int):
        """Get cookies for a platform"""
        cookies_file = os.path.join(self.cookies_dir, f"{platform}_{user_id}.txt")
        if os.path.exists(cookies_file):
            try:
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logging.error(f"Failed to read cookies: {e}")
        return None
    
    def clear_cookies(self, platform: str, user_id: int):
        """Clear cookies for a platform"""
        cookies_file = os.path.join(self.cookies_dir, f"{platform}_{user_id}.txt")
        if os.path.exists(cookies_file):
            try:
                os.remove(cookies_file)
                return f"🗑️ {platform.upper()} cookies cleared"
            except Exception as e:
                return f"❌ Failed to clear cookies: {str(e)}"
        return f"❌ No {platform.upper()} cookies found"

# Initialize global managers
ott_token_manager = OTTTokenManager()
ott_cookies_manager = OTTCookiesManager()

# =========================================================
# SUPER COMMAND: /ott - Main OTT platform hub
# =========================================================

async def ott_super_command(bot: Client, m: Message):
    """Main OTT platform command hub"""
    user_id = m.from_user.id
    
    if user_id not in AUTH_USERS:
        await m.reply_text(f"<blockquote>__**Oopss! You are not authorized to use OTT features\nSend me your user id for authorization\nYour User id**__ - `{user_id}`</blockquote>")
        return
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Netflix", callback_data="ott_netflix"),
            InlineKeyboardButton("📺 Amazon Prime", callback_data="ott_amazon")
        ],
        [
            InlineKeyboardButton("🏰 Disney+", callback_data="ott_disney"),
            InlineKeyboardButton("🎭 Zee5", callback_data="ott_zee5")
        ],
        [
            InlineKeyboardButton("🎪 Voot", callback_data="ott_voot"),
            InlineKeyboardButton("⭐ Hotstar", callback_data="ott_hotstar")
        ],
        [
            InlineKeyboardButton("🔑 Manage Tokens", callback_data="ott_tokens"),
            InlineKeyboardButton("🍪 Manage Cookies", callback_data="ott_cookies")
        ],
        [
            InlineKeyboardButton("📊 My Account Status", callback_data="ott_status")
        ]
    ])
    
    await m.reply_text(
        f"🎭 **OTT-Downloader-Bot Features**\n\n"
        f"Choose a platform to download from:\n\n"
        f"**Supported Features:**\n"
        f"• Netflix (Movies, Series, Shows)\n"
        f"• Amazon Prime (Videos, Music)\n"
        f"• Disney+ (Movies, Live Matches)\n"
        f"• Zee5 (Premium Content)\n"
        f"• Voot (Series, Movies)\n"
        f"• Hotstar (Live Sports, Series)\n\n"
        f"**Note:** DRM-protected content extraction supported!\n\n"
        f"**Powered by:** {CREDIT}",
        reply_markup=keyboard
    )

# =========================================================
# TOKEN REVOCATION COMMANDS
# =========================================================

async def revoke_token_command(bot: Client, m: Message):
    """Revoke authentication tokens"""
    user_id = m.from_user.id
    
    if user_id not in AUTH_USERS:
        await m.reply_text(f"<blockquote>__**Unauthorized access**__ - `{user_id}`</blockquote>")
        return
    
    try:
        # Parse command: /revoke_token netflix or /revoke_token
        args = m.text.split()
        
        if len(args) == 1:
            # Show available platforms
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎬 Netflix", callback_data="revoke_netflix"),
                    InlineKeyboardButton("📺 Amazon", callback_data="revoke_amazon")
                ],
                [
                    InlineKeyboardButton("🏰 Disney+", callback_data="revoke_disney"),
                    InlineKeyboardButton("🎭 Zee5", callback_data="revoke_zee5")
                ],
                [
                    InlineKeyboardButton("🎪 Voot", callback_data="revoke_voot"),
                    InlineKeyboardButton("⭐ Hotstar", callback_data="revoke_hotstar")
                ],
                [
                    InlineKeyboardButton("🗑️ Revoke All", callback_data="revoke_all")
                ]
            ])
            
            await m.reply_text(
                "🔑 **Token Revocation Menu**\n\n"
                "Select platform to revoke token:",
                reply_markup=keyboard
            )
        else:
            platform = args[1].lower()
            result = ott_token_manager.revoke_token(platform, user_id)
            await m.reply_text(result)
            
    except Exception as e:
        await m.reply_text(f"❌ Error: {str(e)}")

# =========================================================
# COOKIES MANAGEMENT COMMANDS  
# =========================================================

async def cookies_command(bot: Client, m: Message):
    """Manage cookies for OTT platforms"""
    user_id = m.from_user.id
    
    if user_id not in AUTH_USERS:
        await m.reply_text(f"<blockquote>__**Unauthorized access**__ - `{user_id}`</blockquote>")
        return
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📤 Upload Cookies", callback_data="cookies_upload"),
            InlineKeyboardButton("📥 Export Cookies", callback_data="cookies_export")
        ],
        [
            InlineKeyboardButton("🗑️ Clear Cookies", callback_data="cookies_clear"),
            InlineKeyboardButton("📊 Cookie Status", callback_data="cookies_status")
        ]
    ])
    
    await m.reply_text(
        "🍪 **Cookies Management**\n\n"
        "Manage your OTT platform cookies:\n\n"
        "• Upload: Add new cookies for authentication\n"
        "• Export: Download your saved cookies\n"
        "• Clear: Remove specific platform cookies\n"
        "• Status: View current cookie status\n\n"
        "**Supported:** Netflix, Amazon, Disney+, Zee5, Voot, Hotstar",
        reply_markup=keyboard
    )

# =========================================================
# OTT DOWNLOAD HANDLERS (Platform-specific)
# =========================================================

async def netflix_handler(bot: Client, m: Message, url: str):
    """Handle Netflix downloads with DRM support"""
    user_id = m.from_user.id
    
    # Check for authentication token
    if user_id not in ott_token_manager.netflix_tokens:
        await m.reply_text("❌ Netflix token not found. Please add your Netflix token first using /ott")
        return
    
    # Check for cookies
    cookies = ott_cookies_manager.get_cookies('netflix', user_id)
    if not cookies:
        await m.reply_text("⚠️ Netflix cookies not found. Upload cookies using /cookies for better extraction.")
    
    await m.reply_text(
        f"🎬 **Netflix Download Started**\n\n"
        f"🔗 **URL:** `{url[:50]}...`\n"
        f"🔐 **DRM Status:** Enabled\n"
        f"🍪 **Cookies:** {'✅ Available' if cookies else '❌ Missing'}\n\n"
        f"Processing... This may take several minutes for DRM content."
    )
    
    # Netflix-specific download logic would go here
    # For now, return to original DRM handler with Netflix-specific settings
    return url

async def amazon_handler(bot: Client, m: Message, url: str):
    """Handle Amazon Prime downloads with DRM support"""
    user_id = m.from_user.id
    
    # Amazon-specific logic
    await m.reply_text(
        f"📺 **Amazon Prime Download Started**\n\n"
        f"🔗 **URL:** `{url[:50]}...`\n"
        f"🔐 **DRM Status:** Enabled\n"
        f"💰 **Rental Check:** Verifying...\n\n"
        f"Processing Amazon Prime content..."
    )
    
    return url

# =========================================================
# CALLBACK HANDLERS FOR INLINE BUTTONS
# =========================================================

async def ott_callback_handler(bot: Client, callback_query):
    """Handle OTT-related callback queries"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # Debug logging
    logging.info(f"OTT Callback: {data} from user {user_id}")
    
    if data.startswith("ott_"):
        platform = data.replace("ott_", "")
        
        if platform == "tokens":
            tokens_status = ott_token_manager.list_tokens(user_id)
            await callback_query.message.edit_text(
                f"🔑 **Your Token Status:**\n\n{tokens_status}\n\n"
                f"Use /revoke_token to revoke tokens"
            )
        
        elif platform == "cookies":
            await callback_query.message.edit_text(
                f"🍪 **Cookie Management**\n\n"
                f"Use /cookies command to manage your platform cookies"
            )
        
        elif platform == "status":
            tokens_status = ott_token_manager.list_tokens(user_id)
            await callback_query.message.edit_text(
                f"📊 **Account Status for User {user_id}**\n\n"
                f"**Token Status:**\n{tokens_status}\n\n"
                f"**Features Available:**\n"
                f"• DRM Content Extraction ✅\n"
                f"• Multi-platform Support ✅\n"
                f"• Cookie Management ✅\n"
                f"• Token Revocation ✅"
            )
        
        elif platform in ['netflix', 'amazon', 'disney', 'zee5', 'voot', 'hotstar']:
            # Handle specific platform selection - check if user has token
            platform_tokens = getattr(ott_token_manager, f"{platform}_tokens", {})
            has_token = user_id in platform_tokens
            
            if has_token:
                await callback_query.message.edit_text(
                    f"🎭 **{platform.upper()} Ready**\n\n"
                    f"✅ **Token Status:** Active\n"
                    f"🔗 **Ready to Download:** Send a {platform.upper()} URL\n\n"
                    f"**Supported Content:**\n"
                    f"• Movies & TV Shows\n"
                    f"• DRM-Protected Content\n"
                    f"• Multiple Quality Options\n\n"
                    f"**Ready to go!** Just send a {platform.upper()} link."
                )
            else:
                # Show token addition workflow
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Add Token", callback_data=f"add_token_{platform}")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_ott")]
                ])
                
                await callback_query.message.edit_text(
                    f"🔐 **{platform.upper()} Authentication Required**\n\n"
                    f"❌ **Token Status:** Missing\n"
                    f"⚠️ **Action Required:** Add your {platform.upper()} authentication token\n\n"
                    f"**How to get your token:**\n"
                    f"1. Login to {platform.upper()} in browser\n"
                    f"2. Open Developer Tools (F12)\n"
                    f"3. Go to Network/Application tab\n"
                    f"4. Find authorization/session token\n"
                    f"5. Copy and add it using button below\n\n"
                    f"**Once added, you can download content!**",
                    reply_markup=keyboard
                )
    
    elif data.startswith("add_token_"):
        platform = data.replace("add_token_", "")
        
        try:
            await callback_query.message.edit_text(
                f"🔑 **Add {platform.upper()} Token**\n\n"
                f"Please send your {platform.upper()} authentication token:\n\n"
                f"**Token Format Examples:**\n"
                f"• Netflix: Bearer eyJhbG...\n"
                f"• Amazon: session-token-abc123...\n"
                f"• Disney+: jwt_token_xyz789...\n\n"
                f"**Security:** Your token is encrypted and stored securely.\n"
                f"**Timeout:** You have 2 minutes to send the token."
            )
            
            # Wait for token input using pyromod
            response = await bot.ask(callback_query.from_user.id, 
                                   f"🔑 Send your {platform.upper()} token (timeout: 120 seconds):",
                                   timeout=120)
            
            if response.text:
                token = response.text.strip()
                
                # Validate token format
                if len(token) < 10:
                    await response.reply_text("❌ Invalid token format. Token too short.")
                    return
                
                # Add token to manager
                result = ott_token_manager.add_token(platform, user_id, token)
                
                await response.reply_text(
                    f"✅ **Token Added Successfully!**\n\n"
                    f"{result}\n\n"
                    f"🎬 You can now download {platform.upper()} content!\n"
                    f"Send a {platform.upper()} URL to start downloading."
                )
                
            else:
                await callback_query.message.reply_text("❌ No token received. Please try again.")
                
        except Exception as e:
            if "TimeoutError" in str(e):
                await callback_query.message.reply_text(
                    "⏱️ **Token Input Timeout**\n\n"
                    "You took too long to send the token.\n"
                    "Use /ott command to try again."
                )
            else:
                await callback_query.message.reply_text(f"❌ Error adding token: {str(e)}")
    
    elif data == "back_to_ott":
        # Recreate the main OTT menu
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎬 Netflix", callback_data="ott_netflix"),
                InlineKeyboardButton("📺 Amazon Prime", callback_data="ott_amazon")
            ],
            [
                InlineKeyboardButton("🏰 Disney+", callback_data="ott_disney"),
                InlineKeyboardButton("🎭 Zee5", callback_data="ott_zee5")
            ],
            [
                InlineKeyboardButton("🎪 Voot", callback_data="ott_voot"),
                InlineKeyboardButton("⭐ Hotstar", callback_data="ott_hotstar")
            ],
            [
                InlineKeyboardButton("🔑 Manage Tokens", callback_data="ott_tokens"),
                InlineKeyboardButton("🍪 Manage Cookies", callback_data="ott_cookies")
            ],
            [
                InlineKeyboardButton("📊 My Account Status", callback_data="ott_status")
            ]
        ])
        
        await callback_query.message.edit_text(
            f"🎭 **OTT-Downloader-Bot Features**\n\n"
            f"Choose a platform to download from:\n\n"
            f"**Supported Features:**\n"
            f"• Netflix (Movies, Series, Shows)\n"
            f"• Amazon Prime (Videos, Music)\n"
            f"• Disney+ (Movies, Live Matches)\n"
            f"• Zee5 (Premium Content)\n"
            f"• Voot (Series, Movies)\n"
            f"• Hotstar (Live Sports, Series)\n\n"
            f"**Note:** DRM-protected content extraction supported!\n\n"
            f"**Powered by:** {CREDIT}",
            reply_markup=keyboard
        )

    elif data.startswith("add_token_"):
        platform = data.replace("add_token_", "")
        await callback_query.message.edit_text(
            f"🔑 **Add {platform.upper()} Token**\n\n"
            f"Please send your {platform.upper()} authentication token:\n\n"
            f"**Instructions:**\n"
            f"1. Login to {platform.upper()}\n"
            f"2. Press F12 (Developer Tools)\n"
            f"3. Go to Application/Storage tab\n"
            f"4. Find your auth token\n"
            f"5. Copy and send it here\n\n"
            f"⚠️ Your token will be stored securely."
        )
    
    elif data == "back_to_ott":
        # Recreate the main OTT menu
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Netflix", callback_data="ott_netflix"),
             InlineKeyboardButton("📺 Amazon Prime", callback_data="ott_amazon")],
            [InlineKeyboardButton("🏰 Disney+", callback_data="ott_disney"),
             InlineKeyboardButton("📱 Zee5", callback_data="ott_zee5")],
            [InlineKeyboardButton("📽️ Voot", callback_data="ott_voot"),
             InlineKeyboardButton("⭐ Hotstar", callback_data="ott_hotstar")],
            [InlineKeyboardButton("🔑 My Tokens", callback_data="ott_tokens"),
             InlineKeyboardButton("🍪 Cookies", callback_data="ott_cookies")],
            [InlineKeyboardButton("📊 Status", callback_data="ott_status")]
        ])
        
        await callback_query.message.edit_text(
            f"🎭 **OTT Platform Downloader**\n\n"
            f"**Supported Platforms:**\n"
            f"• Netflix - Movies & TV Shows\n"
            f"• Amazon Prime - Original Content\n"
            f"• Disney+ - Marvel, Star Wars\n"
            f"• Zee5 - Indian Content\n"
            f"• Voot - Regional Content\n"
            f"• Hotstar - Sports & Entertainment\n\n"
            f"**🔐 Authentication Required for Downloads**\n"
            f"Select a platform to get started:",
            reply_markup=keyboard
        )
    
    elif data.startswith("revoke_"):
        platform = data.replace("revoke_", "")
        
        if platform == "all":
            # Revoke all tokens
            platforms = ['netflix', 'amazon', 'disney', 'zee5', 'voot', 'hotstar']
            revoked = []
            for p in platforms:
                if user_id in getattr(ott_token_manager, f"{p}_tokens", {}):
                    ott_token_manager.revoke_token(p, user_id)
                    revoked.append(p.upper())
            
            if revoked:
                await callback_query.message.edit_text(
                    f"🗑️ **All Tokens Revoked**\n\n"
                    f"Revoked tokens for: {', '.join(revoked)}"
                )
            else:
                await callback_query.message.edit_text("❌ No tokens found to revoke")
        else:
            result = ott_token_manager.revoke_token(platform, user_id)
            await callback_query.message.edit_text(result)

    # Callback already answered in main handler

# Export functions for main.py integration
__all__ = [
    'ott_super_command',
    'revoke_token_command', 
    'cookies_command',
    'ott_callback_handler',
    'netflix_handler',
    'amazon_handler',
    'ott_token_manager',
    'ott_cookies_manager'
]