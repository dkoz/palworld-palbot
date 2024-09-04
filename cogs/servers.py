import nextcord
from nextcord.ext import commands
from utils.modals import AddServerModal
from utils.database import remove_server, server_autocomplete
from utils.translations import t
from utils.errorhandling import restrict_command

class ServerConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="addserver", description=t("ServerConfig", "addserver.description"), default_member_permissions=nextcord.Permissions(administrator=True))
    @restrict_command()
    async def addserver(self, interaction: nextcord.Interaction):
        modal = AddServerModal()
        await interaction.response.send_modal(modal)

    @nextcord.slash_command(name="removeserver", description=t("ServerConfig", "removeserver.description"), default_member_permissions=nextcord.Permissions(administrator=True))
    @restrict_command()
    async def removeserver(self, interaction: nextcord.Interaction, server_name: str):
        result = await remove_server(server_name)
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
        
def setup(bot):
    cog = ServerConfigCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend([cog.addserver, cog.removeserver])
