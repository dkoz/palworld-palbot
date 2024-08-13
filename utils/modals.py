import nextcord
from nextcord import ui, Interaction
from utils.database import add_server, update_economy_setting
from utils.translations import t

class AddServerModal(ui.Modal):
    def __init__(self):
        super().__init__(title=t("Modals", "addserver.title"))
        self.server_name = ui.TextInput(
            label=t("Modals", "addserver.server_name.label"),
            style=nextcord.TextInputStyle.short,
            placeholder=t("Modals", "addserver.server_name.placeholder")
        )
        self.server_host = ui.TextInput(
            label=t("Modals", "addserver.server_host.label"),
            style=nextcord.TextInputStyle.short,
            placeholder=t("Modals", "addserver.server_host.placeholder")
        )
        self.rcon_port = ui.TextInput(
            label=t("Modals", "addserver.rcon_port.label"),
            style=nextcord.TextInputStyle.short,
            placeholder=t("Modals", "addserver.rcon_port.placeholder")
        )
        self.connection_port = ui.TextInput(
            label=t("Modals", "addserver.connection_port.label"),
            style=nextcord.TextInputStyle.short,
            placeholder=t("Modals", "addserver.connection_port.placeholder")
        )
        self.admin_pass = ui.TextInput(
            label=t("Modals", "addserver.admin_pass.label"),
            style=nextcord.TextInputStyle.short,
            placeholder=t("Modals", "addserver.admin_pass.placeholder")
        )

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
        await interaction.response.send_message(
            t("Modals", "addserver.success").format(server_name=self.server_name.value),
            ephemeral=True
        )
       
class EconomySettingsModal(ui.Modal):
    def __init__(self):
        super().__init__(title=t("Modals", "economysettings.title"))
        
        self.currency_name = ui.TextInput(
            label=t("Modals", "economysettings.currency_name.label"),
            placeholder=t("Modals", "economysettings.currency_name.placeholder")
        )
        self.invite_reward = ui.TextInput(
            label=t("Modals", "economysettings.invite_reward.label"),
            placeholder=t("Modals", "economysettings.invite_reward.placeholder")
        )
        self.work_reward_min = ui.TextInput(
            label=t("Modals", "economysettings.work_reward_min.label"),
            placeholder=t("Modals", "economysettings.work_reward_min.placeholder")
        )
        self.work_reward_max = ui.TextInput(
            label=t("Modals", "economysettings.work_reward_max.label"),
            placeholder=t("Modals", "economysettings.work_reward_max.placeholder")
        )
        self.daily_reward = ui.TextInput(
            label=t("Modals", "economysettings.daily_reward.label"),
            placeholder=t("Modals", "economysettings.daily_reward.placeholder")
        )

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
            await interaction.response.send_message(
                t("Modals", "economysettings.success"),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                t("Modals", "economysettings.error").format(error=e),
                ephemeral=True
            )
    
class TimerSettingsModal(ui.Modal):
    def __init__(self):
        super().__init__(title=t("Modals", "timersettings.title"))
        self.work_timer = ui.TextInput(
            label=t("Modals", "timersettings.work_timer.label"),
            placeholder=t("Modals", "timersettings.work_timer.placeholder")
        )
        self.daily_timer = ui.TextInput(
            label=t("Modals", "timersettings.daily_timer.label"),
            placeholder=t("Modals", "timersettings.daily_timer.placeholder")
        )

        self.add_item(self.work_timer)
        self.add_item(self.daily_timer)

    async def callback(self, interaction: Interaction):
        try:
            await update_economy_setting("work_timer", self.work_timer.value)
            await update_economy_setting("daily_timer", self.daily_timer.value)
            await interaction.response.send_message(
                t("Modals", "timersettings.success"),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                t("Modals", "timersettings.error").format(error=e),
                ephemeral=True
            )

class EtcEconomySettingsModal(ui.Modal):
    def __init__(self):
        super().__init__(title=t("Modals", "etceconomysettings.title"))
        
        self.work_description = ui.TextInput(
            label=t("Modals", "etceconomysettings.work_description.label"),
            placeholder=t("Modals", "etceconomysettings.work_description.placeholder"),
            style=nextcord.TextInputStyle.paragraph
        )
        self.role_bonuses = ui.TextInput(
            label=t("Modals", "etceconomysettings.role_bonuses.label"),
            placeholder=t("Modals", "etceconomysettings.role_bonuses.placeholder"),
            style=nextcord.TextInputStyle.paragraph
        )
        self.vote_slug = ui.TextInput(
            label=t("Modals", "etceconomysettings.vote_slug.label"),
            placeholder=t("Modals", "etceconomysettings.vote_slug.placeholder"),
            required=False
        )
        self.vote_apikey = ui.TextInput(
            label=t("Modals", "etceconomysettings.vote_apikey.label"),
            placeholder=t("Modals", "etceconomysettings.vote_apikey.placeholder"),
            required=False
        )
        self.vote_reward = ui.TextInput(
            label=t("Modals", "etceconomysettings.vote_reward.label"),
            placeholder=t("Modals", "etceconomysettings.vote_reward.placeholder"),
            required=False
        )

        self.add_item(self.work_description)
        self.add_item(self.role_bonuses)
        self.add_item(self.vote_slug)
        self.add_item(self.vote_apikey)
        self.add_item(self.vote_reward)

    async def callback(self, interaction: Interaction):
        try:
            await update_economy_setting("work_description", self.work_description.value)
            await update_economy_setting("role_bonuses", self.role_bonuses.value)
            await update_economy_setting("vote_slug", self.vote_slug.value)
            await update_economy_setting("vote_apikey", self.vote_apikey.value)
            await update_economy_setting("vote_reward", self.vote_reward.value)
            await interaction.response.send_message(
                t("Modals", "etceconomysettings.success"),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                t("Modals", "etceconomysettings.error").format(error=e),
                ephemeral=True
            )
