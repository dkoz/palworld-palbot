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
    
    bot.loop.create_task(settings.run_whitelist_check(bot))
    
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

settings.load_cogs(bot)

if __name__ == "__main__":
    bot.run(settings.bot_token)