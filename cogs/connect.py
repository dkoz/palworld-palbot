import asyncio
import json
import os
from nextcord.ext import commands
from util.gamercon_async import GameRCON

class ConnectCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.servers = self.load_config()
        self.last_seen_players = {}
        self.bot.loop.create_task(self.monitor_player_joins())

    def load_config(self):
        config_path = os.path.join('data', 'config.json')
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config["PALWORLD_SERVERS"]

    async def run_command(self, server):
        try:
            async with GameRCON(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"], timeout=10) as pc:
                response = await asyncio.wait_for(pc.send("ShowPlayers"), timeout=10.0)
                return response
        except Exception as e:
            print(f"Error executing ShowPlayers command: {e}")
            return None

    async def monitor_player_joins(self):
        while True:
            for server_name, server_info in self.servers.items():
                current_players = await self.run_command(server_info)
                if current_players:
                    await self.announce_new_players(server_name, current_players)
            await asyncio.sleep(18)

    async def announce_new_players(self, server_name, current_players):
        new_players = self.extract_players(current_players)
        last_seen = self.last_seen_players.get(server_name, set())

        for player in new_players - last_seen:
            await self.announce_player_join(server_name, player)

        self.last_seen_players[server_name] = new_players

    # Pain in my ass
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
            # This message needs to be formatted better.
            if channel:
                await channel.send(f"`Player joined on {server_name}: {name} (SteamID: {steamid})`")

def setup(bot):
    bot.add_cog(ConnectCog(bot))
