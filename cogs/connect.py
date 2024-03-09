import asyncio
import json
import os
import nextcord
from nextcord.ext import commands
from gamercon_async import GameRCON, GameRCONBase64
import base64

class ConnectCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.servers = self.load_config()
        self.last_seen_players = {}
        self.bot.loop.create_task(self.monitor_player_activity())

    def load_config(self):
        config_path = os.path.join('data', 'config.json')
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config["PALWORLD_SERVERS"]
    
    def is_base64_encoded(self, s):
        try:
            if isinstance(s, str):
                s = s.encode('utf-8')
            return base64.b64encode(base64.b64decode(s)) == s
        except Exception:
            return False

    async def run_command(self, server):
        try:
            async with GameRCON(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"], timeout=10) as rcon:
                response = await rcon.send("ShowPlayers")
                if self.is_base64_encoded(response):
                    async with GameRCONBase64(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"], timeout=10) as rcon:
                        response = await rcon.send("ShowPlayers")
                return response
        except Exception as e:
            print(f"Error sending command: {e}")

    async def monitor_player_activity(self):
        while True:
            for server_name, server_info in self.servers.items():
                current_players = await self.run_command(server_info)
                if current_players:
                    await self.announce_player_changes(server_name, current_players)
            await asyncio.sleep(18)

    async def announce_player_changes(self, server_name, current_players):
        new_players = self.extract_players(current_players)
        last_seen = self.last_seen_players.get(server_name, set())

        joined_players = new_players - last_seen
        left_players = last_seen - new_players

        for player in joined_players:
            await self.announce_player_join(server_name, player)

        for player in left_players:
            await self.announce_player_leave(server_name, player)

        self.last_seen_players[server_name] = new_players

    def extract_players(self, player_data):
        players = set()
        lines = player_data.split('\n')[1:]
        for line in lines:
            if line.strip():
                parts = line.split(',')
                if len(parts) == 3:
                    name, _, steamid = parts
                    players.add((name.strip(), steamid.strip()))
        return players

    async def announce_player_join(self, server_name, player):
        name, steamid = player
        if "CONNECTION_CHANNEL" in self.servers[server_name]:
            announcement_channel_id = self.servers[server_name]["CONNECTION_CHANNEL"]
            channel = self.bot.get_channel(announcement_channel_id)
            if channel:
                embed = nextcord.Embed(title="Player Joined", description=f"Player joined {server_name}: {name} (SteamID: {steamid})", color=nextcord.Color.blurple())
                await channel.send(embed=embed)

    async def announce_player_leave(self, server_name, player):
        name, steamid = player
        if "CONNECTION_CHANNEL" in self.servers[server_name]:
            announcement_channel_id = self.servers[server_name]["CONNECTION_CHANNEL"]
            channel = self.bot.get_channel(announcement_channel_id)
            if channel:
                embed = nextcord.Embed(title="Player Left", description=f"Player left {server_name}: {name} (SteamID: {steamid})", color=nextcord.Color.red())
                await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(ConnectCog(bot))