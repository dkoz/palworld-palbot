import nextcord
from nextcord.ext import commands
import utils.settings as settings
import os
import importlib.util
from utils.translations import translator
from utils.errorhandling import handle_errors
import utils.constants as constants
import logging

logging.basicConfig(filename=os.path.join('logs', 'bot.log'), level=logging.INFO)

intents = nextcord.Intents.all()
bot = commands.Bot(
    command_prefix=settings.bot_prefix, intents=intents, help_command=None
)
translator.set_language(settings.bot_language)

@bot.event
async def on_ready():
    print(constants.PALBOT_ART)
    print(f"Connected to {len(bot.guilds)} servers with {len(bot.users)} users.")
    print(f"Invite link: {nextcord.utils.oauth_url(bot.user.id)}")
    print(f"{bot.user} is ready! Created by koz")
    
    await settings.check_whitelist(bot)
    
    activity = nextcord.Activity(
        type=nextcord.ActivityType.playing, name=settings.bot_activity
    )
    await bot.change_presence(activity=activity)

# Error Handling
@bot.event
async def on_application_command_error(interaction, error):
    await handle_errors(interaction, error)

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

def has_setup_function(module_name):
    module_spec = importlib.util.find_spec(module_name)
    if module_spec is None:
        return False
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return hasattr(module, "setup")

for entry in os.listdir("cogs"):
    if entry.endswith(".py"):
        module_name = f"cogs.{entry[:-3]}"
        if has_setup_function(module_name):
            bot.load_extension(module_name)
    elif os.path.isdir(f"cogs/{entry}"):
        for filename in os.listdir(f"cogs/{entry}"):
            if filename.endswith(".py"):
                module_name = f"cogs.{entry}.{filename[:-3]}"
                if has_setup_function(module_name):
                    bot.load_extension(module_name)

if __name__ == "__main__":
    bot.run(settings.bot_token)