import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View
from src.utils.database import (
    get_points,
    set_points,
    get_steam_id,
    get_economy_setting,
    get_server_details,
    server_autocomplete,
)
from src.utils.rconutility import RconUtility
from src.utils.kitutility import load_shop_items
import asyncio
import src.utils.constants as constants
import json
from src.utils.translations import t
from src.utils.errorhandling import restrict_command
import logging

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
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except nextcord.errors.NotFound:
            pass

    def get_purchase_callback(self, item_name: str):
        async def purchase_callback(interaction: nextcord.Interaction):
            try:
                await self.cog.purchase_item(interaction, item_name, self.selected_server)
            except nextcord.errors.NotFound:
                pass
        return purchase_callback

    async def previous_button_callback(self, interaction: nextcord.Interaction):
        self.current_page -= 1
        try:
            await self.update_shop_message(interaction)
        except nextcord.errors.NotFound:
            pass

    async def next_button_callback(self, interaction: nextcord.Interaction):
        self.current_page += 1
        try:
            await self.update_shop_message(interaction)
        except nextcord.errors.NotFound:
            pass

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
    
    async def autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return []
        server_names = await server_autocomplete()
        choices = [server for server in server_names if current.lower() in server.lower()][:25]
        await interaction.response.send_autocomplete(choices)
    
    @nextcord.slash_command(description=t("ShopCog", "shop.description"))
    async def shop(self, _interaction: nextcord.Interaction):
        pass

    @shop.subcommand(name="menu", description=t("ShopCog", "shop.menu.description"))
    @restrict_command()
    async def menu(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(description=t("ShopCog", "shop.redeem.server_description"), autocomplete=True),
        category: str = nextcord.SlashOption(description=t("ShopCog", "shop.redeem.item_category"), required=False, default="main", autocomplete=True)
    ):
        filtered_items = {k: v for k, v in self.shop_items.items() if v["category"].lower() == category.lower()}

        if not filtered_items and category.lower() != "main":
            await interaction.response.send_message(f"No kits found for category '{category}'.", ephemeral=True)
            return

        view = ShopView(filtered_items, self.currency, self, server)
        embed = await view.generate_shop_embed()
        try:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except nextcord.errors.NotFound:
            pass

    @menu.on_autocomplete("server")
    async def on_autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @menu.on_autocomplete("category")
    async def on_autocomplete_category(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return []
        
        categories = list({v["category"] for v in self.shop_items.values()})
        filtered = [cat for cat in categories if current.lower() in cat.lower()][:25]
        await interaction.response.send_autocomplete(filtered)

    async def purchase_item(self, interaction: nextcord.Interaction, item_name: str, server: str):
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        try:
            await interaction.response.defer(ephemeral=True)
        except nextcord.errors.NotFound:
            return

        data = await get_points(user_id, user_name)
        if not data:
            try:
                await interaction.followup.send(t("ShopCog", "shop.redeem.error_retrieve_data"), ephemeral=True)
            except nextcord.errors.NotFound:
                pass
            return

        user_name, points = data
        steam_id = await get_steam_id(user_id)

        if steam_id is None:
            try:
                await interaction.followup.send(t("ShopCog", "shop.redeem.error_no_steamid"), ephemeral=True)
            except nextcord.errors.NotFound:
                pass
            return

        item = self.shop_items.get(item_name)
        if not item:
            try:
                await interaction.followup.send(t("ShopCog", "shop.redeem.error_item_not_found"), ephemeral=True)
            except nextcord.errors.NotFound:
                pass
            return

        if points < item["price"]:
            try:
                await interaction.followup.send(
                    t("ShopCog", "shop.redeem.error_not_enough_points").format(currency=self.currency),
                    ephemeral=True,
                )
            except nextcord.errors.NotFound:
                pass
            return

        new_points = points - item["price"]
        await set_points(user_id, user_name, new_points)

        server_info = await self.get_server_info(server)
        if not server_info:
            try:
                await interaction.followup.send(f"Server {server} not found.", ephemeral=True)
            except nextcord.errors.NotFound:
                pass
            return

        for command_template in json.loads(item["commands"]):
            command = command_template.format(steamid=steam_id)
            try:
                response = await self.rcon_util.rcon_command(server_info, command)

                if "Failed to parse UID" in response or "Failed to find player by UserId" in response:
                    await set_points(user_id, user_name, points)
                    try:
                        await interaction.followup.send(
                            t("ShopCog", "shop.redeem.error_user_not_found").format(user_name=user_name),
                            ephemeral=True
                        )
                    except nextcord.errors.NotFound:
                        pass
                    logging.error(f"Failed to find player {user_name} (ID: {user_id}) while purchasing {item_name}. Points refunded.")
                    return

                await asyncio.sleep(1)

            except Exception as e:
                try:
                    await interaction.followup.send(f"Error executing command '{command}': {e}", ephemeral=True)
                except nextcord.errors.NotFound:
                    pass
                return

        embed = nextcord.Embed(
            title=t("ShopCog", "shop.redeem.success_title").format(item_name=item_name),
            description=t("ShopCog", "shop.redeem.success_description").format(
                item_name=item_name, item_price=item['price'], currency=self.currency, server=server, remaining_points=new_points
            ),
            color=nextcord.Color.green(),
        )
        
        logging.info(f"User {user_name} (ID: {user_id}) purchased {item_name} for {item['price']} {self.currency} on server {server}. Remaining points: {new_points}")
        
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except nextcord.errors.NotFound:
            pass
        
    @shop.subcommand(name="redeem", description=t("ShopCog", "shop.redeem.description"))
    @restrict_command()
    async def redeem(
        self,
        interaction: nextcord.Interaction,
        item_name: str = nextcord.SlashOption(
            description=t("ShopCog", "shop.redeem.item_description"), autocomplete=True
        ),
        server: str = nextcord.SlashOption(
            description=t("ShopCog", "shop.redeem.server_description"), autocomplete=True
        ),
    ):
        try:
            await interaction.response.defer(ephemeral=True)
        except nextcord.errors.NotFound:
            return

        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        data = await get_points(user_id, user_name)
        if not data:
            try:
                await interaction.followup.send(
                    t("ShopCog", "shop.redeem.error_retrieve_data"), ephemeral=True
                )
            except nextcord.errors.NotFound:
                pass
            return

        user_name, points = data
        steam_id = await get_steam_id(user_id)

        if steam_id is None:
            try:
                await interaction.followup.send(t("ShopCog", "shop.redeem.error_no_steamid"), ephemeral=True)
            except nextcord.errors.NotFound:
                pass
            return

        item = self.shop_items.get(item_name)
        if not item:
            try:
                await interaction.followup.send(t("ShopCog", "shop.redeem.error_item_not_found"), ephemeral=True)
            except nextcord.errors.NotFound:
                pass
            return

        if points < item["price"]:
            try:
                await interaction.followup.send(
                    t("ShopCog", "shop.redeem.error_not_enough_points").format(currency=self.currency),
                    ephemeral=True,
                )
            except nextcord.errors.NotFound:
                pass
            return

        new_points = points - item["price"]
        await set_points(user_id, user_name, new_points)

        server_info = await self.get_server_info(server)
        if not server_info:
            try:
                await interaction.followup.send(f"Server {server} not found.", ephemeral=True)
            except nextcord.errors.NotFound:
                pass
            return

        for command_template in json.loads(item["commands"]):
            command = command_template.format(steamid=steam_id)
            try:
                response = await self.rcon_util.rcon_command(server_info, command)

                if "Failed to parse UID" in response or "Failed to find player by UserId" in response:
                    await set_points(user_id, user_name, points)
                    try:
                        await interaction.followup.send(
                            t("ShopCog", "shop.redeem.error_user_not_found").format(user_name=user_name),
                            ephemeral=True
                        )
                    except nextcord.errors.NotFound:
                        pass
                    logging.error(f"Failed to find player {user_name} (ID: {user_id}) while redeeming {item_name}. Points refunded.")
                    return

                await asyncio.sleep(1)

            except Exception as e:
                try:
                    await interaction.followup.send(f"Error executing command '{command}': {e}", ephemeral=True)
                except nextcord.errors.NotFound:
                    pass
                return

        embed = nextcord.Embed(
            title=t("ShopCog", "shop.redeem.success_title").format(item_name=item_name),
            description=t("ShopCog", "shop.redeem.success_description").format(
                item_name=item_name, item_price=item['price'], currency=self.currency, server=server, remaining_points=new_points
            ),
            color=nextcord.Color.green(),
        )
        
        logging.info(f"User {user_name} (ID: {user_id}) redeemed {item_name} for {item['price']} {self.currency} on server {server}. Remaining points: {new_points}")
        
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except nextcord.errors.NotFound:
            pass

    @redeem.on_autocomplete("server")
    async def on_autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @redeem.on_autocomplete("item_name")
    async def on_autocomplete_shop_items(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return[]
        
        choices = [name for name in self.shop_items if current.lower() in name.lower()][:10]
        await interaction.response.send_autocomplete(choices)


def setup(bot):
    bot.add_cog(ShopCog(bot))
