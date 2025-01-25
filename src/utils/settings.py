import os
from dotenv import load_dotenv
import importlib.util
import asyncio
import logging

load_dotenv()
bot_token = os.getenv("BOT_TOKEN", "No token found")
bot_prefix = os.getenv("BOT_PREFIX", "!")
bot_activity = os.getenv("BOT_ACTIVITY", "Palworld")
steam_api_key = os.getenv("STEAM_API_KEY", "No key found")
bot_language = os.getenv("BOT_LANGUAGE", "en")
chatlog_path = os.getenv("CHATLOG_PATH", r"C:\path\to\server\Pal\Binaries\Win64\palguard\logs")
chatlog_webhookurl = os.getenv("CHATLOG_WEBHOOKURL", "https://discord.com/api/webhooks/yourwebhookurl")
chatlog_servername = os.getenv("CHATLOG_SERVERNAME", "Palworld Server")
chatlog_channel = int(os.getenv("CHATLOG_CHANNEL", 12345678910))
whitelist_check = os.getenv('GUILD_WHITELIST')

# Logic for the guild whitelist.
async def check_whitelist(bot):
    if whitelist_check:
        wl_ids = [int(gid.strip()) for gid in whitelist_check.split(',')]
        for guild in bot.guilds:
            if guild.id not in wl_ids:
                await guild.leave()
                logging.info(f"Left {guild.name} (ID: {guild.id})")

async def run_whitelist_check(bot, interval=600):
    while True:
        await check_whitelist(bot)
        await asyncio.sleep(interval)
        logging.info("Whitelist check complete.")

def load_cogs(bot):
    cogs_path = os.path.join(os.path.dirname(__file__), "../cogs")
    for entry in os.listdir(cogs_path):
        if entry.endswith(".py"):
            module_name = f"src.cogs.{entry[:-3]}"
            if _has_setup(module_name):
                bot.load_extension(module_name)
        elif os.path.isdir(os.path.join(cogs_path, entry)):
            for filename in os.listdir(os.path.join(cogs_path, entry)):
                if filename.endswith(".py"):
                    module_name = f"src.cogs.{entry}.{filename[:-3]}"
                    if _has_setup(module_name):
                        bot.load_extension(module_name)

def _has_setup(module_name):
    module_spec = importlib.util.find_spec(module_name)
    if module_spec is None:
        return False
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return hasattr(module, "setup")