import nextcord
from nextcord.ext import commands
from utils.rconutility import RconUtility
import utils.constants as constants
import datetime
from utils.database import get_server_details, server_autocomplete
from utils.translations import t

class PalconCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_servers())
        self.rcon_util = RconUtility()
        self.servers = []

    async def load_servers(self):
        self.servers = await server_autocomplete()

    async def autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        choices = [server for server in self.servers if current.lower() in server.lower()]
        await interaction.response.send_autocomplete(choices)

    async def get_server_info(self, server_name: str):
        details = await get_server_details(server_name)
        if details:
            return {
                "name": server_name,
                "host": details[0],
                "port": details[1],
                "password": details[2]
            }
        return None

    @nextcord.slash_command(
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    async def palcon(self, interaction: nextcord.Interaction):
        await self.load_servers()

    @palcon.subcommand(description=t("PalconCog", "command.description"))
    async def command(
        self,
        interaction: nextcord.Interaction,
        command: str,
        server: str = nextcord.SlashOption(
            description=t("PalconCog", "command.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("PalconCog", "command.server_not_found").format(server=server), ephemeral=True)
            return
        response = await self.rcon_util.rcon_command(server_info, command)
        embed = nextcord.Embed(title=server, color=nextcord.Color.green())
        embed.description = t("PalconCog", "command.response").format(response=response)
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @command.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description=t("PalconCog", "showplayers.description"))
    async def showplayers(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description=t("PalconCog", "command.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("PalconCog", "command.server_not_found").format(server=server), ephemeral=True)
            return
        response = await self.rcon_util.rcon_command(server_info, "ShowPlayers")
        embed = nextcord.Embed(
            title=t("PalconCog", "showplayers.title").format(server=server), color=nextcord.Color.red()
        )
        embed.description = response
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @showplayers.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description=t("PalconCog", "kickplayer.description"))
    async def kickplayer(
        self,
        interaction: nextcord.Interaction,
        steamid: str,
        server: str = nextcord.SlashOption(
            description=t("PalconCog", "command.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("PalconCog", "command.server_not_found").format(server=server), ephemeral=True)
            return
        response = await self.rcon_util.rcon_command(server_info, f"KickPlayer steam_{steamid}")
        embed = nextcord.Embed(
            title=t("PalconCog", "kickplayer.title").format(server=server), color=nextcord.Color.orange()
        )
        embed.add_field(name="Server", value=server, inline=True)
        embed.add_field(name="SteamID", value=steamid, inline=True)
        embed.add_field(name="Response", value=response, inline=False)
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @kickplayer.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description=t("PalconCog", "banplayer.description"))
    async def banplayer(
        self,
        interaction: nextcord.Interaction,
        steamid: str,
        server: str = nextcord.SlashOption(
            description=t("PalconCog", "command.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("PalconCog", "command.server_not_found").format(server=server), ephemeral=True)
            return
        response = await self.rcon_util.rcon_command(server_info, f"BanPlayer steam_{steamid}")
        embed = nextcord.Embed(
            title=t("PalconCog", "banplayer.title").format(server=server), color=nextcord.Color.red()
        )
        embed.add_field(name="Server", value=server, inline=True)
        embed.add_field(name="SteamID", value=steamid, inline=True)
        embed.add_field(name="Response", value=response, inline=False)
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @banplayer.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description=t("PalconCog", "unbanplayer.description"))
    async def unbanplayer(
        self,
        interaction: nextcord.Interaction,
        steamid: str,
        server: str = nextcord.SlashOption(
            description=t("PalconCog", "command.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("PalconCog", "command.server_not_found").format(server=server), ephemeral=True)
            return
        response = await self.rcon_util.rcon_command(server_info, f"UnBanPlayer steam_{steamid}")
        embed = nextcord.Embed(
            title=t("PalconCog", "unbanplayer.title").format(server=server), color=nextcord.Color.red()
        )
        embed.add_field(name="Server", value=server, inline=True)
        embed.add_field(name="SteamID", value=steamid, inline=True)
        embed.add_field(name="Response", value=response, inline=False)
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @unbanplayer.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description=t("PalconCog", "info.description"))
    async def info(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description=t("PalconCog", "command.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("PalconCog", "command.server_not_found").format(server=server), ephemeral=True)
            return
        response = await self.rcon_util.rcon_command(server_info, f"Info")
        embed = nextcord.Embed(title=t("PalconCog", "info.title").format(server=server), color=nextcord.Color.blue())
        embed.description = t("PalconCog", "command.response").format(response=response)
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @info.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description=t("PalconCog", "shutdown.description"))
    async def shutdown(
        self,
        interaction: nextcord.Interaction,
        time: str = nextcord.SlashOption(description=t("PalconCog", "shutdown.time_description")),
        reason: str = nextcord.SlashOption(description=t("PalconCog", "shutdown.reason_description")),
        server: str = nextcord.SlashOption(
            description=t("PalconCog", "command.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("PalconCog", "command.server_not_found").format(server=server), ephemeral=True)
            return
        response = await self.rcon_util.rcon_command(
            server_info, f"Shutdown {time} {reason}"
        )
        embed = nextcord.Embed(
            title=t("PalconCog", "shutdown.title").format(server=server), color=nextcord.Color.blue()
        )
        embed.description = t("PalconCog", "command.response").format(response=response)
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @shutdown.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description=t("PalconCog", "save.description"))
    async def save(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description=t("PalconCog", "command.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("PalconCog", "command.server_not_found").format(server=server), ephemeral=True)
            return
        response = await self.rcon_util.rcon_command(server_info, f"Save")
        embed = nextcord.Embed(title=t("PalconCog", "save.title").format(server=server), color=nextcord.Color.blue())
        embed.description = t("PalconCog", "command.response").format(response=response)
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @save.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description=t("PalconCog", "broadcast.description"))
    async def broadcast(
        self,
        interaction: nextcord.Interaction,
        message: str,
        server: str = nextcord.SlashOption(
            description=t("PalconCog", "command.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("PalconCog", "command.server_not_found").format(server=server), ephemeral=True)
            return
        response = await self.rcon_util.rcon_command(
            server_info, f"Broadcast {message}"
        )
        embed = nextcord.Embed(
            title=t("PalconCog", "broadcast.title").format(server=server), color=nextcord.Color.blue()
        )
        embed.description = t("PalconCog", "command.response").format(response=response)
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @broadcast.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

def setup(bot):
    cog = PalconCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.command,
            cog.showplayers,
            cog.kickplayer,
            cog.banplayer,
            cog.unbanplayer,
            cog.info,
            cog.shutdown,
            cog.save,
            cog.broadcast,
        ]
    )
