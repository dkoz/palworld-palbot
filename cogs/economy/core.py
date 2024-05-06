from nextcord.ext import commands
import nextcord
from util.economy_system import (
    init_db,
    get_points,
    set_points,
    get_top_points,
    get_steam_id,
    get_top_invites,
    link_steam_account,
    update_discord_username,
)
import json
import random
from datetime import datetime, timedelta

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()
        self.load_config()
        self.work_cooldown = {}
        self.daily_cooldown = {}

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            self.economy_config = json.load(config_file)
        self.economy_config = self.economy_config.get("ECONOMY_SETTINGS", {})
        self.currency = self.economy_config.get("currency", "points")
        self.work_reward = self.economy_config.get("work_reward", [1, 10])
        self.work_descriptions = self.economy_config.get(
            "work_description", ["You worked and earned {earned_points} {currency}."]
        )
        self.work_min, self.work_max = self.work_reward
        self.work_timer = self.economy_config.get("work_timer", 60)
        self.daily_reward = self.economy_config.get("daily_reward", 100)
        self.daily_timer = self.economy_config.get("daily_timer", 86400)
        
    def get_bonus_percentage(self, user):
        roles = [role.name for role in user.roles]
        max_bonus = 0
        for role in roles:
            if role in self.economy_config.get("role_bonuses", {}):
                role_bonus = self.economy_config["role_bonuses"][role]
                if role_bonus > max_bonus:
                    max_bonus = role_bonus
        return max_bonus

    async def apply_bonus(self, base_points, user):
        bonus_percentage = self.get_bonus_percentage(user)
        bonus_points = int(base_points * (bonus_percentage / 100.0))
        return base_points + bonus_points

    # Economy Info
    @nextcord.slash_command(
        name="economyinfo", description="Display economy information."
    )
    async def economyinfo(self, interaction: nextcord.Interaction):
        def format_time(seconds):
            if seconds < 3600:
                return f"{int(seconds/60)} minutes"
            hours, remainder = divmod(seconds, 3600)
            minutes = remainder // 60
            return f"{int(hours)} hours {int(minutes)} minutes"

        embed = nextcord.Embed(
            title="Economy Information", color=nextcord.Color.blurple()
        )
        embed.add_field(name="Currency", value=self.currency, inline=False)
        embed.add_field(
            name="Work Reward",
            value=f"{self.work_min}-{self.work_max} {self.currency}",
            inline=False,
        )
        embed.add_field(
            name="Work Cooldown", value=format_time(self.work_timer), inline=False
        )
        embed.add_field(
            name="Daily Cooldown", value=format_time(self.daily_timer), inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Leaderboard for Points
    @nextcord.slash_command(
        name="leaderboard", description="Display the top points leaderboard."
    )
    async def toppoints(self, interaction: nextcord.Interaction):
        top_points = get_top_points()
        embed = nextcord.Embed(
            title=f"Top {self.currency}", color=nextcord.Color.blurple()
        )
        for i, (user_name, points) in enumerate(top_points, start=1):
            embed.add_field(
                name=f"{i}. {user_name}",
                value=f"{points} {self.currency}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    # Transfer Points
    @nextcord.slash_command(
        name="transfer", description="Transfer points to another user."
    )
    async def transferpoints(
        self,
        interaction: nextcord.Interaction,
        recipient: nextcord.Member = nextcord.SlashOption(
            description="Select the recipient"
        ),
        points: int = nextcord.SlashOption(description="How many points to transfer"),
    ):
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        user_name, user_points = get_points(user_id, user_name)
        recipient_id = str(recipient.id)
        recipient_name = recipient.display_name
        recipient_name, recipient_points = get_points(recipient_id, recipient_name)
        if user_points < points:
            await interaction.response.send_message(
                f"You do not have enough {self.currency} to transfer.", ephemeral=True
            )
            return
        new_user_points = user_points - points
        new_recipient_points = recipient_points + points
        set_points(user_id, user_name, new_user_points)
        set_points(recipient_id, recipient_name, new_recipient_points)
        embed = nextcord.Embed(
            title=f"{self.currency} Transfer",
            description=f"Transferred {points} {self.currency} to {recipient_name}.",
            color=nextcord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="balance", description="Check your own points.")
    async def balance(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        user_name, points = get_points(user_id, user_name)
        embed = nextcord.Embed(
            title=f"Your {self.currency} Balance",
            description=f"You have {str(points)} {self.currency} in your account.",
            color=nextcord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="profile", description="Check your profile.")
    async def profile(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        user_name, points = get_points(user_id, user_name)
        steam_id = get_steam_id(user_id)
        embed = nextcord.Embed(
            title=f"{user_name}'s Profile", color=nextcord.Color.blurple()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Discord Username", value=user_name, inline=False)
        embed.add_field(name=f"{self.currency}", value=str(points), inline=False)
        if steam_id:
            embed.add_field(name="Steam ID", value=f"||{steam_id}||", inline=False)
        await interaction.response.send_message(embed=embed)

    # Invite Leaderboard
    @nextcord.slash_command(
        name="topinvites", description="Display the top invite leaderboard."
    )
    async def inviteleaderboard(self, interaction: nextcord.Interaction):
        top_invites = get_top_invites()
        embed = nextcord.Embed(title="Top Invites", color=nextcord.Color.blurple())
        if top_invites:
            for i, (user_name, invite_count) in enumerate(top_invites, start=1):
                embed.add_field(
                    name=f"{i}. {user_name}",
                    value=f"{invite_count} invites",
                    inline=False,
                )
        else:
            embed.description = "No invite data available."
        await interaction.response.send_message(embed=embed)

    # Help Command
    @nextcord.slash_command(
        name="economyhelp", description="Display help for the economy commands."
    )
    async def economyhelp(self, interaction: nextcord.Interaction):
        currency = self.currency
        embed = nextcord.Embed(title="Economy Help", color=nextcord.Color.blurple())
        embed.add_field(
            name="Commands",
            value=f"`/setsteam` - Set your own Steam ID.\n"
            f"`/transfer` - Transfer {currency} to another user.\n"
            f"`/balance` - Check your own {currency}.\n"
            f"`/profile` - Check your profile.\n"
            f"`/work` - Earn {currency} by working.\n"
            f"`/daily` - Claim your daily {currency}.\n"
            f"`/leaderboard` - Display the top {currency} leaderboard.\n"
            f"`/topinvites` - Display the top invite leaderboard.\n"
            f"`/economyinfo` - Display economy information.\n"
            f"`/shop menu` - Displays available items in the shop.\n"
            f"`/shop redeem` - Redeem your {currency} for a shop item."
            f"`/claimreward` - Claim your reward for voting!\n",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Set Steam ID
    @nextcord.slash_command(name="setsteam", description="Set your own Steam ID.")
    async def set_steam(
        self,
        interaction: nextcord.Interaction,
        steam_id: str = nextcord.SlashOption(description="Enter your Steam ID"),
    ):
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        verification_code = "verified"
        await link_steam_account(user_id, steam_id, verification_code)

        await update_discord_username(user_id, user_name)

        await interaction.response.send_message(
            f"Linked Steam account {steam_id} to your account.", ephemeral=True
        )

    # Work Command
    @nextcord.slash_command(name="work", description="Earn points by working.")
    async def work(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        now = datetime.now()
        if user_id in self.work_cooldown and now < self.work_cooldown[
            user_id
        ] + timedelta(seconds=self.work_timer):
            await interaction.response.send_message(
                "You're working too fast. Please take a break.", ephemeral=True
            )
            return
        user_name = interaction.user.display_name
        user_name, points = get_points(user_id, user_name)
        base_points = random.randint(self.work_min, self.work_max)
        earned_points = await self.apply_bonus(base_points, interaction.user)
        new_points = points + earned_points
        set_points(user_id, user_name, new_points)
        desc_text = random.choice(self.work_descriptions).format(
            earned_points=earned_points, currency=self.currency
        )
        embed = nextcord.Embed(
            title="Work", description=desc_text, color=nextcord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)
        self.work_cooldown[user_id] = now

    # Daily Command
    @nextcord.slash_command(name="daily", description="Claim your daily points.")
    async def daily(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        now = datetime.now()
        if user_id in self.daily_cooldown and now < self.daily_cooldown[
            user_id
        ] + timedelta(seconds=self.daily_timer):
            next_claim_time = self.daily_cooldown[user_id] + timedelta(
                seconds=self.daily_timer
            )

            time_diff = next_claim_time - now
            hours, remainder = divmod(time_diff.total_seconds(), 3600)
            minutes = divmod(remainder, 60)[0]

            remaining_time = "{}h {}m".format(int(hours), int(minutes))

            await interaction.response.send_message(
                f"You've already claimed your daily points. Please wait {remaining_time}.",
                ephemeral=True,
            )
            return

        user_name = interaction.user.display_name
        user_name, points = get_points(user_id, user_name)
        base_points = self.daily_reward
        earned_points = await self.apply_bonus(base_points, interaction.user)
        new_points = points + earned_points
        set_points(user_id, user_name, new_points)

        embed = nextcord.Embed(
            title="Daily Reward",
            description=f"Claimed {earned_points} {self.currency}.",
            color=nextcord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed)
        self.daily_cooldown[user_id] = now

def setup(bot):
    config_path = "config.json"
    with open(config_path) as config_file:
        config = json.load(config_file)

    economy_settings = config.get("ECONOMY_SETTINGS", {})
    if not economy_settings.get("enabled", False):
        print("Economy system is disabled in the config.")
        return

    bot.add_cog(EconomyCog(bot))
