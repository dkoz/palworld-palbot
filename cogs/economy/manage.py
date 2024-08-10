import nextcord
from nextcord.ext import commands
from utils.database import (
    add_points,
    get_points,
    set_points,
    link_steam_account,
    update_discord_username,
    get_economy_setting,
)
from utils.modals import EconomySettingsModal, TimerSettingsModal

class EconomyManageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_config())

    async def load_config(self):
        self.currency = await get_economy_setting("currency_name") or "points"

    @nextcord.slash_command(
        name="economyset",
        description="Economy management.",
        default_member_permissions=nextcord.Permissions(administrator=True),
    )
    async def economyset(self, _interaction: nextcord.Interaction):
        pass

    @economyset.subcommand(name="addpoints", description="Add points to a user.")
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
                title=f"Added {self.currency}",
                description=f"Added {points} {self.currency} to {user_name}.",
                color=nextcord.Color.blurple(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(name="checkpoints", description="Check a user's points.")
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
                title=f"Check {self.currency}",
                description=f"{user_name} has {points} {self.currency}.",
                color=nextcord.Color.blurple(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(name="setpoints", description="Set a user's points.")
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
                title=f"Set {self.currency}",
                description=f"Set {user_name}'s {self.currency} to {points}.",
                color=nextcord.Color.blurple(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(
        name="forcesteam", description="Force link a user's Steam account."
    )
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
                f"Linked Steam account {steam_id} to {user.display_name}.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(
        name="removepoints", description="Remove points from a user."
    )
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
                    f"{user_name} does not have enough {self.currency} to remove.",
                    ephemeral=True,
                )
                return
            new_points = current_points - points
            await set_points(user_id, user_name, new_points)
            embed = nextcord.Embed(
                title=f"Removed {self.currency}",
                description=f"Removed {points} {self.currency} from {user_name}.",
                color=nextcord.Color.blurple(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

    @economyset.subcommand(
        name="help", description="Display help for the economy management commands."
    )
    async def help(self, interaction: nextcord.Interaction):
        try:
            embed = nextcord.Embed(
                title="Economy Management Help", color=nextcord.Color.blurple()
            )
            embed.add_field(
                name="Commands",
                value="`/economyset addpoints` - Add points to a user.\n"
                "`/economyset checkpoints` - Check a user's points.\n"
                "`/economyset setpoints` - Set a user's points.\n"
                "`/economyset removepoints` - Remove points from a user.\n"
                "`/economyset forcesteam` - Force link a user's Steam account.",
                inline=False,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)
        
    @economyset.subcommand(
        name="settings", description="Edit the economy settings"
    )
    async def economy_settings(self, interaction: nextcord.Interaction):
        try:
            modal = EconomySettingsModal()
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)
            
    # Timer settings
    @economyset.subcommand(
        name="timers", description="Edit the economy timers"
    )
    async def timer_settings(self, interaction: nextcord.Interaction):
        try:
            modal = TimerSettingsModal()
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(f"Unexpected error: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(EconomyManageCog(bot))
