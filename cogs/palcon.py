import json
import nextcord
from nextcord.ext import commands
from util.rconutility import RconUtility
import util.constants as constants
import datetime

class PalconCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.rcon_util = RconUtility(self.servers)

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            config = json.load(config_file)
            self.servers = config["PALWORLD_SERVERS"]

    async def autocomplete_server(
        self, interaction: nextcord.Interaction, current: str
    ):
        choices = [
            server for server in self.servers if current.lower() in server.lower()
        ]
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    async def palcon(self, interaction: nextcord.Interaction):
        pass

    @palcon.subcommand(description="Send a remote command to your Palworld server.")
    async def command(
        self,
        interaction: nextcord.Interaction,
        command: str,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(server, command)
        embed = nextcord.Embed(title=server, color=nextcord.Color.green())
        embed.description = f"**Response:** {response}"
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @command.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description="Show the current player list for a server.")
    async def showplayers(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(server, "ShowPlayers")
        embed = nextcord.Embed(
            title=f"Player List: {server}", color=nextcord.Color.red()
        )
        embed.description = f"{response}"
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @showplayers.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description="Kick a player from a server using their SteamID.")
    async def kickplayer(
        self,
        interaction: nextcord.Interaction,
        steamid: str,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(server, f"KickPlayer steam_{steamid}")
        embed = nextcord.Embed(
            title=f"KickPlayer Command - {server}", color=nextcord.Color.orange()
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
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description="Ban a player from a server using their SteamID.")
    async def banplayer(
        self,
        interaction: nextcord.Interaction,
        steamid: str,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(server, f"BanPlayer steam_{steamid}")
        embed = nextcord.Embed(
            title=f"BanPlayer Command - {server}", color=nextcord.Color.red()
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
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description="Unban a player from a server using their SteamID.")
    async def unbanplayer(
        self,
        interaction: nextcord.Interaction,
        steamid: str,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(server, f"UnBanPlayer steam_{steamid}")
        embed = nextcord.Embed(
            title=f"Unban Player Command - {server}", color=nextcord.Color.red()
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
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description="Show information about the server.")
    async def info(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(server, f"Info")
        embed = nextcord.Embed(title=f"Info - {server}", color=nextcord.Color.blue())
        embed.description = f"**Response:** {response}"
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @info.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description="Shutdown the server.")
    async def shutdown(
        self,
        interaction: nextcord.Interaction,
        time: str = nextcord.SlashOption(description="Time for the shutdown"),
        reason: str = nextcord.SlashOption(description="Reason for the shutdown"),
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(
            server, f"Shutdown {time} {reason}"
        )
        embed = nextcord.Embed(
            title=f"Shutdown - {server}", color=nextcord.Color.blue()
        )
        embed.description = f"**Response:** {response}"
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @shutdown.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description="Save the server.")
    async def save(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(server, f"Save")
        embed = nextcord.Embed(title=f"Save - {server}", color=nextcord.Color.blue())
        embed.description = f"**Response:** {response}"
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @save.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palcon.subcommand(description="Broadcast a message to the server.")
    async def broadcast(
        self,
        interaction: nextcord.Interaction,
        message: str,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(
            server, f"Broadcast {message}"
        )
        embed = nextcord.Embed(
            title=f"Broadcast - {server}", color=nextcord.Color.blue()
        )
        embed.description = f"**Response:** {response}"
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )
        await interaction.followup.send(embed=embed)

    @broadcast.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
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
            cog.info,
            cog.shutdown,
            cog.save,
            cog.broadcast,
        ]
    )