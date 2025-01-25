import json
import os
import nextcord
import time
from nextcord.ext import commands
from src.utils.palgame import (
    get_pals,
    add_experience,
    level_up,
    get_stats,
    get_palgame_settings
)
from src.utils.database import add_points
import random
from src.utils.errorhandling import restrict_command

class BattleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pals = self.load_pals()
        self.cooldowns = {}

    def load_pals(self):
        with open(os.path.join('src', 'gamedata', 'game.json'), 'r') as file:
            return json.load(file)

    def check_cooldown(self, user_id, cooldown_period):
        if user_id in self.cooldowns:
            time_elapsed = time.time() - self.cooldowns[user_id]
            if time_elapsed < cooldown_period:
                return cooldown_period - time_elapsed
        return None

    def update_cooldown(self, user_id):
        self.cooldowns[user_id] = time.time()

    async def pal_autocomplete(self, interaction: nextcord.Interaction, current: str):
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

    @nextcord.slash_command(
        name="battle",
        description="Engage your Pal in a battle to earn experience!",
        default_member_permissions=nextcord.Permissions(send_messages=True),
    )
    @restrict_command()
    async def battle(
        self,
        interaction: nextcord.Interaction,
        pal_name: str = nextcord.SlashOption(description="Choose your Pal", autocomplete=True)
    ):
        user_id = str(interaction.user.id)

        settings = await get_palgame_settings()
        cooldown_period = settings.get("battle_cooldown", 90)
        reward_min = settings.get("battle_reward_min", 10)
        reward_max = settings.get("battle_reward_max", 50)
        experience_reward = settings.get("battle_experience", 100)

        remaining_time = self.check_cooldown(user_id, cooldown_period)
        if remaining_time is not None:
            remaining_seconds = int(remaining_time)
            await interaction.response.send_message(f"You are on cooldown! Please wait {remaining_seconds} seconds before starting another battle.")
            return

        self.update_cooldown(user_id)

        await interaction.response.defer()

        user_pals = await get_pals(user_id)
        user_pal = next((pal for pal in user_pals if pal[0] == pal_name), None)
        if not user_pal:
            embed = nextcord.Embed(title="Error", description="Pal not found.", color=nextcord.Color.red())
            await interaction.followup.send(embed=embed)
            return

        pal_data = next((pal for pal in self.pals if pal['Name'] == pal_name), None)
        opponent_pal = random.choice(self.pals)
        user_pal_stats = await get_stats(user_id, pal_name)
        user_hp = pal_data['Stats']['HP'] + (user_pal_stats[0] * 10)
        opponent_hp = opponent_pal['Stats']['HP']
        user_stamina = pal_data['Stats']['Stamina']
        opponent_stamina = opponent_pal['Stats']['Stamina']

        view = self.create_battle_view(pal_data, interaction.user, opponent_pal, user_pal_stats[0], user_pal_stats[1], user_hp, opponent_hp, user_stamina, opponent_stamina, reward_min, reward_max, experience_reward)
        
        embed = nextcord.Embed(title=f"Battle: {pal_name} VS {opponent_pal['Name']}", description="Choose your action:", color=nextcord.Color.blue())
        embed.add_field(name=f"{pal_name} Stats", value=self.format_stats(pal_data, user_pal_stats[0]), inline=False)
        embed.add_field(name=f"{opponent_pal['Name']} Stats", value=self.format_stats(opponent_pal), inline=False)
        embed.set_thumbnail(url=opponent_pal['WikiImage'])
        await interaction.followup.send(embed=embed, view=view)

    def format_stats(self, pal, level=1):
        stats = pal['Stats']
        return (f"HP: {stats['HP'] + (level * 10)}\n"
                f"Attack (Melee): {stats['Attack']['Melee'] + (level * 2)}\n"
                f"Attack (Ranged): {stats['Attack']['Ranged'] + (level * 2)}\n"
                f"Defense: {stats['Defense'] + (level * 2)}\n"
                f"Stamina: {stats['Stamina'] + (level * 5)}")

    def create_battle_view(self, pal_data, user, opponent_pal, level, experience, user_hp, opponent_hp, user_stamina, opponent_stamina, reward_min, reward_max, experience_reward):
        view = nextcord.ui.View(timeout=300)

        for skill in pal_data['Skills']:
            if level >= skill['Level']:
                button = nextcord.ui.Button(label=skill['Name'], style=nextcord.ButtonStyle.primary)
                button.callback = lambda inter, s=skill, p_data=pal_data: self.skill_callback(
                    inter, user, opponent_pal, s, p_data, level, experience, user_hp, opponent_hp, user_stamina, opponent_stamina, reward_min, reward_max, experience_reward
                )
                view.add_item(button)
        return view

    async def skill_callback(self, interaction, user, opponent_pal, skill, pal_data, level, experience, user_hp, opponent_hp, user_stamina, opponent_stamina, reward_min, reward_max, experience_reward):
        if interaction.user.id != user.id:
            await interaction.response.send_message("You can't interact with this button.", ephemeral=True)
            return

        if interaction.response.is_done():
            return

        if user_stamina <= 0:
            await interaction.response.send_message(f"{pal_data['Name']} is too exhausted to use {skill['Name']}! You need to rest.")
            return

        damage = self.calculate_damage(skill['Power'], 'Melee', user_pal=pal_data, opponent_pal=opponent_pal)
        opponent_hp -= damage
        if opponent_hp < 0:
            opponent_hp = 0
        user_stamina -= 10

        result_text = f"{pal_data['Name']} used {skill['Name']}! It dealt {damage} damage. {opponent_pal['Name']} has {opponent_hp} HP left."

        new_experience = experience

        if opponent_hp <= 0:
            result_text += f"\n{opponent_pal['Name']} has been defeated!"

            rarity_multiplier = opponent_pal.get('Rarity', 1)
            experience_gained = experience_reward * rarity_multiplier
            new_experience += experience_gained
            result_text += f"\n{pal_data['Name']} gained {experience_gained} experience points."

            required_experience = 1000 + (level - 1) * 200

            leveled_up = False
            while new_experience >= required_experience:
                level += 1
                new_experience -= required_experience
                required_experience = 1000 + (level - 1) * 200
                leveled_up = True

            await add_experience(str(interaction.user.id), pal_data['Name'], experience_gained)
            if leveled_up:
                await level_up(str(interaction.user.id), pal_data['Name'])

            if leveled_up:
                result_text += f"\n{pal_data['Name']} leveled up to Level {level}!"
            else:
                result_text += f"\n{pal_data['Name']} is still at Level {level}."

            points_awarded = random.randint(reward_min, reward_max)
            await add_points(str(interaction.user.id), user.name, points_awarded)
            result_text += f"\nYou earned {points_awarded} points for winning the battle!"

            embed = nextcord.Embed(title="Battle Result", description=result_text, color=nextcord.Color.green())
            await interaction.response.edit_message(embed=embed, view=None)
            return

        opponent_skill = random.choice(opponent_pal['Skills'])
        opponent_damage = self.calculate_damage(opponent_skill['Power'], 'Melee', user_pal=opponent_pal, opponent_pal=pal_data)
        user_hp -= opponent_damage
        if user_hp < 0:
            user_hp = 0
        opponent_stamina -= 10

        result_text += f"\n\n{opponent_pal['Name']} used {opponent_skill['Name']}! It dealt {opponent_damage} damage. {pal_data['Name']} has {user_hp} HP left."

        if user_hp <= 0:
            result_text += f"\n{pal_data['Name']} has been defeated!"
            embed = nextcord.Embed(title="Battle Result", description=result_text, color=nextcord.Color.red())
            await interaction.response.edit_message(embed=embed, view=None)
            return

        embed = nextcord.Embed(title="Battle Update", description=result_text, color=nextcord.Color.orange())
        view = self.create_battle_view(pal_data, user, opponent_pal, level, new_experience, user_hp, opponent_hp, user_stamina, opponent_stamina, reward_min, reward_max, experience_reward)
        await interaction.response.edit_message(embed=embed, view=view)

    def calculate_damage(self, skill_power, attack_type, user_pal, opponent_pal):
        user_attack = user_pal['Stats']['Attack'][attack_type]
        opponent_defense = opponent_pal['Stats']['Defense']
        base_damage = skill_power + (user_attack * 0.5) - (opponent_defense * 0.3)
        return max(1, int(base_damage + random.randint(-5, 5)))

    @battle.on_autocomplete("pal_name")
    async def on_autocomplete_pal(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return []

        await self.pal_autocomplete(interaction, current)

def setup(bot):
    cog = BattleCog(bot)
    bot.add_cog(cog)
    
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.battle,
        ]
    )
