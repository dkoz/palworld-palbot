import json
import os
import nextcord
from nextcord.ext import commands
from util.rconutility import RconUtility
import asyncio

class KitsCog(commands.Cog):
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
        name="kit",
        description="Give a kit to a player.",
        default_member_permissions=nextcord.Permissions(administrator=True),
    )
    async def givekit(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description="SteamID/UID of the player."),
        kit_name: str = nextcord.SlashOption(
            description="The name of the kit.", autocomplete=True
        ),
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer()

        packages_path = os.path.join("gamedata", "kits.json")
        with open(packages_path) as packages_file:
            kits = json.load(packages_file)

        package = kits.get(kit_name)
        if not package:
            await interaction.followup.send("Kit not found.", ephemeral=True)
            return

        for command_template in package["commands"]:
            command = command_template.format(steamid=steamid)
            asyncio.create_task(self.rcon_util.rcon_command(server, command))
            await asyncio.sleep(1)

        embed = nextcord.Embed(
            title=f"Package Delivery - {server}", color=nextcord.Color.green()
        )
        embed.description = f"Delivering {kit_name} kit to {steamid}."
        await interaction.followup.send(embed=embed)

    @givekit.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @givekit.on_autocomplete("kit_name")
    async def on_autocomplete_packages(
        self, interaction: nextcord.Interaction, current: str
    ):
        packages_path = os.path.join("gamedata", "kits.json")
        with open(packages_path) as packages_file:
            kits = json.load(packages_file)
        choices = [name for name in kits if current.lower() in name.lower()][:25]
        await interaction.response.send_autocomplete(choices)

def setup(bot):
    bot.add_cog(KitsCog(bot))