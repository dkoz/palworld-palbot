import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ButtonStyle
from nextcord.ui import Button, View
import random
import json
import time
import os
from utils.palgame import (
    add_pal,
    check_pal
)
from utils.database import add_points
from utils.errorhandling import restrict_command

class PalGameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pals = self.load_pals()
        self.cooldowns = {}

    def load_pals(self):
        with open(os.path.join('gamedata', 'game.json'), 'r') as file:
            data = json.load(file)
        return data

    def check_cooldown(self, user_id, cooldown_period):
        if user_id in self.cooldowns:
            time_elapsed = time.time() - self.cooldowns[user_id]
            if time_elapsed < cooldown_period:
                return cooldown_period - time_elapsed
        return None

    def update_cooldown(self, user_id):
        self.cooldowns[user_id] = time.time()

    async def user_has_pal(self, user_id, pal_name):
        return await check_pal(user_id, pal_name)

    @nextcord.slash_command(name="catch", description="Catch a random Pal!")
    @restrict_command()
    async def catch(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        cooldown_period = 90

        remaining_time = self.check_cooldown(user_id, cooldown_period)
        if remaining_time is not None:
            remaining_seconds = int(remaining_time)
            await interaction.response.send_message(f"You just caught a pal! Please wait {remaining_seconds} seconds before catching another.")
            return

        self.update_cooldown(user_id)
        random_pal = random.choice(self.pals)
        pal_name = random_pal['Name']

        if await self.user_has_pal(user_id, pal_name):
            points_awarded = random.randint(10, 50)
            await add_points(user_id, interaction.user.name, points_awarded)
            
            embed = nextcord.Embed(
                title="Already Caught!", 
                description=f"You already have {pal_name}, but you earned {points_awarded} points!", 
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        view = self.create_catch_view(random_pal, interaction.user)
        embed = nextcord.Embed(title="A wild Pal appeared!")
        embed.add_field(name=random_pal['Name'], value=random_pal['Description'], inline=False)
        embed.set_thumbnail(url=random_pal['WikiImage'])
        await interaction.response.send_message(embed=embed, view=view)

    def create_catch_view(self, pal, user):
        view = View()

        catch_button = Button(style=ButtonStyle.green, label="Catch")
        butcher_button = Button(style=ButtonStyle.red, label="Butcher")

        async def catch_callback(interaction: Interaction):
            if await self.user_has_pal(str(user.id), pal['Name']):
                embed = nextcord.Embed(
                    title="Already Caught!", 
                    description=f"You already have {pal['Name']}.", 
                    color=nextcord.Color.red()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                return

            await add_pal(str(user.id), pal['Name'])
            embed = nextcord.Embed(
                title="Congratulations!", 
                description=f"You have successfully caught {pal['Name']}."
            )
            await interaction.response.edit_message(embed=embed, view=None)

        async def butcher_callback(interaction: Interaction):
            points_awarded = random.randint(10, 50)
            await add_points(str(user.id), user.name, points_awarded)
            embed = nextcord.Embed(
                title="Butchered!", 
                description=f"You have butchered {pal['Name']} and earned {points_awarded} points."
            )
            await interaction.response.edit_message(embed=embed, view=None)

        catch_button.callback = catch_callback
        butcher_button.callback = butcher_callback

        view.add_item(catch_button)
        view.add_item(butcher_button)
        return view  

def setup(bot):
    cog = PalGameCog(bot)
    bot.add_cog(cog)
    
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.catch
        ]
    )
