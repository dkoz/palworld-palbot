import nextcord
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from nextcord.ext import commands
from nextcord import Interaction
from functools import wraps

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_filename = f"palbot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_path = os.path.join('logs', log_filename)

    log_handler = RotatingFileHandler(
        filename=log_path, 
        maxBytes=10**7,
        backupCount=6,
        encoding='utf-8'
    )
    log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    log_handler.setFormatter(log_formatter)

    logging.basicConfig(level=logging.INFO, handlers=[log_handler])

    clean_old_logs('logs', 10)

def clean_old_logs(directory, max_logs):
    log_files = sorted(
        [os.path.join(directory, f) for f in os.listdir(directory) if f.startswith("palbot_") and f.endswith(".log")],
        key=os.path.getctime,
        reverse=True
    )

    while len(log_files) > max_logs:
        os.remove(log_files.pop())

async def handle_errors(interaction, error):
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

def restrict_command():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            interaction: Interaction = args[1]
            if not interaction.guild:
                await interaction.response.send_message("This command cannot be used in DMs.", ephemeral=True)
                return
            return await func(*args, **kwargs)
        return wrapper
    return decorator  