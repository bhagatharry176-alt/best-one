#!/usr/bin/env python3
"""
Render Web Service startup script for SAINI DRM Bot
Runs both Flask server (for Render web requirements) and Telegram bot
"""

import logging
import sys
import threading
import time
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def start_telegram_bot():
    """Start the main Telegram bot"""
    try:
        logging.info("🤖 Starting Telegram bot as Background Worker...")
        
        # Import the main module first
        import main
        
        # Check if required environment variables are set
        from modules.vars import API_ID, API_HASH, BOT_TOKEN
        if not all([API_ID, API_HASH, BOT_TOKEN]):
            raise ValueError("Missing required environment variables: API_ID, API_HASH, BOT_TOKEN")
        
        logging.info("✅ Environment variables verified")
        
        # Clear webhook and set commands (from main.py)
        try:
            import requests
            webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
            requests.post(webhook_url, json={"drop_pending_updates": True})
            logging.info("✅ Cleared webhook, using polling mode")
        except Exception as e:
            logging.warning(f"⚠️ Webhook clear failed: {e}")
        
        # Set bot commands and notify owner
        main.reset_and_set_commands()
        main.notify_owner()
        
        logging.info("🤖 Bot starting with polling...")
        # This is the key fix - actually run the bot
        main.bot.run()
        
    except ImportError as e:
        logging.error(f"❌ Import error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Telegram bot failed to start: {e}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

def start_flask_server():
    """Start Flask server for Render web service requirements"""
    try:
        logging.info("🚀 Starting Flask server for Render web service...")
        # Add version diagnostics
        try:
            import flask
            logging.info(f"🔍 Using Flask version: {flask.__version__}")
        except Exception as flask_import_error:
            logging.error(f"❌ Flask import failed: {flask_import_error}")
            import traceback
            logging.error(f"📝 Flask traceback: {traceback.format_exc()}")
            raise
        
        import app
        port = int(os.environ.get('PORT', 10000))  # Render uses PORT env var
        logging.info(f"🌐 Flask server starting on port {port} (Render Web Service)")
        app.app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logging.error(f"❌ Flask server failed: {e}")
        import traceback
        logging.error(f"📝 Full Flask traceback: {traceback.format_exc()}")
        sys.exit(1)

def main():
    """Main entry point for Render Web Service deployment"""
    logging.info("🚀 Starting SAINI DRM Bot as Render Web Service...")
    logging.info("🌐 Starting Flask server + Telegram bot")
    
    # Start Flask server in background thread
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    
    # Wait a moment for Flask to start
    time.sleep(2)
    logging.info("✅ Flask server started in background")
    
    # Start Telegram bot (blocking main thread)
    start_telegram_bot()

if __name__ == "__main__":
    main()