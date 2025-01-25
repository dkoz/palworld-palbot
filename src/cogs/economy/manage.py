import nextcord
from nextcord.ext import commands
from src.utils.database import (
    add_points,
    get_points,
    set_points,
    link_steam_account,
    update_discord_username,
    get_economy_setting,
)
from src.utils.modals import (
    EconomySettingsModal,
    TimerSettingsModal,
    EtcEconomySettingsModal,
    VoteSettingsModal,
    fetch_economy_settings
)
from src.utils.translations import t
from src.utils.errorhandling import restrict_command

class EconomyManageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_config())

    async def load_config(self):
        self.currency = await get_economy_setting("currency_name") or "points"

    @nextcord.slash_command(
        name="economyset",
        description=t("EconomyManageCog", "economyset.description"),
        default_member_permissions=nextcord.Permissions(administrator=True) 
    )
    async def economyset(self, _interaction: nextcord.Interaction):
        pass

    @economyset.subcommand(name="addpoints", description=t("EconomyManageCog", "economyset.addpoints.description"))
    @restrict_command()
    async def addpoints(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="Select the user"),
        points: int = nextcord.SlashOption(description="How many points to add"),
    ):
        try:
            user_id = str(user.id)
            user_name = user.display_name
            await add_points(user_id, user_name, points)
            embed = nextcord.Embed(
                title=t("EconomyManageCog", "economyset.addpoints.title").format(currency=self.currency),
                description=t("EconomyManageCog", "economyset.addpoints.message").format(points=points, currency=self.currency, user_name=user_name),
                color=nextcord.Color.blurple(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(name="checkpoints", description=t("EconomyManageCog", "economyset.checkpoints.description"))
    @restrict_command()
    async def checkpoints(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="Select the user"),
    ):
        try:
            user_id = str(user.id)
            user_name = user.display_name
            user_name, points = await get_points(user_id, user_name)
            embed = nextcord.Embed(
                title=t("EconomyManageCog", "economyset.checkpoints.title").format(currency=self.currency),
                description=t("EconomyManageCog", "economyset.checkpoints.message").format(user_name=user_name, points=points, currency=self.currency),
                color=nextcord.Color.blurple(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(name="setpoints", description=t("EconomyManageCog", "economyset.setpoints.description"))
    @restrict_command()
    async def setpoints(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="Select the user"),
        points: int = nextcord.SlashOption(description="How many points to set"),
    ):
        try:
            user_id = str(user.id)
            user_name = user.display_name
            await set_points(user_id, user_name, points)
            embed = nextcord.Embed(
                title=t("EconomyManageCog", "economyset.setpoints.title").format(currency=self.currency),
                description=t("EconomyManageCog", "economyset.setpoints.message").format(user_name=user_name, points=points, currency=self.currency),
                color=nextcord.Color.blurple(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(
        name="forcesteam", description=t("EconomyManageCog", "economyset.forcesteam.description")
    )
    @restrict_command()
    async def force_steam(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="Select the user"),
        steam_id: str = nextcord.SlashOption(description="Enter the user's Steam ID"),
    ):
        try:
            user_id = str(user.id)
            user_name = user.display_name
            await link_steam_account(user_id, steam_id)
            await update_discord_username(user_id, user_name)
            await interaction.response.send_message(
                t("EconomyManageCog", "economyset.forcesteam.message").format(steam_id=steam_id, user_name=user.display_name),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(
        name="removepoints", description=t("EconomyManageCog", "economyset.removepoints.description")
    )
    @restrict_command()
    async def removepoints(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="Select the user"),
        points: int = nextcord.SlashOption(description="How many points to remove"),
    ):
        try:
            user_id = str(user.id)
            user_name = user.display_name
            user_name, current_points = await get_points(user_id, user_name)
            if current_points < points:
                await interaction.response.send_message(
                    t("EconomyManageCog", "economyset.removepoints.insufficient_funds").format(user_name=user_name, currency=self.currency),
                    ephemeral=True,
                )
                return
            new_points = current_points - points
            await set_points(user_id, user_name, new_points)
            embed = nextcord.Embed(
                title=t("EconomyManageCog", "economyset.removepoints.title").format(currency=self.currency),
                description=t("EconomyManageCog", "economyset.removepoints.message").format(points=points, currency=self.currency, user_name=user_name),
                color=nextcord.Color.blurple(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(
        name="help", description=t("EconomyManageCog", "economyset.help.description")
    )
    @restrict_command()
    async def help(self, interaction: nextcord.Interaction):
        try:
            embed = nextcord.Embed(
                title=t("EconomyManageCog", "economyset.help.title"),
                color=nextcord.Color.blurple()
            )
            embed.add_field(
                name="Commands",
                value=t("EconomyManageCog", "economyset.help.commands"),
                inline=False,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)
        
    @economyset.subcommand(
        name="settings", description=t("EconomyManageCog", "economyset.settings.description")
    )
    @restrict_command()
    async def economy_settings(self, interaction: nextcord.Interaction):
        try:
            settings = await fetch_economy_settings()
            modal = EconomySettingsModal(settings)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(
        name="timers", description=t("EconomyManageCog", "economyset.timers.description")
    )
    @restrict_command()
    async def timer_settings(self, interaction: nextcord.Interaction):
        try:
            settings = await fetch_economy_settings()
            modal = TimerSettingsModal(settings)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(
        name="misc", description=t("EconomyManageCog", "economyset.etc.description")
    )
    @restrict_command()
    async def etc_settings(self, interaction: nextcord.Interaction):
        try:
            settings = await fetch_economy_settings()
            modal = EtcEconomySettingsModal(settings)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(
        name="vote", description=t("EconomyManageCog", "economyset.vote.description")
    )
    @restrict_command()
    async def vote_settings(self, interaction: nextcord.Interaction):
        try:
            settings = await fetch_economy_settings()
            modal = VoteSettingsModal(settings)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(EconomyManageCog(bot))
