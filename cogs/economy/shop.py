import json
import os
import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View
from util.economy_system import get_points, set_points, get_steam_id
from util.rconutility import RconUtility
import asyncio
import util.constants as constants

class ShopView(View):
    def __init__(self, shop_items, currency):
        super().__init__()
        self.shop_items = shop_items
        self.currency = currency
        self.current_page = 0

    async def generate_shop_embed(self):
        embed = nextcord.Embed(
            title="Shop Items",
            description="Welcome to the shop! Please ensure you're connected to the palworld server before making a purchase.",
            color=nextcord.Color.blue(),
        )
        item_names = list(self.shop_items.keys())
        start = self.current_page * 5
        end = min(start + 5, len(item_names))

        for item_name in item_names[start:end]:
            item_info = self.shop_items[item_name]
            embed.add_field(
                name=item_name,
                value=f"{item_info['description']}\n"
                      f"**Price:** {item_info['price']} {self.currency}",
                inline=False,
            )
        embed.set_footer(
            text=f"{constants.FOOTER_TEXT}: Page {self.current_page + 1}",
            icon_url=constants.FOOTER_IMAGE,
        )
        return embed

    @nextcord.ui.button(label="Previous", style=nextcord.ButtonStyle.blurple)
    async def previous_button_callback(self, button, interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_shop_message(interaction)

    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.blurple)
    async def next_button_callback(self, button, interaction):
        if (self.current_page + 1) * 5 < len(self.shop_items):
            self.current_page += 1
            await self.update_shop_message(interaction)

    async def update_shop_message(self, interaction):
        embed = await self.generate_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_shop_items()
        self.load_config()
        self.load_economy()
        self.rcon_util = RconUtility(self.servers)

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            config = json.load(config_file)
            self.servers = config["PALWORLD_SERVERS"]

    def load_economy(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            self.economy_config = json.load(config_file)
        self.economy_config = self.economy_config.get("ECONOMY_SETTINGS", {})
        self.currency = self.economy_config.get("currency", "points")

    def load_shop_items(self):
        config_path = "gamedata"
        shop_items_path = os.path.join(config_path, "kits.json")
        with open(shop_items_path) as shop_items_file:
            all_items = json.load(shop_items_file)
            # Filtering out items with a price of 0
            self.shop_items = {
                key: value for key, value in all_items.items() if value["price"] > 0
            }

    @nextcord.slash_command(name="shop", description="Shop commands.")
    async def shop(self, _interaction: nextcord.Interaction):
        pass

    @shop.subcommand(name="menu", description="Displays available items in the shop.")
    async def menu(self, interaction: nextcord.Interaction):
        view = ShopView(self.shop_items, self.currency)
        embed = await view.generate_shop_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @shop.subcommand(name="redeem", description="Redeem your points for a shop item.")
    async def redeem(
        self,
        interaction: nextcord.Interaction,
        item_name: str = nextcord.SlashOption(
            description="The name of the item to redeem.", autocomplete=True
        ),
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        data = get_points(user_id, user_name)
        if not data:
            await interaction.followup.send(
                "There was an error retrieving your data.", ephemeral=True
            )
            return

        user_name, points = data
        steam_id = get_steam_id(user_id)

        if steam_id is None:
            await interaction.followup.send("No Steam ID linked.", ephemeral=True)
            return

        item = self.shop_items.get(item_name)
        if not item:
            await interaction.followup.send("Item not found.", ephemeral=True)
            return

        # Added price check so that items with a price of 0 cannot be redeemed
        if item["price"] <= 0:
            await interaction.followup.send(
                "This item cannot be redeemed.", ephemeral=True
            )
            return

        if points < item["price"]:
            await interaction.followup.send(
                f"You do not have enough {self.currency} to redeem this item.",
                ephemeral=True,
            )
            return

        new_points = points - item["price"]
        set_points(user_id, user_name, new_points)

        for command_template in item["commands"]:
            command = command_template.format(steamid=steam_id)
            asyncio.create_task(self.rcon_util.rcon_command(server, command))
            await asyncio.sleep(1)

        embed = nextcord.Embed(
            title=f"Redeemed {item_name}",
            description=f"Successfully redeemed {item_name} for {item['price']} {self.currency} on server {server}. You now have {new_points} {self.currency} left.",
            color=nextcord.Color.green(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @redeem.on_autocomplete("server")
    async def on_autocomplete_server(
        self, interaction: nextcord.Interaction, current: str
    ):
        choices = [
            server for server in self.servers if current.lower() in server.lower()
        ][:25]
        await interaction.response.send_autocomplete(choices)

    @redeem.on_autocomplete("item_name")
    async def on_autocomplete_shop_items(
        self, interaction: nextcord.Interaction, current: str
    ):
        choices = [name for name in self.shop_items if current.lower() in name.lower()][
            :25
        ]
        await interaction.response.send_autocomplete(choices)

def setup(bot):
    config_path = "config.json"
    with open(config_path) as config_file:
        config = json.load(config_file)

    economy_settings = config.get("ECONOMY_SETTINGS", {})
    if not economy_settings.get("enabled", False):
        return

    bot.add_cog(ShopCog(bot))
