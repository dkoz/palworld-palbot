import json
import os
import nextcord
from nextcord.ext import commands

class GamedataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_pals()
        self.load_items()

    def load_pals(self):
        pals_path = os.path.join("gamedata", "pals.json")
        with open(pals_path, "r", encoding="utf-8") as pals_file:
            self.pals = json.load(pals_file)["creatures"]

    def load_items(self):
        items_path = os.path.join("gamedata", "items.json")
        with open(items_path, "r", encoding="utf-8") as items_file:
            self.items = json.load(items_file)["items"]

    async def autocomplete_pal(self, interaction: nextcord.Interaction, current: str):
        choices = [
            pal["name"] for pal in self.pals if current.lower() in pal["name"].lower()
        ][:25]
        await interaction.response.send_autocomplete(choices)

    async def autocomplete_item(self, interaction: nextcord.Interaction, current: str):
        choices = [
            item["name"] for item in self.items if current.lower() in item["name"].lower()
        ][:25]
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    async def search(self, _interaction: nextcord.Interaction):
        pass

    @search.subcommand(description="Search for a pal by name.")
    async def pal(
        self,
        interaction: nextcord.Interaction,
        name: str = nextcord.SlashOption(
            description="Name of the pal to search for", autocomplete=True),
    ):
        await interaction.response.defer(ephemeral=True)
        pal = next((pal for pal in self.pals if pal["name"] == name), None)
        if pal:
            embed = nextcord.Embed(
                title=pal['name'], color=nextcord.Color.blue())
            embed.description = f"Spawn Code: `{pal['id']}`"
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Pal not found.", ephemeral=True)

    @pal.on_autocomplete("name")
    async def autocomplete_pal_name(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_pal(interaction, current)

    @search.subcommand(description="Search for an item by name.")
    async def item(
        self,
        interaction: nextcord.Interaction,
        name: str = nextcord.SlashOption(
            description="Name of the item to search for", autocomplete=True),
    ):
        await interaction.response.defer(ephemeral=True)
        item = next(
            (item for item in self.items if item["name"] == name), None)
        if item:
            embed = nextcord.Embed(
                title=item['name'], color=nextcord.Color.green())
            embed.description = f"Spawn Code: `{item['id']}`"
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Item not found.", ephemeral=True)

    @item.on_autocomplete("name")
    async def autocomplete_item_name(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_item(interaction, current)

def setup(bot):
    cog = GamedataCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.search,
            cog.pal,
            cog.item,
        ]
    )
