import asyncio
import nextcord
from nextcord.ext import commands
from src.utils.database import (
    get_server_details,
    get_connection_port,
    server_autocomplete,
    add_query_channel,
    remove_query_channel,
    get_query_channel
)
from src.utils.rconutility import RconUtility
import src.utils.constants as constants
import re
import datetime
import logging
from src.utils.translations import t
from src.utils.errorhandling import restrict_command

class QueryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rcon_util = RconUtility()
        self.servers = []
        self.bot.loop.create_task(self.load_servers())
        self.bot.loop.create_task(self.monitor_server_status())

    async def load_servers(self):
        self.servers = await server_autocomplete()

    async def monitor_server_status(self):
        while True:
            for server_name in self.servers:
                server_info = await get_server_details(server_name)
                connection_port = await get_connection_port(server_name)
                if server_info and connection_port:
                    await self.server_status_check(server_name, server_info, connection_port)
            await asyncio.sleep(60)

    async def server_status_check(self, server_name, server_info, connection_port):
        server_dict = {
            'name': server_name,
            'host': server_info[0],
            'port': server_info[1],
            'password': server_info[2]
        }
        try:
            channel_info = await get_query_channel(server_name)
            if channel_info:
                channel_id, status_message_id, players_message_id = channel_info
                channel = self.bot.get_channel(channel_id)
                if channel:
                    status, response = await self.check_server_status(server_dict)
                    player_count = (
                        await self.get_player_count(server_dict)
                        if status == "Online"
                        else 0
                    )
                    players = (
                        await self.get_player_names(server_dict)
                        if status == "Online"
                        else []
                    )
                    version, description = await self.extract_server_info(response)

                    embed = nextcord.Embed(
                        title=t("QueryCog", "status.title").format(server=server_name),
                        description=description,
                        color=(
                            nextcord.Color.green()
                            if status == "Online"
                            else nextcord.Color.red()
                        ),
                    )
                    embed.add_field(name=t("QueryCog", "status.status"), value=status, inline=True)
                    embed.add_field(name=t("QueryCog", "status.version"), value=version, inline=True)
                    embed.add_field(
                        name=t("QueryCog", "status.players"),
                        value=f"{player_count} online",
                        inline=False,
                    )
                    embed.add_field(
                        name=t("QueryCog", "status.connection_info"),
                        value=f"```{server_dict['host']}:{connection_port}```",
                        inline=False,
                    )
                    embed.set_footer(
                        text=constants.FOOTER_TEXT, icon_url=constants.FOOTER_IMAGE
                    )

                    players_chunks = list(self.split_players(players, 11))
                    players_embed = nextcord.Embed(
                        title=t("QueryCog", "status.players_online"), color=nextcord.Color.blue()
                    )

                    for chunk in players_chunks:
                        players_list = (
                            "\n".join(chunk) if chunk else t("QueryCog", "status.no_players_online")
                        )
                        players_embed.add_field(
                            name="\u200b", value=players_list, inline=True
                        )

                    if status_message_id:
                        try:
                            message = await channel.fetch_message(status_message_id)
                            await message.edit(embed=embed)
                        except nextcord.NotFound:
                            message = await channel.send(embed=embed)
                            status_message_id = message.id
                    else:
                        message = await channel.send(embed=embed)
                        status_message_id = message.id

                    if players_message_id:
                        try:
                            player_message = await channel.fetch_message(players_message_id)
                            await player_message.edit(embed=players_embed)
                        except nextcord.NotFound:
                            player_message = await channel.send(embed=players_embed)
                            players_message_id = player_message.id
                    else:
                        player_message = await channel.send(embed=players_embed)
                        players_message_id = player_message.id

                    await add_query_channel(server_name, channel_id, status_message_id, players_message_id)

        except Exception as e:
            logging.error(f"Query: Error sending command to {server_name}: {e}")

    def split_players(self, lst, chunk_size):
        for i in range(0, len(lst), chunk_size):
            yield lst[i : i + chunk_size]

    async def check_server_status(self, server_dict):
        try:
            response = await self.rcon_util.rcon_command(server_dict, "Info")
            if "Welcome to Pal Server" in response:
                return "Online", response
            else:
                return "Offline", ""
        except Exception:
            return "Offline", ""

    async def get_player_count(self, server_dict):
        try:
            players_output = await self.rcon_util.rcon_command(server_dict, "ShowPlayers")
            if players_output:
                return len(self.parse_players(players_output))
            return 0
        except Exception:
            return 0

    async def get_player_names(self, server_dict):
        try:
            players_output = await self.rcon_util.rcon_command(server_dict, "ShowPlayers")
            if players_output:
                return self.parse_players(players_output)
            return []
        except Exception:
            return []

    def parse_players(self, players_output):
        players = []
        lines = players_output.split("\n")
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 3:
                players.append(parts[0])
        return players

    async def extract_server_info(self, response):
        try:
            match = re.search(r"Welcome to Pal Server\[v([\d.]+)\] (.+)", response)
            if match:
                version = match.group(1)
                description = match.group(2)
                return version, description
            return None, None
        except Exception:
            return None, None

    async def autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return []
        server_names = await server_autocomplete()
        choices = [server for server in server_names if current.lower() in server.lower()][:25]
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(description=t("QueryCog", "query.description"), default_member_permissions=nextcord.Permissions(administrator=True))
    async def query(self, interaction: nextcord.Interaction):
        pass

    @query.subcommand(name="add", description=t("QueryCog", "query.add.description"))
    @restrict_command()
    async def querylogs(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel, server: str = nextcord.SlashOption(description=t("QueryCog", "query.add.server_description"), autocomplete=True)):
        await interaction.response.defer(ephemeral=True)
        success = await add_query_channel(server, channel.id, None, None)
        if success:
            await interaction.followup.send(t("QueryCog", "query.add.success").format(server=server), ephemeral=True)
        else:
            await interaction.followup.send(t("QueryCog", "query.add.failed").format(server=server), ephemeral=True)

    @querylogs.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)
        
    @query.subcommand(name="remove", description=t("QueryCog", "query.remove.description"))
    @restrict_command()
    async def removequerylogs(self, interaction: nextcord.Interaction, server: str = nextcord.SlashOption(description=t("QueryCog", "query.remove.server_description"), autocomplete=True)):
        await interaction.response.defer(ephemeral=True)
        success = await remove_query_channel(server)
        if success:
            await interaction.followup.send(t("QueryCog", "query.remove.success").format(server=server), ephemeral=True)
        else:
            await interaction.followup.send(t("QueryCog", "query.remove.failed").format(server=server), ephemeral=True)

    @removequerylogs.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

def setup(bot):
    cog = QueryCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.query
        ]
    )
