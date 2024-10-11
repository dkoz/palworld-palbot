import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View
import json
import os
from utils.palgame import get_pals
from utils.errorhandling import restrict_command

class PalListView(View):
    def __init__(self, user_pals, pals_data):
        super().__init__()
        self.user_pals = user_pals
        self.pals_data = pals_data
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
            pal_data = next((p for p in self.pals_data if p["Name"] == pal[0]), None)
            if pal_data:
                stats = self.format_stats(pal_data, pal[1])
                embed.add_field(name=f"{pal[0]} (Level {pal[1]})", value=stats, inline=False)

        embed.set_footer(
            text=f"Page {self.current_page + 1} of {len(self.user_pals) // 6 + 1}"
        )

        return embed

    def format_stats(self, pal_data, level):
        stats = pal_data['Stats']
        return (f"Health: {stats['HP']} (+{level * 10})\n"
                f"Attack (Melee): {stats['Attack']['Melee']} (+{level * 2})\n"
                f"Attack (Ranged): {stats['Attack']['Ranged']} (+{level * 2})\n"
                f"Defense: {stats['Defense']} (+{level * 2})\n"
                f"Stamina: {stats['Stamina']} (+{level * 5})")

    @nextcord.ui.button(label="Previous", style=nextcord.ButtonStyle.blurple)
    async def previous_button_callback(self, button: Button, interaction: nextcord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.generate_pal_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.blurple)
    async def next_button_callback(self, button: Button, interaction: nextcord.Interaction):
        if (self.current_page + 1) * 6 < len(self.user_pals):
            self.current_page += 1
            embed = await self.generate_pal_embed()
            await interaction.response.edit_message(embed=embed, view=self)

class PalboxCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pals = self.load_pals()

    def load_pals(self):
        with open(os.path.join('gamedata', 'game.json'), 'r') as file:
            data = json.load(file)
        return data
    
    def format_stats(self, pal_data, level):
        stats = pal_data['Stats']
        return (f"Health: {stats['HP']} (+{level * 10})\n"
                f"Attack (Melee): {stats['Attack']['Melee']} (+{level * 2})\n"
                f"Attack (Ranged): {stats['Attack']['Ranged']} (+{level * 2})\n"
                f"Defense: {stats['Defense']} (+{level * 2})\n"
                f"Stamina: {stats['Stamina']} (+{level * 5})")
    
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

    @nextcord.slash_command(name="palbox", description="Show all your Pals.")
    @restrict_command()
    async def palbox(self, interaction: nextcord.Interaction, pal_name: str = nextcord.SlashOption(description="Select a Pal (Optional)", required=False, autocomplete=True)):
        try:
            await interaction.response.defer()
            user_pals = await get_pals(str(interaction.user.id))
            if not user_pals:
                await interaction.followup.send("You don't have any Pals yet! Use `/catch` to get some.")
                return

            user_pals = sorted(user_pals, key=lambda pal: pal[1], reverse=True)

            if pal_name:
                selected_pal = next((pal for pal in user_pals if pal[0].lower() == pal_name.lower()), None)
                if selected_pal:
                    pal_data = next((p for p in self.pals if p["Name"] == selected_pal[0]), None)
                    if pal_data:
                        stats = self.format_stats(pal_data, selected_pal[1])
                        embed = nextcord.Embed(
                            title=f"{selected_pal[0]} (Level {selected_pal[1]})",
                            description=f"Experience: {selected_pal[2]}\n{stats}",
                            color=nextcord.Color.green(),
                        )
                        await interaction.followup.send(embed=embed)
                        return
                    else:
                        await interaction.followup.send(f"Pal '{pal_name}' not found in your collection.")
                        return

            view = PalListView(user_pals, self.pals)
            embed = await view.generate_pal_embed()
            await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            await interaction.followup.send(f"Error with `palbox` command: {e}")
            
    @palbox.on_autocomplete("pal_name")
    async def on_autocomplete_pal(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return[]
        
        await self.pal_autocomplete(interaction, current)

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
