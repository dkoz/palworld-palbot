import nextcord
from nextcord.ext import commands
from src.utils.rconutility import RconUtility
from src.utils.database import get_server_details, server_autocomplete
from src.utils.kitutility import (
    init_kitdb,
    get_kit,
    autocomplete_kits,
    save_kit,
    delete_kit,
    fetch_all_kits,
    KitModal
)
import json
import asyncio
import os
from src.utils.translations import t
from src.utils.errorhandling import restrict_command

class KitsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(init_kitdb())
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
        name="kit",
        description=t("KitsCog", "givekit.description"),
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    @restrict_command()
    async def givekit(self, interaction: nextcord.Interaction, steamid: str, kit_name: str, server: str):
        await interaction.response.defer(ephemeral=True)
        
        kit = await get_kit(kit_name)
        if not kit:
            await interaction.followup.send(t("KitsCog", "givekit.kit_not_found"), ephemeral=True)
            return
        commands, description, price, category = kit
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(t("KitsCog", "givekit.server_not_found").format(server=server), ephemeral=True)
            return

        for command_template in json.loads(commands):
            command = command_template.format(steamid=steamid)
            try:
                asyncio.create_task(self.rcon_util.rcon_command(server_info, command))
                await asyncio.sleep(1)
            except Exception as e:
                await interaction.followup.send(t("KitsCog", "givekit.error_executing_command").format(command=command, error=e), ephemeral=True)
                return

        embed = nextcord.Embed(
            title=t("KitsCog", "givekit.package_delivery_title").format(server=server),
            color=nextcord.Color.green(),
            description=t("KitsCog", "givekit.package_delivery_description").format(kit_name=kit_name, steamid=steamid)
        )
        await interaction.followup.send(embed=embed)

    @givekit.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return []
        
        await self.autocomplete_server(interaction, current)

    @givekit.on_autocomplete("kit_name")
    async def on_autocomplete_kits(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return []
        
        choices = await autocomplete_kits(current)
        await interaction.response.send_autocomplete(choices[:10])

    @nextcord.slash_command(
        name="managekits",
        description=t("KitsCog", "manage_kits.description"),
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    @restrict_command()
    async def manage_kits(self, interaction: nextcord.Interaction, kit_name: str = ""):
        try:
            kit = await get_kit(kit_name)
            if kit:
                commands = kit[0]
                description = kit[1]
                price = str(kit[2])
                category = kit[3]
            else:
                commands = "[]"
                description = ""
                price = "0"
                category = "main"
            modal = KitModal(t("Modals", "kitmodal.title"), kit_name, commands, description, price, category)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(t("KitsCog", "manage_kits.error_loading_kit").format(error=e), ephemeral=True)

    @manage_kits.on_autocomplete("kit_name")
    async def on_autocomplete_kits(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return[]

        choices = await autocomplete_kits(current)
        await interaction.response.send_autocomplete(choices[:10])

    @nextcord.slash_command(
        name="deletekit",
        description=t("KitsCog", "delete_kit.description"),
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    @restrict_command()
    async def delete_kit(self, interaction: nextcord.Interaction, kit_name: str):
        await interaction.response.defer(ephemeral=True)

        await delete_kit(kit_name)
        await self.bot.get_cog('ShopCog').load_shop_items()
        await interaction.followup.send(t("KitsCog", "delete_kit.success").format(kit_name=kit_name), ephemeral=True)

    @delete_kit.on_autocomplete("kit_name")
    async def on_autocomplete_kits(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return[]

        choices = await autocomplete_kits(current)
        await interaction.response.send_autocomplete(choices[:10])

    @nextcord.slash_command(
        name="uploadkits",
        description=t("KitsCog", "uploadkits.description"),
        default_member_permissions=nextcord.Permissions(administrator=True),
    )
    @restrict_command()
    async def uploadkits(self, interaction: nextcord.Interaction, json_file: nextcord.Attachment):
        await interaction.response.defer(ephemeral=True)

        if not json_file.filename.endswith('.json'):
            await interaction.followup.send(t("KitsCog", "uploadkits.invalid_file"), ephemeral=True)
            return

        try:
            file_content = await json_file.read()
            kits_data = json.loads(file_content)

            for kit_name, kit_data in kits_data.items():
                commands = json.dumps(kit_data['commands'])
                description = kit_data.get('description', '')
                price = kit_data.get('price', 0)
                category = kit_data.get('category', 'main')
                await save_kit(kit_name, commands, description, price, category)
            await self.bot.get_cog('ShopCog').load_shop_items()

            await interaction.followup.send(t("KitsCog", "uploadkits.success"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(t("KitsCog", "uploadkits.error").format(error=e), ephemeral=True)

    @nextcord.slash_command(
        name="exportkits",
        description="Export all kits as a JSON file.",
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    @restrict_command()
    async def exportkits(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)

        file_path = "kits.json"
        try:
            kits = await fetch_all_kits()
            if not kits:
                await interaction.followup.send("No kits found to export.", ephemeral=True)
                return

            kits_data = {}
            for kit in kits:
                kit_name = kit[0]
                commands = json.loads(kit[1])
                kits_data[kit_name] = {
                    'commands': commands,
                    'description': kit[2],
                    'price': kit[3],
                    'category': kit[4]
                }
            kits_json = json.dumps(kits_data, indent=4, ensure_ascii=False)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(kits_json)

            await interaction.followup.send(file=nextcord.File(file_path), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred while exporting kits: {str(e)}", ephemeral=True)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

def setup(bot):
    cog = KitsCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.givekit,
            cog.manage_kits,
            cog.delete_kit,
            cog.uploadkits,
            cog.exportkits
        ]
    )