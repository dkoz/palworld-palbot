import nextcord
from nextcord.ext import commands
from util.modals import AddServerModal
from util.database import remove_server, server_autocomplete

class ServerConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="addserver", description="Add a new server configuration.", default_member_permissions=nextcord.Permissions(administrator=True))
    async def addserver(self, interaction: nextcord.Interaction):
        modal = AddServerModal()
        await interaction.response.send_modal(modal)

    @nextcord.slash_command(name="removeserver", description="Remove an existing server configuration.", default_member_permissions=nextcord.Permissions(administrator=True))
    async def removeserver(self, interaction: nextcord.Interaction, server_name: str):
        result = await remove_server(server_name)
        if result:
            await interaction.response.send_message(f"Server '{server_name}' removed successfully.", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to remove server. It may not exist.", ephemeral=True)

    @removeserver.on_autocomplete("server_name")
    async def server_name_autocomplete(self, interaction: nextcord.Interaction, current: str):
        server_names = await server_autocomplete()
        choices = [name for name in server_names if current.lower() in name.lower()][:25]
        await interaction.response.send_autocomplete(choices)
        
def setup(bot):
    bot.add_cog(ServerConfigCog(bot))
