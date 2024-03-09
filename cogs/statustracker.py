import json
import os
import asyncio
import base64
from nextcord.ext import commands
import nextcord
from gamercon_async import GameRCON, GameRCONBase64

class StatusTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = {}
        self.servers = {}
        self.load_config()
        if self.config.get("STATUS_TRACKING", False):
            self.bot.loop.create_task(self.update_status())

    def load_config(self):
        config_path = os.path.join('data', 'config.json')
        with open(config_path) as config_file:
            self.config = json.load(config_file)
            self.servers = self.config.get("PALWORLD_SERVERS", {})

    def is_base64_encoded(self, s):
        try:
            if isinstance(s, str):
                s = s.encode('utf-8')
            return base64.b64encode(base64.b64decode(s)) == s
        except Exception:
            return False

    async def update_status(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed() and self.config.get("STATUS_TRACKING", False):
            total_players = await self.get_total_players()
            max_players = sum(server.get("SERVER_SLOTS", 32) for server in self.servers.values())
            status_message = f"{total_players}/{max_players} players"
            await self.bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=status_message))
            await asyncio.sleep(60)

    async def get_total_players(self):
        total_players = 0
        for server_config in self.servers.values():
            players_output = ""
            try:
                async with GameRCON(server_config["RCON_HOST"], server_config["RCON_PORT"], server_config["RCON_PASS"], timeout=15) as pc:
                    players_output = await pc.send("ShowPlayers")
            except Exception as e:
                print(f"Failed to get player count for a server: {e}")

            if self.is_base64_encoded(players_output):
                try:
                    async with GameRCONBase64(server_config["RCON_HOST"], server_config["RCON_PORT"], server_config["RCON_PASS"], timeout=15) as pc:
                        players_output = await pc.send("ShowPlayers")
                except Exception as e:
                    print(f"Failed to get player count for a server using Base64 encoding: {e}")

            players = self.parse_players(players_output)
            total_players += len(players)
        return total_players

    def parse_players(self, players_output):
        players = []
        lines = players_output.split('\n')
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) >= 3:
                players.append(parts[0])
        return players

def setup(bot):
    bot.add_cog(StatusTracker(bot))