import json
import asyncio
from nextcord.ext import commands
import nextcord
from util.rconutility import RconUtility

class StatusTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = {}
        self.servers = {}
        self.load_config()
        self.rcon_util = RconUtility(self.servers)
        if self.config.get("STATUS_TRACKING", False):
            self.bot.loop.create_task(self.update_status())

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            self.config = json.load(config_file)
            self.servers = self.config.get("PALWORLD_SERVERS", {})

    async def update_status(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed() and self.config.get("STATUS_TRACKING", False):
            total_players = await self.get_total_players()
            max_players = sum(
                server.get("SERVER_SLOTS", 32) for server in self.servers.values()
            )
            status_message = f"{total_players}/{max_players} players"
            await self.bot.change_presence(
                activity=nextcord.Activity(
                    type=nextcord.ActivityType.watching, name=status_message
                )
            )
            await asyncio.sleep(60)

    async def get_total_players(self):
        total_players = 0
        for server_name in self.servers:
            try:
                players_output = await self.rcon_util.rcon_command(
                    server_name, "ShowPlayers"
                )
                players = self.parse_players(players_output)
                total_players += len(players)
            except Exception as e:
                print(f"Failed to get player count for server '{server_name}': {e}")
        return total_players

    def parse_players(self, players_output):
        players = []
        lines = players_output.split("\n")
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 3:
                players.append(parts[0])
        return players

def setup(bot):
    bot.add_cog(StatusTracker(bot))