import json
import os
from datetime import datetime, timedelta
import nextcord
from nextcord.ext import commands, tasks
import pytz
from util.rconutility import RconUtility

class RestartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shutdown_config = {}
        self.load_config()
        self.rcon_util = RconUtility(self.servers)
        if self.shutdown_config.get("enabled", False):
            self.shutdown_schedule.start()

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            config = json.load(config_file)
        self.servers = config["PALWORLD_SERVERS"]
        self.shutdown_config = config.get("SHUTDOWN_SCHEDULE", {"enabled": False})
        timezone_str = self.shutdown_config.get("timezone", "UTC")
        self.timezone = pytz.timezone(timezone_str)
        self.announce_channel = self.shutdown_config.get("channel")

    @tasks.loop(seconds=60)
    async def shutdown_schedule(self):
        if not self.shutdown_config.get("enabled", False):
            return
        now_utc = datetime.now(pytz.utc)
        now_local = now_utc.astimezone(self.timezone)
        for shutdown_time_str in self.shutdown_config.get("times", []):
            shutdown_time = datetime.strptime(shutdown_time_str, "%H:%M").time()
            shutdown_datetime_local = datetime.now(self.timezone).replace(
                hour=shutdown_time.hour,
                minute=shutdown_time.minute,
                second=0,
                microsecond=0,
            )
            if shutdown_datetime_local < now_local:
                shutdown_datetime_local += timedelta(days=1)
            time_until_shutdown = (shutdown_datetime_local - now_local).total_seconds()

            if 300 <= time_until_shutdown < 360:
                await self.broadcast_warning("Server restart in 5 minutes")
            elif 180 <= time_until_shutdown < 240:
                await self.broadcast_warning("Server restart in 3 minutes")
            elif 120 <= time_until_shutdown < 180:
                await self.save_server_state()
            elif 60 <= time_until_shutdown < 120:
                await self.initiate_shutdown("Shutdown 30 Server_restart_in_30_seconds")

    async def broadcast_warning(self, message):
        for server_name in self.servers:
            try:
                message_format = message.replace(" ", "\u001f")
                await self.rcon_util.rcon_command(
                    server_name, f"Broadcast {message_format}"
                )
                print(f"Broadcasted to {server_name}: {message}")
            except Exception as e:
                print(f"Error broadcasting to {server_name}: {e}")

    async def save_server_state(self):
        for server_name in self.servers:
            try:
                response = await self.rcon_util.rcon_command(server_name, "Save")
                print(f"State saved for {server_name}: {response}")
            except Exception as e:
                print(f"Error saving state for {server_name}: {e}")

    async def initiate_shutdown(self, command):
        for server_name in self.servers:
            try:
                response = await self.rcon_util.rcon_command(server_name, command)
                print(f"Shutdown initiated for {server_name}: {response}")
                await self.announce_restart(server_name)
            except Exception as e:
                print(f"Error initiating shutdown for {server_name}: {e}")

    # There is a slight 30 second delay between the broadcast and the actual shutdown
    async def announce_restart(self, server_name):
        if self.announce_channel:
            channel = self.bot.get_channel(self.announce_channel)
            if channel:
                now = datetime.now(self.timezone)
                timestamp = now.strftime("%m-%d-%Y %H:%M:%S")
                timestamp_desc = now.strftime("%I:%M %p")
                embed = nextcord.Embed(
                    title="Server Restart",
                    description=f"The {server_name} server has been restarted at {timestamp_desc}.",
                    color=nextcord.Color.blurple(),
                )
                embed.set_footer(text=f"Time: {timestamp}")
                await channel.send(embed=embed)
            else:
                print("Announcement channel not found.")
        else:
            print("Announcement channel ID not set.")

    @shutdown_schedule.before_loop
    async def before_shutdown_schedule(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(RestartCog(bot))
