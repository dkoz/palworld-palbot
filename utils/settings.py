import os
from dotenv import load_dotenv
import logging

load_dotenv()
bot_token = os.getenv("BOT_TOKEN", "No token found")
bot_prefix = os.getenv("BOT_PREFIX", "!")
bot_activity = os.getenv("BOT_ACTIVITY", "Palworld")
steam_api_key = os.getenv("STEAM_API_KEY", "No key found")
bot_language = os.getenv("BOT_LANGUAGE", "en")
whitelist_check = os.getenv('GUILD_WHITELIST')

async def check_whitelist(bot):
    if whitelist_check:
        wl_ids = [int(gid.strip()) for gid in whitelist_check.split(',')]
        for guild in bot.guilds:
            if guild.id not in wl_ids:
                await guild.leave()
                logging.info(f"Left {guild.name} (ID: {guild.id})")