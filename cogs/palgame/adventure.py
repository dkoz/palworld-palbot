import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import random
import time
import json
import os
from utils.palgame import (
    get_pals,
    add_experience,
    level_up,
    get_palgame_settings
)
from utils.database import add_points
from utils.errorhandling import restrict_command

class AdventureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pals = self.load_pals()
        self.cooldowns = {}

    def load_pals(self):
        with open(os.path.join('gamedata', 'game.json'), 'r') as file:
            return json.load(file)

    def check_cooldown(self, user_id, cooldown_period):
        if user_id in self.cooldowns:
            time_elapsed = time.time() - self.cooldowns[user_id]
            if time_elapsed < cooldown_period:
                return cooldown_period - time_elapsed
        return None

    def update_cooldown(self, user_id):
        self.cooldowns[user_id] = time.time()

    async def autocomplete_pals(self, interaction: nextcord.Interaction, current: str):
        user_pals = await get_pals(str(interaction.user.id))
        choices = []

        if current:
            choices = [pal[0] for pal in user_pals if current.lower() in pal[0].lower()]
        else:
            top_pals = sorted(user_pals, key=lambda pal: pal[1], reverse=True)[:5]
            choices = [pal[0] for pal in top_pals]

        if interaction.response.is_done():
            return

        await interaction.response.send_autocomplete(choices=choices[:10])

    def get_pal_image(self, pal_name):
        for pal in self.pals:
            if pal['Name'] == pal_name:
                return pal.get('WikiImage')
        return None

    @nextcord.slash_command(name="adventure", description="Send one of your Pals on an adventure!")
    @restrict_command()
    async def adventure(
        self,
        interaction: Interaction,
        pal_name: str = nextcord.SlashOption(description="Choose your Pal", autocomplete=True)
    ):
        user_id = str(interaction.user.id)

        settings = await get_palgame_settings()
        cooldown_period = settings.get("adventure_cooldown", 90)
        reward_min = settings.get("adventure_reward_min", 50)
        reward_max = settings.get("adventure_reward_max", 200)
        experience_min = settings.get("adventure_experience_min", 100)
        experience_max = settings.get("adventure_experience_max", 500)

        remaining_time = self.check_cooldown(user_id, cooldown_period)
        if remaining_time is not None:
            remaining_minutes = int(remaining_time // 60)
            remaining_seconds = int(remaining_time % 60)
            await interaction.response.send_message(
                f"Your Pal is still recovering from their last adventure! Please wait {remaining_minutes} minutes and {remaining_seconds} seconds.",
                ephemeral=True
            )
            return

        user_pals = await get_pals(user_id)
        if pal_name not in [pal[0] for pal in user_pals]:
            await interaction.response.send_message("You don't have this Pal! Please select one of your own Pals.", ephemeral=True)
            return

        pal_image = self.get_pal_image(pal_name)

        self.update_cooldown(user_id)
        adventure_success = random.random() < 0.85

        if adventure_success:
            currency_earned = random.randint(reward_min, reward_max)
            experience_gained = random.randint(experience_min, experience_max)
            await add_experience(user_id, pal_name, experience_gained)
            leveled_up = await level_up(user_id, pal_name)
            await add_points(user_id, interaction.user.name, currency_earned)

            description = f"Your Pal {pal_name} returned from an adventure and earned {currency_earned} coins and gained {experience_gained} experience!"
            if leveled_up:
                description += f"\n🎉 {pal_name} leveled up!"
            embed = nextcord.Embed(
                title="Adventure Successful!",
                description=description,
                color=nextcord.Color.green()
            )
        else:
            broken_item = "Broken Sphere"
            currency_earned = random.randint(5, 20)
            await add_points(user_id, interaction.user.name, currency_earned)
            
            description = f"Your Pal {pal_name} failed the adventure and returned with a {broken_item} and {currency_earned} coins."
            embed = nextcord.Embed(
                title="Adventure Failed!",
                description=description,
                color=nextcord.Color.red()
            )

        if pal_image:
            embed.set_thumbnail(url=pal_image)

        await interaction.response.send_message(embed=embed)

    @adventure.on_autocomplete("pal_name")
    async def autocomplete_pal_name(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return []
        
        await self.autocomplete_pals(interaction, current)

def setup(bot):
    cog = AdventureCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.adventure
        ]
    )
