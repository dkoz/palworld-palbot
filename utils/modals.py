import nextcord
from nextcord import ui, Interaction
from utils.database import add_server, update_economy_setting

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
       
class EconomySettingsModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Economy Settings")
        
        self.currency_name = ui.TextInput(label="Currency Name", placeholder="Points")
        self.invite_reward = ui.TextInput(label="Invite Reward", placeholder="10")
        self.work_reward_min = ui.TextInput(label="Minimum Work Reward", placeholder="20")
        self.work_reward_max = ui.TextInput(label="Maximum Work Reward", placeholder="50")
        self.daily_reward = ui.TextInput(label="Daily Reward", placeholder="200")

        self.add_item(self.currency_name)
        self.add_item(self.invite_reward)
        self.add_item(self.work_reward_min)
        self.add_item(self.work_reward_max)
        self.add_item(self.daily_reward)

    async def callback(self, interaction: Interaction):
        try:
            await update_economy_setting("currency_name", self.currency_name.value)
            await update_economy_setting("invite_reward", self.invite_reward.value)
            await update_economy_setting("work_reward_min", self.work_reward_min.value)
            await update_economy_setting("work_reward_max", self.work_reward_max.value)
            await update_economy_setting("daily_reward", self.daily_reward.value)
            await interaction.response.send_message("Economy settings updated successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)
    
class TimerSettingsModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Timer Settings")
        self.work_timer = ui.TextInput(label="Work Timer (seconds)", placeholder="360")
        self.daily_timer = ui.TextInput(label="Daily Timer (seconds)", placeholder="86400")

        self.add_item(self.work_timer)
        self.add_item(self.daily_timer)

    async def callback(self, interaction: Interaction):
        try:
            await update_economy_setting("work_timer", self.work_timer.value)
            await update_economy_setting("daily_timer", self.daily_timer.value)
            await interaction.response.send_message("Timer settings updated successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)