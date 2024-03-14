import json
import os
import asyncio
import nextcord
from nextcord.ext import commands
from util.rconutility import RconUtility
import util.constants as constants
import re
import datetime

class PlayerInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_folder = 'data'
        self.player_data_file = os.path.join(self.data_folder, 'players.json')
        self.servers = self.load_servers_config()
        self.rcon_util = RconUtility(self.servers)
        self.ensure_data_file()
        self.bot.loop.create_task(self.update_players())

    def load_servers_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            config = json.load(config_file)
            return config["PALWORLD_SERVERS"]

    def ensure_data_file(self):
        if not os.path.exists(self.player_data_file):
            with open(self.player_data_file, 'w') as file:
                json.dump({}, file)

    async def run_showplayers_command(self, server_name):
        try:
            response = await self.rcon_util.rcon_command(server_name, "ShowPlayers")
            if response:
                return response
            else:
                print(f"No response from ShowPlayers command for {server_name}.")
                return None
        except Exception as e:
            print(f"Exception sending ShowPlayers command for {server_name}: {e}")
            return None

    async def update_players(self):
        while True:
            for server_name in self.servers.keys():
                player_data = await self.run_showplayers_command(server_name)
                if player_data:
                    self.process_and_save_player_data(server_name, player_data)
                    if self.servers[server_name].get('WHITELIST_ENABLED', False):
                        await self.whitelist_check(server_name, player_data)
            await asyncio.sleep(15)

    async def whitelist_check(self, server_name, player_data):
        with open(self.player_data_file) as file:
            players = json.load(file)

        for line in player_data.split('\n')[1:]:
            if line.strip():
                _, playeruid, steamid = line.split(',')[:3]
                if not any(info.get("whitelist", False) for player, info in players.items() if info.get("playeruid") == playeruid):
                    await self.kick_player(server_name, steamid, playeruid=playeruid)

    async def kick_player(self, server_name, steamid, playeruid=None, reason="not being whitelisted"):
        try:
            identifier = steamid if steamid and self.is_valid_steamid(steamid) else playeruid
            command = f"KickPlayer {identifier}"
            
            result = await self.rcon_util.rcon_command(server_name, command)
            
            if "Failed" in result:
                print(f"Failed to execute kick command for {identifier} on {server_name}: {result}")
            else:
                print(f"Successfully executed kick command for {identifier} on {server_name}: {result}")
            
            server_info = self.servers[server_name]
            if "CONNECTION_CHANNEL" in server_info:
                channel = self.bot.get_channel(server_info["CONNECTION_CHANNEL"])
                if channel:
                    embed_description = f"Player `{identifier}` kicked for {reason}." if "Failed" not in result else f"Failed to kick Player `{identifier}`: {reason}."
                    embed = nextcord.Embed(title="Whitelist Check", description=embed_description, color=nextcord.Color.red() if "Failed" in result else nextcord.Color.green())
                    embed.set_footer(text=f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    await channel.send(embed=embed)
        except Exception as e:
            print(f"Exception during kick command for {identifier} on {server_name}: {e}")

    def is_valid_steamid(self, steamid):
        return bool(re.match(r'^7656119[0-9]{10}$', steamid))

    def process_and_save_player_data(self, server_name, data):
        if data.strip():
            with open(self.player_data_file, 'r+') as file:
                existing_players = json.load(file)
                for line in data.split('\n')[1:]:
                    if line.strip():
                        name, playeruid, steamid = [part.strip() for part in line.split(',')[:3]]
                        if self.is_valid_steamid(steamid):
                            existing_players[steamid] = {"name": name, "playeruid": playeruid, "whitelist": existing_players.get(steamid, {}).get("whitelist", False)}
                file.seek(0)
                json.dump(existing_players, file)
                file.truncate()

    @nextcord.slash_command(description="Search the user database.", default_member_permissions=nextcord.Permissions(administrator=True))
    async def paldb(self, interaction: nextcord.Interaction):
        pass

    async def steamid_autocomplete(self, interaction: nextcord.Interaction, current: str):
        with open(self.player_data_file, 'r') as file:
            players = json.load(file)

        matches = [steamid for steamid in players if current.lower() in steamid.lower()]
        return matches[:25]

    @paldb.subcommand(name="steam", description="Find player by SteamID")
    async def search(self, interaction: nextcord.Interaction, steamid: str = nextcord.SlashOption(description="Enter SteamID", autocomplete=True)):
        with open(self.player_data_file, 'r') as file:
            players = json.load(file)

        player_info = players.get(steamid)
        if player_info:
            embed = nextcord.Embed(title="Player Information", color=nextcord.Color.blue())
            embed.add_field(name="Name", value=f"```{player_info['name']}```", inline=False)
            embed.add_field(name="Player UID", value=f"```{player_info['playeruid']}```", inline=False)
            embed.add_field(name="SteamID", value=f"```{steamid}```", inline=False)
            embed.add_field(name="Whitelist", value=f"```{str(player_info['whitelist'])}```", inline=False)
            embed.set_footer(text=constants.FOOTER_TEXT, icon_url=constants.FOOTER_IMAGE)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No player found with SteamID {steamid}", ephemeral=True)

    @search.on_autocomplete("steamid")
    async def on_steamid_autocomplete(self, interaction: nextcord.Interaction, current: str):
        choices = await self.steamid_autocomplete(interaction, current)
        await interaction.response.send_autocomplete(choices)

    async def name_autocomplete(self, interaction: nextcord.Interaction, current: str):
        with open(self.player_data_file, 'r') as file:
            players = json.load(file)

        matches = [player["name"] for steamid, player in players.items() if player["name"] and current.lower() in player["name"].lower()]
        return matches[:25]

    @paldb.subcommand(name="name", description="Find player by name")
    async def searchname(self, interaction: nextcord.Interaction, name: str = nextcord.SlashOption(description="Enter player name", autocomplete=True)):
        with open(self.player_data_file, 'r') as file:
            players = json.load(file)

        player_info = None
        player_steamid = None
        for steamid, player in players.items():
            if player.get("name") and player["name"].lower() == name.lower():
                player_info = player
                player_steamid = steamid
                break

        if player_info and player_steamid:
            embed = nextcord.Embed(title="Player Information", color=nextcord.Color.blue())
            embed.add_field(name="Name", value=f"```{player_info['name']}```", inline=False)
            embed.add_field(name="Player UID", value=f"```{player_info['playeruid']}```", inline=False)
            embed.add_field(name="SteamID", value=f"```{player_steamid}```", inline=False)
            embed.add_field(name="Whitelist", value=f"```{str(player_info['whitelist'])}```", inline=False)
            embed.set_footer(text=constants.FOOTER_TEXT, icon_url=constants.FOOTER_IMAGE)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No player found with name '{name}'", ephemeral=True)

    @searchname.on_autocomplete("name")
    async def on_name_autocomplete(self, interaction: nextcord.Interaction, current: str):
        choices = await self.name_autocomplete(interaction, current)
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(description="Manage the whitelist", default_member_permissions=nextcord.Permissions(administrator=True))
    async def whitelist(self, interaction: nextcord.Interaction):
        pass

    @whitelist.subcommand(name="add", description="Add player to whitelist")
    async def whitelist_add(self, interaction: nextcord.Interaction, steamid: str = nextcord.SlashOption(description="Enter SteamID", required=True), playeruid: str = nextcord.SlashOption(description="Enter PlayerUID", required=False)):
        if not steamid and not playeruid:
            await interaction.response.send_message("Please provide either a SteamID or PlayerUID.", ephemeral=True)
            return

        identifier = steamid if steamid else playeruid
        with open(self.player_data_file, 'r+') as file:
            players = json.load(file)

            if identifier not in players:
                players[identifier] = {"name": None, "playeruid": playeruid if playeruid else None, "whitelist": True}
                file.seek(0)
                json.dump(players, file)
                file.truncate()
                message = f"Player {identifier} added to whitelist and will be fully registered upon joining." if steamid else f"Player with PlayerUID {playeruid} added to whitelist and will be fully registered upon joining."
            else:
                players[identifier]["whitelist"] = True
                if playeruid:
                    players[identifier]["playeruid"] = playeruid
                file.seek(0)
                json.dump(players, file)
                file.truncate()
                message = f"Player {identifier} added to whitelist." if steamid else f"Player with PlayerUID {playeruid} added to whitelist."

        await interaction.response.send_message(message, ephemeral=True)

    @whitelist.subcommand(name="remove", description="Remove player from whitelist")
    async def whitelist_remove(self, interaction: nextcord.Interaction, steamid: str):
        with open(self.player_data_file, 'r') as file:
            players = json.load(file)

        if steamid in players and players[steamid]["whitelist"]:
            players[steamid]["whitelist"] = False
            with open(self.player_data_file, 'w') as file:
                json.dump(players, file)
            await interaction.response.send_message(f"Player {steamid} removed from whitelist.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Player {steamid} not found or not on whitelist.", ephemeral=True)

def setup(bot):
    cog = PlayerInfoCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, 'all_slash_commands'):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend([
        cog.search,
        cog.searchname,
        cog.whitelist_add,
        cog.whitelist_remove
    ])