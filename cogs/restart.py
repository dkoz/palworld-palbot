import json
import os
from datetime import datetime, timedelta
import nextcord
from nextcord.ext import commands, tasks
import pytz
from gamercon_async import GameRCON, GameRCONBase64
import base64
import datetime

class RestartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.shutdown_schedule.start()

    def load_config(self):
        config_path = os.path.join('data', 'config.json')
        with open(config_path) as config_file:
            config = json.load(config_file)
            self.servers = config.get("PALWORLD_SERVERS", {})
            self.shutdown_config = config.get("SHUTDOWN_SCHEDULE", {})
            self.timezone = pytz.timezone(self.shutdown_config.get("timezone", "UTC"))
            self.announce_channel = self.shutdown_config.get("channel", None)

    def is_base64_encoded(self, s):
        try:
            if isinstance(s, str):
                s = s.encode('utf-8')
            return base64.b64encode(base64.b64decode(s)) == s
        except Exception:
            return False

    async def rcon_command(self, server_info, command):
        async def send_rcon_command(rcon_class):
            try:
                async with rcon_class(server_info["RCON_HOST"], server_info["RCON_PORT"], server_info["RCON_PASS"], timeout=10) as rcon:
                    response = await rcon.send(command)
                    if self.is_base64_encoded(response):
                        return None
                    return response
            except Exception as e:
                return f"Error sending command: {e}"

        response = await send_rcon_command(GameRCON)
        if response is None:
            response = await send_rcon_command(GameRCONBase64)
        return response

    @tasks.loop(seconds=60)
    async def shutdown_schedule(self):
        now_utc = datetime.now(pytz.utc)
        now_local = now_utc.astimezone(self.timezone)
        if self.shutdown_config.get("enabled", False):
            for shutdown_time_str in self.shutdown_config.get("times", []):
                shutdown_time = datetime.strptime(shutdown_time_str, "%H:%M").time()
                shutdown_datetime_local = datetime.now(self.timezone).replace(hour=shutdown_time.hour, minute=shutdown_time.minute, second=0, microsecond=0)
                if shutdown_datetime_local < now_local:
                    shutdown_datetime_local += timedelta(days=1)
                time_until_shutdown = (shutdown_datetime_local - now_local).total_seconds()

                if 300 <= time_until_shutdown < 360:  # 5 minutes before
                    await self.broadcast_warning("Server_restart_in_5_minutes")
                elif 180 <= time_until_shutdown < 240:  # 3 minutes before
                    await self.broadcast_warning("Server_restart_in_3_minutes")
                elif 120 <= time_until_shutdown < 180:
                    await self.save_server_state() # Save the server state
                elif 60 <= time_until_shutdown < 120:
                    await self.initiate_shutdown("Shutdown 60 Server_restart_in_1_minute")

    async def broadcast_warning(self, message):
        for server_name, server_info in self.servers.items():
            await self.rcon_command(server_info, f"Broadcast {message}")
            print(f"Broadcasted to {server_name}: {message}")

    async def save_server_state(self):
        for server_name, server_info in self.servers.items():
            response = await self.rcon_command(server_info, "Save")
            print(f"State saved for {server_name}: {response}")

    async def initiate_shutdown(self, command):
        for server_name, server_info in self.servers.items():
            response = await self.rcon_command(server_info, command)
            print(f"Shutdown initiated for {server_name}: {response}")
        await self.announce_restart()

    async def announce_restart(self):
        if self.announce_channel:
            channel = self.bot.get_channel(self.announce_channel)
            if channel:
                now = datetime.datetime.now()
                timestamp = now.strftime("%m-%d-%Y at %I:%M:%S %p")
                thetime = now.strftime("%I:%M %p")
                embed = nextcord.Embed(title="Server Restarted", description=f"The server has been restarted at {thetime}.", color=nextcord.Color.blurple())
                embed = embed.set_footer(text=f"Time: {timestamp}")
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
