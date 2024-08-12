import nextcord
from nextcord.ext import commands
import utils.settings as settings
import os
import importlib.util
from utils.translations import translator
import logging

logging.basicConfig(filename=os.path.join('logs', 'bot.log'), level=logging.INFO)

intents = nextcord.Intents.all()
bot = commands.Bot(
    command_prefix=settings.bot_prefix, intents=intents, help_command=None
)
translator.set_language(settings.bot_language)

@bot.event
async def on_ready():
    ascii_art = r"""
__________        .__ ___.           __   
\______   \_____  |  |\_ |__   _____/  |_ 
 |     ___/\__  \ |  | | __ \ /  _ \   __\
 |    |     / __ \|  |_| \_\ (  <_> )  |  
 |____|    (____  /____/___  /\____/|__|  
                \/         \/             
    """
    print(ascii_art)
    print(f"{bot.user} is ready! Created by koz")
    activity = nextcord.Activity(
        type=nextcord.ActivityType.playing, name=settings.bot_activity
    )
    await bot.change_presence(activity=activity)

# Error Handling
@bot.event
async def on_application_command_error(interaction, error):
    try:
        if interaction.response.is_done():
            return
        
        if isinstance(error, nextcord.NotFound):
            await interaction.followup.send("Interaction expired or not found.", ephemeral=True)
        elif isinstance(error, nextcord.HTTPException):
            await interaction.followup.send("HTTP error occurred.", ephemeral=True)
        elif isinstance(error, nextcord.Forbidden):
            await interaction.followup.send("You do not have permission to perform this action.", ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            await interaction.followup.send(f"Command is on cooldown. Please wait {error.retry_after:.2f} seconds.", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await interaction.followup.send("You are missing required permissions.", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await interaction.followup.send("Missing a required argument.", ephemeral=True)
        else:
            await interaction.followup.send(f"An error occurred: {str(error)}", ephemeral=True)
    except nextcord.errors.NotFound:
        logging.error("Failed to send error message, interaction not found or expired.")
    except Exception as e:
        logging.error(f"Unexpected error when handling command error: {e}")

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