import nextcord
from nextcord.ext import commands
from util.economy_system import (
    add_points,
    get_points,
    set_points,
    link_steam_account,
    update_discord_username,
)
import json

class EconomyManageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            self.economy_config = json.load(config_file)
        self.economy_config = self.economy_config.get("ECONOMY_SETTINGS", {})
        self.currency = self.economy_config.get("currency", "points")

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
        user_id = str(user.id)
        user_name = user.display_name
        add_points(user_id, user_name, points)
        emebd = nextcord.Embed(
            title=f"Added {self.currency}",
            description=f"Added {points} {self.currency} to {user_name}.",
            color=nextcord.Color.blurple(),
        )
        await interaction.response.send_message(embed=emebd, ephemeral=True)

    @economyset.subcommand(name="checkpoints", description="Check a user's points.")
    async def checkpoints(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="Select the user"),
    ):
        user_id = str(user.id)
        user_name = user.display_name
        user_name, points = get_points(user_id, user_name)

        embed = nextcord.Embed(
            title=f"Check {self.currency}",
            description=f"{user_name} has {points} {self.currency}.",
            color=nextcord.Color.blurple(),
        )
        if user_name:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("User not found.", ephemeral=True)

    @economyset.subcommand(name="setpoints", description="Set a user's points.")
    async def setpoints(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="Select the user"),
        points: int = nextcord.SlashOption(description="How many points to set"),
    ):
        user_id = str(user.id)
        user_name = user.display_name
        set_points(user_id, user_name, points)
        embed = nextcord.Embed(
            title=f"Set {self.currency}",
            description=f"Set {user_name}'s {self.currency} to {points}.",
            color=nextcord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @economyset.subcommand(
        name="forcesteam", description="Force link a user's Steam account."
    )
    async def force_steam(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="Select the user"),
        steam_id: str = nextcord.SlashOption(description="Enter the user's Steam ID"),
        verification_code: str = nextcord.SlashOption(
            description="Enter the verification code"
        ),
    ):
        user_id = str(user.id)
        user_name = user.display_name
        await link_steam_account(user_id, steam_id, verification_code)

        await update_discord_username(user_id, user_name)

        await interaction.response.send_message(
            f"Linked Steam account {steam_id} to {user.display_name}.", ephemeral=True
        )

    @economyset.subcommand(
        name="removepoints", description="Remove points from a user."
    )
    async def removepoints(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="Select the user"),
        points: int = nextcord.SlashOption(description="How many points to remove"),
    ):
        user_id = str(user.id)
        user_name = user.display_name
        user_name, current_points = get_points(user_id, user_name)
        if current_points < points:
            await interaction.response.send_message(
                f"{user_name} does not have enough {self.currency} to remove.",
                ephemeral=True,
            )
            return
        new_points = current_points - points
        set_points(user_id, user_name, new_points)
        embed = nextcord.Embed(
            title=f"Removed {self.currency}",
            description=f"Removed {points} {self.currency} from {user_name}.",
            color=nextcord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @economyset.subcommand(
        name="help", description="Display help for the economy management commands."
    )
    async def help(self, interaction: nextcord.Interaction):
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
        await interaction.response.send_message(embed=embed)

def setup(bot):
    config_path = "config.json"
    with open(config_path) as config_file:
        config = json.load(config_file)

    economy_settings = config.get("ECONOMY_SETTINGS", {})
    if not economy_settings.get("enabled", False):
        return

    bot.add_cog(EconomyManageCog(bot))
