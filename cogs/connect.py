import asyncio
import nextcord
from nextcord.ext import commands
from utils.database import (
    get_server_details,
    server_autocomplete,
    add_event_channel,
    remove_event_channel,
    get_event_channel,   
)
from utils.rconutility import RconUtility
import datetime

class ConnectCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rcon_util = RconUtility()
        self.servers = []
        self.last_seen_players = {}
        self.player_names = {}
        self.bot.loop.create_task(self.load_servers())
        self.bot.loop.create_task(self.monitor_player_activity())

    async def load_servers(self):
        self.servers = await server_autocomplete()

    async def monitor_player_activity(self):
        while True:
            for server_name in self.servers:
                server_info = await get_server_details(server_name)
                if server_info and len(server_info) == 3:
                    response = await self.run_command(server_info, server_name)
                    if response:
                        await self.announce_player_changes(server_name, response)
            await asyncio.sleep(13)

    async def run_command(self, server_info, server_name):
        server_dict = {
            'name': server_name,
            'host': server_info[0],
            'port': server_info[1],
            'password': server_info[2]
        }
        try:
            response = await self.rcon_util.rcon_command(server_dict, "ShowPlayers")
            return response
        except Exception as e:
            print(f"Error sending command to {server_name}: {e}")
            return ""

    # Major pain in my ass
    async def announce_player_changes(self, server_name, current_players):
        try:
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
        except Exception as e:
            print(f"Error announcing player changes for {server_name}: {e}")

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
        try:
            channel_id = await get_event_channel(server_name)
            if channel_id:
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
                else:
                    print(f"Channel with ID {channel_id} not found for server {server_name}")
            else:
                print(f"No event channel set for server {server_name}")
        except Exception as e:
            print(f"Error announcing player join for {server_name}: {e}")

    async def announce_player_leave(self, server_name, player_name, steamid):
        try:
            channel_id = await get_event_channel(server_name)
            if channel_id:
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
                else:
                    print(f"Channel with ID {channel_id} not found for server {server_name}")
            else:
                print(f"No event channel set for server {server_name}")
        except Exception as e:
            print(f"Error announcing player leave for {server_name}: {e}")

    async def autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        choices = [server for server in self.servers if current.lower() in server.lower()]
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(description="Set a channel to log server events.")
    async def eventlogs(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel, server: str = nextcord.SlashOption(description="Select a server.", autocomplete=True)):
        await interaction.response.defer(ephemeral=True)
        success = await add_event_channel(server, channel.id)
        if success:
            await interaction.followup.send(f"Event logging channel set for {server}.", ephemeral=True)
        else:
            await interaction.followup.send(f"Failed to set event logging channel for {server}.", ephemeral=True)

    @eventlogs.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    # Did not test this yet. lol
    @nextcord.slash_command(description="Remove a channel from logging server events.")
    async def removeeventlogs(self, interaction: nextcord.Interaction, server: str = nextcord.SlashOption(description="Select a server.", autocomplete=True)):
        await interaction.response.defer(ephemeral=True)
        success = await remove_event_channel(server)
        if success:
            await interaction.followup.send(f"Event logging channel removed for {server}.", ephemeral=True)
        else:
            await interaction.followup.send(f"Failed to remove event logging channel for {server}.", ephemeral=True)
            
    @removeeventlogs.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

def setup(bot):
    bot.add_cog(ConnectCog(bot))
