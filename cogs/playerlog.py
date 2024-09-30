import asyncio
import nextcord
from nextcord.ext import commands
from utils.rconutility import RconUtility
import utils.constants as constants
import re
import datetime
from utils.database import (
    get_server_details,
    server_autocomplete,
    insert_player_data,
    get_player_steamids,
    get_player_names,
    get_player_profile
)
import logging
from utils.translations import t
from utils.errorhandling import restrict_command

class PlayerInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rcon_util = RconUtility()
        self.bot.loop.create_task(self.load_servers())
        self.bot.loop.create_task(self.update_players())
        self.servers = []

    async def load_servers(self):
        self.servers = await server_autocomplete()

    async def run_showplayers_command(self, server_info):
        try:
            response = await self.rcon_util.rcon_command(server_info, "ShowPlayers")
            if response:
                return response
            else:
                logging.error(f"No response from ShowPlayers command for {server_info['name']}.")
                return None
        except Exception as e:
            logging.error(f"Error sending command to {server_info['name']}: {e}")
            return None

    async def update_players(self):
        while True:
            for server_name in self.servers:
                server_info = await get_server_details(server_name)
                if server_info:
                    server_dict = {
                        'name': server_name,
                        'host': server_info[0],
                        'port': int(server_info[1]),
                        'password': server_info[2]
                    }
                    player_data = await self.run_showplayers_command(server_dict)
                    if player_data:
                        await self.process_and_save_player_data(server_name, player_data)
            await asyncio.sleep(15)

    async def process_and_save_player_data(self, server_name, data):
        if data.strip():
            for line in data.split("\n")[1:]:
                if line.strip():
                    name, playeruid, steamid = [
                        part.strip() for part in line.split(",")[:3]
                    ]
                    if self.is_valid_steamid(steamid):
                        await insert_player_data(steamid, name, playeruid)

    def is_valid_steamid(self, steamid):
        return bool(re.match(r"^7656119[0-9]{10}$", steamid))

    @nextcord.slash_command(
        description=t("PlayerInfoCog", "userdb.description"),
        default_member_permissions=nextcord.Permissions(administrator=True),
        dm_permission=False
    )
    async def userdb(self, interaction: nextcord.Interaction):
        pass

    @userdb.subcommand(name="steam", description=t("PlayerInfoCog", "userdb.search_by_steamid"))
    @restrict_command()
    async def search(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(
            description=t("PlayerInfoCog", "userdb.enter_steamid"), autocomplete=True
        ),
    ):
        player_info = await get_player_profile(steamid)
        if player_info:
            steamid, name, playeruid = player_info
            embed = nextcord.Embed(
                title=t("PlayerInfoCog", "userdb.player_info_title"), color=nextcord.Color.blue()
            )
            embed.add_field(name=t("PlayerInfoCog", "userdb.name"), value=f"```{name}```", inline=False)
            embed.add_field(name=t("PlayerInfoCog", "userdb.player_uid"), value=f"```{playeruid}```", inline=False)
            embed.add_field(name=t("PlayerInfoCog", "userdb.steamid"), value=f"```{steamid}```", inline=False)
            embed.set_footer(
                text=constants.FOOTER_TEXT, icon_url=constants.FOOTER_IMAGE
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                t("PlayerInfoCog", "userdb.no_player_found").format(steamid=steamid), ephemeral=True
            )

    @search.on_autocomplete("steamid")
    async def on_name_autocomplete(
        self, interaction: nextcord.Interaction, current: str
    ):
        choices = await get_player_steamids(current)
        await interaction.response.send_autocomplete(choices[:25])

    @userdb.subcommand(name="name", description=t("PlayerInfoCog", "userdb.search_by_name"))
    @restrict_command()
    async def searchname(
        self,
        interaction: nextcord.Interaction,
        name: str = nextcord.SlashOption(
            description=t("PlayerInfoCog", "userdb.enter_name"), autocomplete=True
        ),
    ):
        player_info = await get_player_profile(name)
        if player_info:
            steamid, name, playeruid = player_info
            embed = nextcord.Embed(
                title=t("PlayerInfoCog", "userdb.player_info_title"), color=nextcord.Color.blue()
            )
            embed.add_field(name=t("PlayerInfoCog", "userdb.name"), value=f"```{name}```", inline=False)
            embed.add_field(name=t("PlayerInfoCog", "userdb.player_uid"), value=f"```{playeruid}```", inline=False)
            embed.add_field(name=t("PlayerInfoCog", "userdb.steamid"), value=f"```{steamid}```", inline=False)
            embed.set_footer(
                text=constants.FOOTER_TEXT, icon_url=constants.FOOTER_IMAGE
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                t("PlayerInfoCog", "userdb.player_not_found").format(name=name), ephemeral=True
            )

    @searchname.on_autocomplete("name")
    async def on_name_autocomplete(
        self, interaction: nextcord.Interaction, current: str
    ):
        choices = await get_player_names(current)
        await interaction.response.send_autocomplete(choices[:25])

def setup(bot):
    cog = PlayerInfoCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.userdb
        ]
    )