#🇳‌🇮‌🇰‌🇭‌🇮‌🇱‌
# Add your details here and then deploy by clicking on HEROKU Deploy button
import os
from os import environ

# Try multiple methods to load environment variables
def get_env_var(key, default=""):
    # Method 1: Standard environment
    value = environ.get(key, "").strip()
    if value:
        return value
    
    # Method 2: Check all env vars for case variations
    for env_key, env_value in environ.items():
        if env_key.upper() == key.upper() and env_value.strip():
            return env_value.strip()
    
    # Method 3: Try with different prefixes
    for prefix in ["", "REPLIT_", "SECRET_"]:
        full_key = f"{prefix}{key}"
        value = environ.get(full_key, "").strip()
        if value:
            return value
    
    return default

API_ID_STR = get_env_var("API_ID")
API_HASH_STR = get_env_var("API_HASH") 
BOT_TOKEN_STR = get_env_var("BOT_TOKEN")
OWNER_STR = get_env_var("OWNER")

print(f"🔍 Found: API_ID length={len(API_ID_STR)}, API_HASH length={len(API_HASH_STR)}")
print(f"🔍 Found: BOT_TOKEN length={len(BOT_TOKEN_STR)}, OWNER length={len(OWNER_STR)}")

# Convert values with validation
if not API_ID_STR:
    print("⚠️  Environment variables not found - bot will need real credentials to run")
    API_ID = 0
    API_HASH = ""
    BOT_TOKEN = ""
    OWNER = 0
else:
    API_ID = int(API_ID_STR)
    API_HASH = API_HASH_STR
    BOT_TOKEN = BOT_TOKEN_STR 
    OWNER = int(OWNER_STR) if OWNER_STR else 0
CREDIT = environ.get("CREDIT", "TheOne")
REPO_URL = environ.get("REPO_URL", "https://github.com/Harrytt345/saini-txt-direct")
cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")

TOTAL_USER = os.environ.get('TOTAL_USERS', '').split(',')
TOTAL_USERS = [int(user_id) for user_id in TOTAL_USER if user_id.strip()]

AUTH_USER = os.environ.get('AUTH_USERS', '').split(',')
AUTH_USERS = [int(user_id) for user_id in AUTH_USER if user_id.strip()]
if int(OWNER) not in AUTH_USERS:
    AUTH_USERS.append(int(OWNER))
  
#WEBHOOK = True  # Don't change this
#PORT = int(os.environ.get("PORT", 8080))  # Default to 8000 if not set


# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
api_url = os.environ.get("API_URL", "http://master-api-v3.vercel.app/")
api_token = os.environ.get("API_TOKEN")
token_cp = os.environ.get("TOKEN_CP")
adda_token = os.environ.get("ADDA_TOKEN")
photologo = 'https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png' #https://envs.sh/GV0.jpg
photoyt = 'https://tinypic.host/images/2025/03/18/YouTube-Logo.wine.png' #https://envs.sh/GVi.jpg
photocp = 'https://tinypic.host/images/2025/03/28/IMG_20250328_133126.jpg'
photozip = 'https://envs.sh/cD_.jpg'
# .....,.....,.......,...,.......,....., .....,.....,.......,...,.


