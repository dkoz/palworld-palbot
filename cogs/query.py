import json
import os
import nextcord
from nextcord.ext import commands, tasks
from util.gamercon_async import GameRCON
import util.constants as constants

class QueryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_ids = {}
        self.load_config()
        self.load_message_ids()
        self.server_status_checks = []
        for server_name, server_config in self.servers.items():
            self.server_status_checks.append(self.create_task(server_name, server_config))
        for task in self.server_status_checks:
            task.start()

    def load_config(self):
        config_path = os.path.join('data', 'config.json')
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

    def create_task(self, server_name, server_config):
        @tasks.loop(minutes=2)
        async def server_status_check():
            if "QUERY_CHANNEL" in server_config:
                channel_id = server_config["QUERY_CHANNEL"]
                channel = self.bot.get_channel(channel_id)
                if channel:
                    status = await self.check_server_status(server_config)
                    player_count = await self.get_player_count(server_config) if status == "Online" else 0

                    embed = nextcord.Embed(title=f"{server_name} Status", description=f"**Status:** {status}", color=nextcord.Color.green())
                    embed.add_field(name="Players", value=f"{player_count}/32", inline=False)
                    embed.add_field(name="Connection Info", value=f"```{server_config['RCON_HOST']}:{server_config['SERVER_PORT']}```", inline=False)
                    embed.set_footer(text=constants.FOOTER_TEXT, icon_url=constants.FOOTER_IMAGE)

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

                if status == "Online":
                    players = await self.get_player_names(server_config)
                    if players:
                        player_list = '\n'.join(players)
                        description = f"{player_list}"
                    else:
                        description = "No players online"
                else:
                    description = "Server Offline"

                players_embed = nextcord.Embed(title=f"Players Online", description=description, color=nextcord.Color.blue())

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

        @server_status_check.before_loop
        async def before_server_status_check():
            await self.bot.wait_until_ready()

        return server_status_check

    async def check_server_status(self, server_config):
        try:
            async with GameRCON(server_config["RCON_HOST"], server_config["RCON_PORT"], server_config["RCON_PASS"]) as pc:
                return "Online"
        except Exception:
            return "Offline"

    async def get_player_count(self, server_config):
        try:
            async with GameRCON(server_config["RCON_HOST"], server_config["RCON_PORT"], server_config["RCON_PASS"]) as pc:
                players_output = await pc.send("ShowPlayers")
                return len(self.parse_players(players_output))
        except Exception:
            return 0
        
    async def get_player_names(self, server_config):
        try:
            async with GameRCON(server_config["RCON_HOST"], server_config["RCON_PORT"], server_config["RCON_PASS"]) as pc:
                players_output = await pc.send("ShowPlayers")
                return self.parse_players(players_output)
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

def setup(bot):
    bot.add_cog(QueryCog(bot))
