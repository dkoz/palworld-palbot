import os
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv('BOT_TOKEN', "No token found")
bot_prefix = os.getenv('BOT_PREFIX', "!")
bot_activity = os.getenv('BOT_ACTIVITY', "Palworld")
steam_api_key = os.getenv('STEAM_API_KEY', "No key found")