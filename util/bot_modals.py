import nextcord
from nextcord import ui, Interaction
from util.economy_system import add_server

class AddServerModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Add New Server")
        self.server_name = ui.TextInput(label="Server Name", style=nextcord.TextInputStyle.short, placeholder="Enter a unique name for the server")
        self.server_host = ui.TextInput(label="Server Host", style=nextcord.TextInputStyle.short, placeholder="Enter server host IP or address")
        self.rcon_port = ui.TextInput(label="RCON Port", style=nextcord.TextInputStyle.short, placeholder="Enter RCON port")
        self.connection_port = ui.TextInput(label="Connection Port", style=nextcord.TextInputStyle.short, placeholder="Enter connection port")
        self.admin_pass = ui.TextInput(label="Admin Password", style=nextcord.TextInputStyle.short, placeholder="Enter admin password")

        self.add_item(self.server_name)
        self.add_item(self.server_host)
        self.add_item(self.rcon_port)
        self.add_item(self.connection_port)
        self.add_item(self.admin_pass)

    async def callback(self, interaction: Interaction):
        guild_id = str(interaction.guild_id)
        await add_server(
            guild_id=guild_id,
            server_name=self.server_name.value,
            server_host=self.server_host.value,
            rcon_port=int(self.rcon_port.value),
            connection_port=int(self.connection_port.value),
            admin_pass=self.admin_pass.value
        )
        await interaction.response.send_message(f"Server '{self.server_name.value}' added successfully.", ephemeral=True)
