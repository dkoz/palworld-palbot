import nextcord
from nextcord.ext import commands
from utils.rconutility import RconUtility
from utils.database import get_server_details, server_autocomplete
from utils.kitutility import (
    init_kitdb,
    get_kit,
    autocomplete_kits,
    save_kit,
    delete_kit,
    KitModal
)
import json
import asyncio

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

    @nextcord.slash_command(name="kit", description="Give a kit to a player.", default_member_permissions=nextcord.Permissions(administrator=True))
    async def givekit(self, interaction: nextcord.Interaction, steamid: str, kit_name: str, server: str):
        await interaction.response.defer(ephemeral=True)
        
        kit = await get_kit(kit_name)
        if not kit:
            await interaction.followup.send("Kit not found.", ephemeral=True)
            return
        
        commands, description, price = kit

        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(f"Server {server} not found.", ephemeral=True)
            return

        for command_template in json.loads(commands):
            command = command_template.format(steamid=steamid)
            try:
                asyncio.create_task(self.rcon_util.rcon_command(server_info, command))
                await asyncio.sleep(1)
            except Exception as e:
                await interaction.followup.send(f"Error executing command '{command}': {e}", ephemeral=True)
                return

        embed = nextcord.Embed(
            title=f"Package Delivery - {server}",
            color=nextcord.Color.green(),
            description=f"Delivering {kit_name} kit to {steamid}."
        )
        await interaction.followup.send(embed=embed)

    @givekit.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @givekit.on_autocomplete("kit_name")
    async def on_autocomplete_kits(self, interaction: nextcord.Interaction, current: str):
        choices = await autocomplete_kits(current)
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(name="managekits", description="Add or update a kit.", default_member_permissions=nextcord.Permissions(administrator=True))
    async def manage_kits(self, interaction: nextcord.Interaction, kit_name: str = ""):
        try:
            kit = await get_kit(kit_name)
            
            commands = kit[0] if kit else "[]"
            description = kit[1] if kit else ""
            price = str(kit[2]) if kit else "0"
            
            modal = KitModal("Manage Kit", kit_name, commands, description, price)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(f"Error loading kit details: {e}", ephemeral=True)
            
    @manage_kits.on_autocomplete("kit_name")
    async def on_autocomplete_kits(self, interaction: nextcord.Interaction, current: str):
        choices = await autocomplete_kits(current)
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(name="deletekit", description="Delete a kit.", default_member_permissions=nextcord.Permissions(administrator=True))
    async def delete_kit(self, interaction: nextcord.Interaction, kit_name: str):
        await interaction.response.defer(ephemeral=True)
        
        await delete_kit(kit_name)
        await interaction.followup.send(f"Kit '{kit_name}' has been deleted.", ephemeral=True)

    @delete_kit.on_autocomplete("kit_name")
    async def on_autocomplete_kits(self, interaction: nextcord.Interaction, current: str):
        choices = await autocomplete_kits(current)
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(name="uploadkits", description="Upload kits from a JSON file to the database.", default_member_permissions=nextcord.Permissions(administrator=True))
    async def uploadkits(self, interaction: nextcord.Interaction, json_file: nextcord.Attachment):
        await interaction.response.defer(ephemeral=True)

        if not json_file.filename.endswith('.json'):
            await interaction.followup.send("Please upload a valid JSON file.", ephemeral=True)
            return

        try:
            file_content = await json_file.read()
            kits_data = json.loads(file_content)

            for kit_name, kit_data in kits_data.items():
                commands = json.dumps(kit_data['commands'])
                description = kit_data.get('description', '')
                price = kit_data.get('price', 0)

                await save_kit(kit_name, commands, description, price)

            await interaction.followup.send("Kits uploaded successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred while uploading kits: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(KitsCog(bot))