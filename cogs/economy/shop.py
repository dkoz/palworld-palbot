import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View
from utils.database import (
    get_points,
    set_points,
    get_steam_id,
    get_economy_setting,
    get_server_details,
    server_autocomplete,
)
from utils.rconutility import RconUtility
from utils.kitutility import load_shop_items
import asyncio
import utils.constants as constants
import json
from utils.translations import t

class ShopView(View):
    def __init__(self, shop_items, currency, cog, selected_server):
        super().__init__(timeout=None)
        self.shop_items = shop_items
        self.currency = currency
        self.current_page = 0
        self.cog = cog
        self.selected_server = selected_server
        self.add_shop_buttons()

    def add_shop_buttons(self):
        self.clear_items()

        item_names = list(self.shop_items.keys())
        start = self.current_page * 5
        end = min(start + 5, len(item_names))

        for item_name in item_names[start:end]:
            button = Button(label=f"Buy {item_name}", style=nextcord.ButtonStyle.green)
            button.callback = self.get_purchase_callback(item_name)
            self.add_item(button)

        if self.current_page > 0:
            previous_button = Button(label="Previous", style=nextcord.ButtonStyle.blurple)
            previous_button.callback = self.previous_button_callback
            self.add_item(previous_button)

        if (self.current_page + 1) * 5 < len(item_names):
            next_button = Button(label="Next", style=nextcord.ButtonStyle.blurple)
            next_button.callback = self.next_button_callback
            self.add_item(next_button)

    async def generate_shop_embed(self):
        embed = nextcord.Embed(
            title=t("ShopCog", "shop.menu.title"),
            description=t("ShopCog", "shop.menu.message"),
            color=nextcord.Color.blue(),
        )
        item_names = list(self.shop_items.keys())
        start = self.current_page * 5
        end = min(start + 5, len(item_names))

        for item_name in item_names[start:end]:
            item_info = self.shop_items[item_name]
            embed.add_field(
                name=item_name,
                value=f"{item_info['description']}\n**{t('ShopCog', 'shop.menu.price_label')}:** {item_info['price']} {self.currency}",
                inline=False,
            )

        embed.set_footer(
            text=f"{constants.FOOTER_TEXT}: Page {self.current_page + 1} of {((len(item_names) - 1) // 5) + 1}",
            icon_url=constants.FOOTER_IMAGE
        )
        return embed

    async def update_shop_message(self, interaction: nextcord.Interaction):
        self.add_shop_buttons()
        embed = await self.generate_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def get_purchase_callback(self, item_name: str):
        async def purchase_callback(interaction: nextcord.Interaction):
            await self.cog.purchase_item(interaction, item_name, self.selected_server)
        return purchase_callback

    async def previous_button_callback(self, interaction: nextcord.Interaction):
        self.current_page -= 1
        await self.update_shop_message(interaction)

    async def next_button_callback(self, interaction: nextcord.Interaction):
        self.current_page += 1
        await self.update_shop_message(interaction)

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_config())
        self.bot.loop.create_task(self.load_economy())
        self.bot.loop.create_task(self.reload_cache())
        self.rcon_util = RconUtility()
        self.servers = []

    async def reload_cache(self):
        while True:
            await self.load_shop_items()
            await asyncio.sleep(30)

    async def load_config(self):
        self.servers = await server_autocomplete()

    async def load_economy(self):
        self.currency = await get_economy_setting("currency_name") or "points"
        self.shop_items = await load_shop_items()

    async def load_shop_items(self):
        self.shop_items = await load_shop_items()

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

    @nextcord.slash_command(name="shop", description=t("ShopCog", "shop.description"))
    async def shop(self, interaction: nextcord.Interaction, server: str = nextcord.SlashOption(description=t("ShopCog", "shop.server_description"), autocomplete=True)):
        view = ShopView(self.shop_items, self.currency, self, server)
        embed = await view.generate_shop_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @shop.on_autocomplete("server")
    async def on_autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        choices = [server for server in self.servers if current.lower() in server.lower()][:25]
        await interaction.response.send_autocomplete(choices)

    async def purchase_item(self, interaction: nextcord.Interaction, item_name: str, server: str):
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        await interaction.response.defer(ephemeral=True)

        data = await get_points(user_id, user_name)
        if not data:
            await interaction.followup.send(t("ShopCog", "shop.redeem.error_retrieve_data"), ephemeral=True)
            return

        user_name, points = data
        steam_id = await get_steam_id(user_id)

        if steam_id is None:
            await interaction.followup.send(t("ShopCog", "shop.redeem.error_no_steamid"), ephemeral=True)
            return

        item = self.shop_items.get(item_name)
        if not item:
            await interaction.followup.send(t("ShopCog", "shop.redeem.error_item_not_found"), ephemeral=True)
            return

        if points < item["price"]:
            await interaction.followup.send(
                t("ShopCog", "shop.redeem.error_not_enough_points").format(currency=self.currency),
                ephemeral=True,
            )
            return

        new_points = points - item["price"]
        await set_points(user_id, user_name, new_points)

        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(f"Server {server} not found.", ephemeral=True)
            return

        for command_template in json.loads(item["commands"]):
            command = command_template.format(steamid=steam_id)
            try:
                await self.rcon_util.rcon_command(server_info, command)
                await asyncio.sleep(1)
            except Exception as e:
                await interaction.followup.send(f"Error executing command: {e}", ephemeral=True)
                return

        embed = nextcord.Embed(
            title=t("ShopCog", "shop.redeem.success_title").format(item_name=item_name),
            description=t("ShopCog", "shop.redeem.success_description").format(
                item_name=item_name, item_price=item['price'], server=server, currency=self.currency, remaining_points=new_points
            ),
            color=nextcord.Color.green(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(ShopCog(bot))
