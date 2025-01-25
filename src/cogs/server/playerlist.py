import nextcord
from nextcord.ext import commands
from nextcord.ui import View
from src.utils.rconutility import RconUtility
import src.utils.constants as constants
import datetime
from src.utils.database import get_server_details, server_autocomplete
from src.utils.translations import t
from src.utils.errorhandling import restrict_command

class PlayerListView(View):
    def __init__(self, server, player_data):
        super().__init__()
        self.server = server
        self.player_data = player_data
        self.current_page = 0

    async def generate_player_embed(self):
        embed = nextcord.Embed(
            title=t("PlayerListCog", "playerslist.title").format(server=self.server),
            description=t("PlayerListCog", "playerslist.description"),
            color=nextcord.Color.green(),
        )
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%Y-%m-%d at %I:%M %p')}",
            icon_url=constants.FOOTER_IMAGE,
        )

        names = ""
        uids = ""
        steamids = ""

        start = self.current_page * 10
        end = min(start + 10, len(self.player_data))

        for player in self.player_data[start:end]:
            parts = player.strip().split(',')
            if len(parts) == 3 and all(parts):
                name, playeruid, steamid = parts
                names += f"{name}\n"
                uids += f"{playeruid}\n"
                steamids += f"{steamid}\n"

        embed.add_field(name=t("PlayerListCog", "playerslist.names"), value=names or t("PlayerListCog", "playerslist.no_data"), inline=True)
        embed.add_field(name=t("PlayerListCog", "playerslist.uids"), value=uids or t("PlayerListCog", "playerslist.no_data"), inline=True)
        embed.add_field(name=t("PlayerListCog", "playerslist.steamids"), value=steamids or t("PlayerListCog", "playerslist.no_data"), inline=True)

        return embed

    @nextcord.ui.button(label=t("PlayerListCog", "button.previous"), style=nextcord.ButtonStyle.blurple)
    async def previous_button_callback(self, button, interaction):
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.generate_player_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @nextcord.ui.button(label=t("PlayerListCog", "button.next"), style=nextcord.ButtonStyle.blurple)
    async def next_button_callback(self, button, interaction):
        if (self.current_page + 1) * 10 < len(self.player_data):
            self.current_page += 1
            embed = await self.generate_player_embed()
            await interaction.response.edit_message(embed=embed, view=self)

class PlayerListCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_servers())
        self.rcon_util = RconUtility()
        self.servers = []

    async def load_servers(self):
        self.servers = await server_autocomplete()

    async def autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return []
        server_names = await server_autocomplete()
        choices = [server for server in server_names if current.lower() in server.lower()][:25]
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
        name="players",
        description=t("PlayerListCog", "playerslist.command_description"),
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    @restrict_command()
    async def playerslist(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description=t("PlayerListCog", "playerslist.server_description"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            embed = nextcord.Embed(
                title=t("PlayerListCog", "error.title"),
                description=t("PlayerListCog", "error.server_not_found").format(server=server),
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        response = await self.rcon_util.rcon_command(server_info, "ShowPlayers")

        if response:
            player_data = response.split('\n')[1:]
            if player_data:
                view = PlayerListView(server, player_data)
                embed = await view.generate_player_embed()
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                embed = nextcord.Embed(
                    title=t("PlayerListCog", "playerslist.empty_title"),
                    description=t("PlayerListCog", "playerslist.no_players_online"),
                    color=nextcord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = nextcord.Embed(
                title=t("PlayerListCog", "error.title"),
                description=t("PlayerListCog", "error.failed_to_retrieve"),
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    @playerslist.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

def setup(bot):
    cog = PlayerListCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.playerslist
        ]
    )
