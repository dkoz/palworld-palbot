import nextcord
import logging
from nextcord.ext import commands

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
