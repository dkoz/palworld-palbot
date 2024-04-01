import asyncio
import json
import nextcord
from nextcord.ext import commands
from util.rconutility import RconUtility
import datetime

class ConnectCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.servers = self.load_config()
        self.rcon_util = RconUtility(self.servers)
        self.last_seen_players = {}
        self.player_names = {}
        self.bot.loop.create_task(self.monitor_player_activity())

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config["PALWORLD_SERVERS"]

    async def run_command(self, server_name):
        try:
            response = await self.rcon_util.rcon_command(server_name, "ShowPlayers")
            return response
        except Exception as e:
            print(f"Error sending command to {server_name}: {e}")
            return ""

    async def monitor_player_activity(self):
        while True:
            for server_name, server_info in self.servers.items():
                current_players = await self.run_command(server_name)
                if current_players:
                    await self.announce_player_changes(server_name, current_players)
            await asyncio.sleep(13)

    async def announce_player_changes(self, server_name, current_players):
        new_player_data = self.extract_players(current_players)
        new_players = {steamid for _, steamid in new_player_data}
        
        last_seen = self.last_seen_players.get(server_name, set())

        joined_players = new_players - last_seen
        left_players = last_seen - new_players

        for steamid in joined_players:
            player_name = next((name for name, sid in new_player_data if sid == steamid), "Unknown Player")
            self.player_names[steamid] = player_name
            await self.announce_player_join(server_name, player_name, steamid)

        for steamid in left_players:
            player_name = self.player_names.get(steamid, "Unknown Player")
            await self.announce_player_leave(server_name, player_name, steamid)

        self.last_seen_players[server_name] = new_players

    def extract_players(self, player_data):
        players = set()
        lines = player_data.split("\n")[1:]
        for line in lines:
            if line.strip():
                parts = line.split(",")
                if len(parts) == 3:
                    name, _, steamid = parts
                    players.add((name.strip(), steamid.strip()))
        return players

    async def announce_player_join(self, server_name, player_name, steamid):
        channel_id = self.servers[server_name].get("CONNECTION_CHANNEL")
        channel = self.bot.get_channel(channel_id)
        if channel:
            now = datetime.datetime.now()
            timestamp = now.strftime("%m-%d-%Y at %I:%M:%S %p")
            embed = nextcord.Embed(
                title="Player Joined",
                description=f"Player joined {server_name}: {player_name} (SteamID: {steamid})",
                color=nextcord.Color.blurple(),
            )
            embed.set_footer(text=f"Time: {timestamp}")
            await channel.send(embed=embed)

    async def announce_player_leave(self, server_name, player_name, steamid):
        channel_id = self.servers[server_name].get("CONNECTION_CHANNEL")
        channel = self.bot.get_channel(channel_id)
        if channel:
            now = datetime.datetime.now()
            timestamp = now.strftime("%m-%d-%Y at %I:%M:%S %p")
            embed = nextcord.Embed(
                title="Player Left",
                description=f"Player left {server_name}: {player_name} (SteamID: {steamid})",
                color=nextcord.Color.red(),
            )
            embed.set_footer(text=f"Time: {timestamp}")
            await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(ConnectCog(bot))