import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ButtonStyle
from nextcord.ui import Button, View
import json
from utils.palgame import get_pals
from utils.errorhandling import restrict_command

class PalListView(View):
    def __init__(self, user_pals):
        super().__init__()
        self.user_pals = user_pals
        self.current_page = 0

    async def generate_pal_embed(self):
        embed = nextcord.Embed(
            title="Your Pals",
            description="Here are some of the Pals you've caught!",
            color=nextcord.Color.green(),
        )
        
        start = self.current_page * 6
        end = min(start + 6, len(self.user_pals))

        for pal in self.user_pals[start:end]:
            embed.add_field(name=f"{pal[0]} (Level {pal[1]})", value=f"Experience: {pal[2]}", inline=False)

        embed.set_footer(
            text=f"Page {self.current_page + 1} of {len(self.user_pals) // 6 + 1}"
        )

        return embed

    @nextcord.ui.button(label="Previous", style=ButtonStyle.blurple)
    async def previous_button_callback(self, button: Button, interaction: Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.generate_pal_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @nextcord.ui.button(label="Next", style=ButtonStyle.blurple)
    async def next_button_callback(self, button: Button, interaction: Interaction):
        if (self.current_page + 1) * 6 < len(self.user_pals):
            self.current_page += 1
            embed = await self.generate_pal_embed()
            await interaction.response.edit_message(embed=embed, view=self)

class PalboxCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pals = self.load_pals()

    def load_pals(self):
        with open('gamedata/game.json', 'r') as file:
            data = json.load(file)
        return data

    @nextcord.slash_command(name="palbox", description="Show all your Pals.")
    @restrict_command()
    async def palbox(self, interaction: Interaction):
        try:
            await interaction.response.defer()
            user_pals = await get_pals(str(interaction.user.id))
            if not user_pals:
                await interaction.followup.send("You don't have any Pals yet! Use `/catch` to get some.")
                return

            user_pals = sorted(user_pals, key=lambda pal: pal[1], reverse=True)
            view = PalListView(user_pals)
            embed = await view.generate_pal_embed()
            await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            await interaction.followup.send(f"Error with `palbox` command: {e}")
            

def setup(bot):
    cog = PalboxCog(bot)
    bot.add_cog(cog)
    
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.palbox
        ]
    )
