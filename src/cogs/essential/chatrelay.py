import nextcord
from nextcord.ext import commands
import os
from src.utils.database import get_server_details
from src.utils.rconutility import RconUtility
import src.utils.settings as s
import logging

sftp_channel_id = s.chatlog_channel
server_name = s.chatlog_servername

class ChatRelayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sftp_channel_id = sftp_channel_id
        self.server_name = server_name
        self.rcon_util = RconUtility()

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        if message.channel.id != self.sftp_channel_id:
            return

        if not message.content:
            return

        server_details = await get_server_details(self.server_name)
        if not server_details:
            return

        broadcast_message = f"[{message.author.name}]: {message.content}"
        server_info = {
            "name": self.server_name,
            "host": server_details[0],
            "port": server_details[1],
            "password": server_details[2],
        }

        await self.rcon_util.rcon_command(server_info, f"Broadcast {broadcast_message}")

def setup(bot):
    if not os.getenv("CHATLOG_CHANNEL"):
        logging.error("Chat log channel env variable not set. Chat feed will not be loaded.")
        return
    bot.add_cog(ChatRelayCog(bot))
