import json
import os
import nextcord
from nextcord.ext import commands
from utils.palgame import (
    get_pals,
    add_experience,
    level_up,
    get_stats
)
from utils.database import add_points
import random

class BattleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pals = self.load_pals()

    def load_pals(self):
        with open(os.path.join('gamedata', 'game.json'), 'r') as file:
            return json.load(file)

    async def pal_autocomplete(self, interaction: nextcord.Interaction, current: str):
        user_pals = await get_pals(str(interaction.user.id))
        choices = [pal[0] for pal in user_pals if current.lower() in pal[0].lower()]
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(
        name="battle",
        description="Engage your Pal in a battle to earn experience!",
        default_member_permissions=nextcord.Permissions(send_messages=True),
    )
    async def battle(
        self,
        interaction: nextcord.Interaction,
        pal_name: str = nextcord.SlashOption(description="Choose your Pal", autocomplete=True)
    ):
        await interaction.response.defer(ephemeral=True)

        user_id = str(interaction.user.id)
        user_pals = await get_pals(user_id)
        user_pal = next((pal for pal in user_pals if pal[0] == pal_name), None)
        if not user_pal:
            embed = nextcord.Embed(title="Error", description="Pal not found.", color=nextcord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        pal_data = next((pal for pal in self.pals if pal['Name'] == pal_name), None)
        opponent_pal = random.choice(self.pals)
        user_pal_stats = await get_stats(user_id, pal_name)
        user_hp = pal_data['Stats']['HP'] + (user_pal_stats[0] * 10)
        opponent_hp = opponent_pal['Stats']['HP']
        user_stamina = pal_data['Stats']['Stamina']
        opponent_stamina = opponent_pal['Stats']['Stamina']

        view = self.create_battle_view(pal_data, interaction.user, opponent_pal, user_pal_stats[0], user_pal_stats[1], user_hp, opponent_hp, user_stamina, opponent_stamina)
        
        embed = nextcord.Embed(title=f"Battle: {pal_name} VS {opponent_pal['Name']}", description="Choose your action:", color=nextcord.Color.blue())
        embed.add_field(name=f"{pal_name} Stats", value=self.format_stats(pal_data, user_pal_stats[0]), inline=False)
        embed.add_field(name=f"{opponent_pal['Name']} Stats", value=self.format_stats(opponent_pal), inline=False)
        embed.set_thumbnail(url=opponent_pal['WikiImage'])
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    def format_stats(self, pal, level=1):
        stats = pal['Stats']
        return (f"HP: {stats['HP'] + (level * 10)}\n"
                f"Attack (Melee): {stats['Attack']['Melee'] + (level * 2)}\n"
                f"Attack (Ranged): {stats['Attack']['Ranged'] + (level * 2)}\n"
                f"Defense: {stats['Defense'] + (level * 2)}\n"
                f"Stamina: {stats['Stamina'] + (level * 5)}")

    def create_battle_view(self, pal_data, user, opponent_pal, level, experience, user_hp, opponent_hp, user_stamina, opponent_stamina):
        view = nextcord.ui.View()

        for skill in pal_data['Skills']:
            if level >= skill['Level']:
                button = nextcord.ui.Button(label=skill['Name'], style=nextcord.ButtonStyle.primary)
                button.callback = lambda inter, s=skill, p_data=pal_data: self.skill_callback(
                    inter, user, opponent_pal, s, p_data, level, experience, user_hp, opponent_hp, user_stamina, opponent_stamina)
                view.add_item(button)
        return view

    async def skill_callback(self, interaction, user, opponent_pal, skill, pal_data, level, experience, user_hp, opponent_hp, user_stamina, opponent_stamina):
        if user_stamina <= 0:
            await interaction.response.send_message(f"{pal_data['Name']} is too exhausted to use {skill['Name']}! You need to rest.", ephemeral=True)
            return

        damage = self.calculate_damage(skill['Power'], 'Melee', user_pal=pal_data, opponent_pal=opponent_pal)
        opponent_hp -= damage
        user_stamina -= 10

        result_text = f"{pal_data['Name']} used {skill['Name']}! It dealt {damage} damage. {opponent_pal['Name']} has {opponent_hp} HP left."

        if opponent_hp <= 0:
            result_text += f"\n{opponent_pal['Name']} has been defeated!"

            experience_gained = 50
            new_experience = experience + experience_gained
            result_text += f"\n{pal_data['Name']} gained {experience_gained} experience points."

            leveled_up = False
            if new_experience >= 1000:
                await level_up(str(interaction.user.id), pal_data['Name'])
                new_experience -= 1000
                result_text += f"\n{pal_data['Name']} leveled up!"
                leveled_up = True

            await add_experience(str(interaction.user.id), pal_data['Name'], experience_gained)

            points_awarded = random.randint(10, 20)
            await add_points(str(interaction.user.id), user.name, points_awarded)
            result_text += f"\nYou earned {points_awarded} points for winning the battle!"

            embed = nextcord.Embed(title="Battle Result", description=result_text, color=nextcord.Color.green())
            await interaction.response.edit_message(embed=embed, view=None)
            return

        opponent_skill = random.choice(opponent_pal['Skills'])
        opponent_damage = self.calculate_damage(opponent_skill['Power'], 'Melee', user_pal=opponent_pal, opponent_pal=pal_data)
        user_hp -= opponent_damage
        opponent_stamina -= 10

        result_text += f"\n\n{opponent_pal['Name']} used {opponent_skill['Name']}! It dealt {opponent_damage} damage. {pal_data['Name']} has {user_hp} HP left."

        if user_hp <= 0:
            result_text += f"\n{pal_data['Name']} has been defeated!"
            embed = nextcord.Embed(title="Battle Result", description=result_text, color=nextcord.Color.red())
            await interaction.response.edit_message(embed=embed, view=None)
            return

        embed = nextcord.Embed(title="Battle Update", description=result_text, color=nextcord.Color.orange())
        view = self.create_battle_view(pal_data, user, opponent_pal, level, experience, user_hp, opponent_hp, user_stamina, opponent_stamina)
        await interaction.response.edit_message(embed=embed, view=view)

    def calculate_damage(self, skill_power, attack_type, user_pal, opponent_pal):
        user_attack = user_pal['Stats']['Attack'][attack_type]
        opponent_defense = opponent_pal['Stats']['Defense']
        base_damage = skill_power + (user_attack * 0.5) - (opponent_defense * 0.3)
        return max(1, int(base_damage + random.randint(-5, 5)))

    @battle.on_autocomplete("pal_name")
    async def on_autocomplete_pal(self, interaction: nextcord.Interaction, current: str):
        await self.pal_autocomplete(interaction, current)

def setup(bot):
    bot.add_cog(BattleCog(bot))
