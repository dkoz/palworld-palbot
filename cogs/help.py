import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View

class HelpView(View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.current_page = 0

    async def generate_help_embed(self):
        embed = nextcord.Embed(title="Help Menu", description="List of all available commands.", color=nextcord.Color.blue())
        embed.set_footer(text=f"Page {self.current_page + 1}", icon_url=self.bot.user.avatar.url)

        commands = self.bot.all_slash_commands if hasattr(self.bot, 'all_slash_commands') else []
        start = self.current_page * 6
        end = min(start + 6, len(commands))

        for command in commands[start:end]:
            embed.add_field(name=f"`/{command.name}`", value=command.description or "No description", inline=True)

        return embed

    @nextcord.ui.button(label="Previous", style=nextcord.ButtonStyle.grey)
    async def previous_button_callback(self, button, interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_help_message(interaction)

    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.grey)
    async def next_button_callback(self, button, interaction):
        if (self.current_page + 1) * 6 < len(self.bot.all_slash_commands if hasattr(self.bot, 'all_slash_commands') else []):
            self.current_page += 1
            await self.update_help_message(interaction)

    async def update_help_message(self, interaction):
        embed = await self.generate_help_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(description="Shows a list of available commands.")
    async def help(self, interaction: nextcord.Interaction):
        view = HelpView(self.bot)
        embed = await view.generate_help_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # Please do not remove the about me section. I've spent a lot of time on this bot and I would appreciate it if you left it in.
    @nextcord.slash_command(description="Information about the Palworld bot.")
    async def about(self, interaction: nextcord.Interaction):
        bot_avatar_url = self.bot.user.avatar.url

        embed = nextcord.Embed(title="Palworld Bot", color=nextcord.Color.blue())
        embed.set_footer(text="Created by Koz", icon_url=bot_avatar_url)
        embed.add_field(name="About", value="The bot is an open-source project available [here](https://github.com/dkoz/palworld-bot). You can find more info on our readme. I'm always looking for code contributions and support! If there is something wrong with the bot itself, please let me know!", inline=False)
        embed.add_field(name="Creator", value="This bot was created by [Kozejin](https://kozejin.dev). Feel free to add `koz#1337` on discord if you have any questions.", inline=False)

        website_button = Button(label="Support", url="https://discord.gg/3HUq8cJSrX", style=nextcord.ButtonStyle.link)
        github_button = Button(label="GitHub", url="https://github.com/dkoz", style=nextcord.ButtonStyle.link)
        project_button = Button(label="Project", url="https://github.com/dkoz/palworld-bot", style=nextcord.ButtonStyle.link)

        view = View()
        view.add_item(website_button)
        view.add_item(github_button)
        view.add_item(project_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(HelpCog(bot))