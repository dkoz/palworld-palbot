import json
import os
import nextcord
from nextcord.ext import commands
from src.utils.errorhandling import restrict_command

class PaldexCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_game_data()

    def load_game_data(self):
        game_data_path = os.path.join("src", "gamedata", "game.json")
        with open(game_data_path, "r", encoding="utf-8") as game_data_file:
            self.game_data = json.load(game_data_file)

    async def autocomplete_pal(self, interaction: nextcord.Interaction, current: str):
        choices = [pal["Name"] for pal in self.game_data if current.lower() in pal["Name"].lower()][:10]
        await interaction.response.send_autocomplete(choices)

    @nextcord.slash_command(description="Search for a Pal in the Paldex")
    @restrict_command()
    async def paldex(
        self,
        interaction: nextcord.Interaction,
        name: str = nextcord.SlashOption(
            description="The name of the Pal.", autocomplete=True),
    ):
        await interaction.response.defer()
        
        # Do not edit this if you don't know what you are doing...
        pal = next((pal for pal in self.game_data if pal["Name"] == name), None)
        if pal:
            embed = nextcord.Embed(
                title=pal['Name'], color=nextcord.Color.blue())
            embed.description = pal["Description"]
            embed.set_thumbnail(url=pal["WikiImage"])
            stats = pal['Stats']
            embed.add_field(name="Stats", value=f"HP: {stats['HP']}\nDefense: {stats['Defense']}\nStamina: {stats['Stamina']}", inline=True)
            embed.add_field(name="Attack", value=f"Melee: {stats['Attack']['Melee']}\nRanged: {stats['Attack']['Ranged']}", inline=True)
            embed.add_field(name="Rarity", value=pal["Rarity"], inline=True)
            
            skills = "\n".join([f"**{skill['Name']}** (*Level: {skill['Level']}*)\n{skill['Description']}" for skill in pal["Skills"]])
            embed.add_field(name="Skills", value=skills, inline=False)

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Pal not found.")

    @paldex.on_autocomplete("name")
    async def autocomplete_pal_name(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return[]
        
        await self.autocomplete_pal(interaction, current)

def setup(bot):
    cog = PaldexCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.paldex,
        ]
    )
