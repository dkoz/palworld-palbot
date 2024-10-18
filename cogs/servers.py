import nextcord
from nextcord.ext import commands
from utils.modals import AddServerModal
from utils.database import (
    remove_server,
    server_autocomplete,
    edit_server_details,
    update_server_details
)
from utils.translations import t
from utils.errorhandling import restrict_command

class ServerConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_servers())

    async def load_servers(self):
        self.servers = await server_autocomplete()
        self.bot.servers = self.servers

    async def refresh_servers(self):
        self.bot.servers = await server_autocomplete()
        for cog in self.bot.cogs.values():
            if hasattr(cog, 'servers'):
                cog.servers = self.bot.servers

    @nextcord.slash_command(name="addserver", description=t("ServerConfig", "addserver.description"), default_member_permissions=nextcord.Permissions(administrator=True), dm_permission=False)
    @restrict_command()
    async def addserver(self, interaction: nextcord.Interaction):
        modal = AddServerModal()
        await interaction.response.send_modal(modal)

    @nextcord.slash_command(name="removeserver", description=t("ServerConfig", "removeserver.description"), default_member_permissions=nextcord.Permissions(administrator=True), dm_permission=False)
    @restrict_command()
    async def removeserver(self, interaction: nextcord.Interaction, server_name: str):
        result = await remove_server(server_name)
        await self.refresh_servers()
        if result:
            await interaction.response.send_message(t("ServerConfig", "removeserver.success").format(server_name=server_name), ephemeral=True)
        else:
            await interaction.response.send_message(t("ServerConfig", "removeserver.failed"), ephemeral=True)

    @removeserver.on_autocomplete("server_name")
    async def server_name_autocomplete(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return[]
        
        server_names = await server_autocomplete()
        choices = [name for name in server_names if current.lower() in name.lower()][:25]
        await interaction.response.send_autocomplete(choices)
        
    @nextcord.slash_command(name="editserver", description=t("ServerConfig", "editserver.description"), default_member_permissions=nextcord.Permissions(administrator=True), dm_permission=False)
    @restrict_command()
    async def editserver(self, interaction: nextcord.Interaction, server_name: str):
        try:
            server_details = await edit_server_details(server_name)
            if not server_details:
                await interaction.response.send_message(t("ServerConfig", "editserver.notfound").format(server_name=server_name), ephemeral=True)
                return

            server_host, rcon_port, connection_port, admin_pass = server_details

            modal = AddServerModal()
            modal.children[0].default_value = server_name
            modal.children[1].default_value = server_host
            modal.children[2].default_value = str(rcon_port)
            modal.children[3].default_value = str(connection_port)
            modal.children[4].default_value = admin_pass

            async def modal_callback(interaction):
                await update_server_details(
                    old_server_name=server_name, 
                    new_server_name=modal.children[0].value, 
                    server_host=modal.children[1].value, 
                    rcon_port=int(modal.children[2].value), 
                    connection_port=int(modal.children[3].value), 
                    admin_pass=modal.children[4].value
                )

                await self.refresh_servers()

                await interaction.response.send_message(t("ServerConfig", "editserver.success").format(server_name=server_name), ephemeral=True)

            modal.callback = modal_callback
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.followup.send(f"Unexpected error: {e}", ephemeral=True)
        
    @editserver.on_autocomplete("server_name")
    async def server_name_autocomplete(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return[]
        
        server_names = await server_autocomplete()
        choices = [name for name in server_names if current.lower() in name.lower()][:25]
        await interaction.response.send_autocomplete(choices)
        
def setup(bot):
    cog = ServerConfigCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend([cog.addserver, cog.removeserver, cog.editserver])
