import nextcord
from nextcord.ext import commands
import settings
import os
import importlib.util

intents = nextcord.Intents.all()
bot = commands.Bot(
    command_prefix=settings.bot_prefix, intents=intents, help_command=None
)

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
    if isinstance(error, nextcord.NotFound):
        await interaction.response.send_message("Interaction expired or not found.", ephemeral=True)
    elif isinstance(error, nextcord.HTTPException):
        await interaction.response.send_message("HTTP error occurred.", ephemeral=True)
    elif isinstance(error, nextcord.Forbidden):
        await interaction.response.send_message("You do not have permission to perform this action.", ephemeral=True)
    elif isinstance(error, commands.CommandOnCooldown):
        await interaction.response.send_message(f"Command is on cooldown. Please wait {error.retry_after:.2f} seconds.", ephemeral=True)
    elif isinstance(error, commands.MissingPermissions):
        await interaction.response.send_message("You are missing required permissions.", ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await interaction.response.send_message("Missing a required argument.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)

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