import json
import os
import nextcord
from nextcord.ext import commands
from util.rconutility import RconUtility
import util.constants as constants
import asyncio
import re

class QueryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.servers = {}
        self.message_ids = {}
        self.load_config()
        self.load_message_ids()
        self.rcon_util = RconUtility(self.servers)
        self.create_task()

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            config = json.load(config_file)
        self.servers = config["PALWORLD_SERVERS"]

    def load_message_ids(self):
        ids_path = os.path.join('data', 'server_status.json')
        if os.path.exists(ids_path):
            with open(ids_path) as ids_file:
                self.message_ids = json.load(ids_file)
                
    def save_message_ids(self):
        with open(os.path.join('data', 'server_status.json'), 'w') as file:
            json.dump(self.message_ids, file, indent=4)

    def create_task(self):
        for server_name in self.servers:
            self.bot.loop.create_task(self.server_status_check(server_name))

    # Split player list into chunks
    def split_players(self, lst, chunk_size):
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    async def server_status_check(self, server_name):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                channel_id = self.servers[server_name].get("QUERY_CHANNEL")
                channel = self.bot.get_channel(channel_id)
                if channel:
                    status = await self.check_server_status(server_name)
                    player_count = await self.get_player_count(server_name) if status == "Online" else 0
                    players = await self.get_player_names(server_name) if status == "Online" else []
                    version, description = await self.extract_server_info(server_name)

                    server_config = self.servers[server_name]
                    max_players = server_config.get('SERVER_SLOTS', 32)

                    embed = nextcord.Embed(title=f"{server_name} Status", description=description, 
                                        color=nextcord.Color.green() if status == "Online" else nextcord.Color.red())
                    embed.add_field(name="Status", value=status, inline=True)
                    embed.add_field(name="Version", value=version, inline=True)
                    embed.add_field(name="Players", value=f"{player_count}/{max_players}", inline=False)
                    embed.add_field(name="Connection Info", value=f"```{server_config['RCON_HOST']}:{server_config['SERVER_PORT']}```", inline=False)
                    embed.set_footer(text=constants.FOOTER_TEXT, icon_url=constants.FOOTER_IMAGE)

                    players_chunks = list(self.split_players(players, 11))
                    players_embed = nextcord.Embed(title=f"Players Online", color=nextcord.Color.blue())
                    
                    for chunk in players_chunks:
                        players_list = '\n'.join(chunk) if chunk else "No players online."
                        players_embed.add_field(name="\u200b", value=players_list, inline=True)

                    message_key = f"{server_name}_{channel_id}"
                    message_id = self.message_ids.get(message_key)
                    if message_id:
                        try:
                            message = await channel.fetch_message(message_id)
                            await message.edit(embed=embed)
                        except nextcord.NotFound:
                            message = await channel.send(embed=embed)
                            self.message_ids[message_key] = message.id
                    else:
                        message = await channel.send(embed=embed)
                        self.message_ids[message_key] = message.id

                    player_message_key = f"{server_name}_{channel_id}_players"
                    player_message_id = self.message_ids.get(player_message_key)
                    if player_message_id:
                        try:
                            player_message = await channel.fetch_message(player_message_id)
                            await player_message.edit(embed=players_embed)
                        except nextcord.NotFound:
                            player_message = await channel.send(embed=players_embed)
                            self.message_ids[player_message_key] = player_message.id
                    else:
                        player_message = await channel.send(embed=players_embed)
                        self.message_ids[player_message_key] = player_message.id

                    self.save_message_ids()
            except Exception as e:
                print(f"An error occurred: {e}")
            await asyncio.sleep(60)

    async def check_server_status(self, server_name):
        try:
            response = await self.rcon_util.rcon_command(server_name, "Info")
            if "Welcome to Pal Server" in response:
                return "Online"
            else:
                return "Offline"
        except Exception:
            return "Offline"

    async def get_player_count(self, server_name):
        try:
            players_output = await self.rcon_util.rcon_command(server_name, "ShowPlayers")
            if players_output:
                return len(self.parse_players(players_output))
            return 0
        except Exception:
            return 0

    async def get_player_names(self, server_name):
        try:
            players_output = await self.rcon_util.rcon_command(server_name, "ShowPlayers")
            if players_output:
                return self.parse_players(players_output)
            return []
        except Exception:
            return []

    def parse_players(self, players_output):
        players = []
        lines = players_output.split('\n')
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) >= 3:
                players.append(parts[0])
        return players
    
    async def extract_server_info(self, server_name):
        try:
            response = await self.rcon_util.rcon_command(server_name, "Info")
            match = re.search(r"Welcome to Pal Server\[v([\d.]+)\] (.+)", response)
            if match:
                version = match.group(1)
                description = match.group(2)
                return version, description
            return None, None
        except Exception:
            return None, None

def setup(bot):
    bot.add_cog(QueryCog(bot))
