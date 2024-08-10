import nextcord
from nextcord.ext import commands
from nextcord.ui import View
from utils.rconutility import RconUtility
import utils.constants as constants
import datetime
from utils.database import get_server_details, server_autocomplete

class PlayerListView(View):
    def __init__(self, server, player_data):
        super().__init__()
        self.server = server
        self.player_data = player_data
        self.current_page = 0

    async def generate_player_embed(self):
        embed = nextcord.Embed(
            title=f"Player List: {self.server}",
            description="Here are the players currently online:",
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

        embed.add_field(name="Names", value=names or "No data", inline=True)
        embed.add_field(name="Player UIDs", value=uids or "No data", inline=True)
        embed.add_field(name="SteamIDs", value=steamids or "No data", inline=True)

        return embed

    @nextcord.ui.button(label="Previous", style=nextcord.ButtonStyle.blurple)
    async def previous_button_callback(self, button, interaction):
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.generate_player_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.blurple)
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

    async def autocomplete_server(
        self, interaction: nextcord.Interaction, current: str
    ):
        choices = [
            server for server in self.servers if current.lower() in server.lower()
        ]
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

    @nextcord.slash_command(name="players",description="Display the player list in an interactive embed.", default_member_permissions=nextcord.Permissions(administrator=True))
    async def playerslist(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            embed = nextcord.Embed(
                title="Error",
                description=f"Server {server} not found.",
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
                    title="Player List: Empty",
                    description="No players are currently online.",
                    color=nextcord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = nextcord.Embed(
                title="Error",
                description="Failed to retrieve player data.",
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
    bot.all_slash_commands.append(cog.playerslist)