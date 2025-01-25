import nextcord
from nextcord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
import pytz
from src.utils.errorhandling import restrict_command

class GiveawayView(nextcord.ui.View):
    def __init__(self, cog, prize, end_time, host, winners, message):
        super().__init__(timeout=None)
        self.cog = cog
        self.prize = prize
        self.end_time = end_time
        self.host = host
        self.winners = winners
        self.entries = set()
        self.message = message
        self.ended = False

    @nextcord.ui.button(emoji='🎉', label='Enter Giveaway', style=nextcord.ButtonStyle.primary)
    async def enter_giveaway(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        user = interaction.user

        if self.ended:
            await interaction.response.send_message("The giveaway has ended. No more entries are allowed.", ephemeral=True)
            return

        if user.id in self.entries:
            await interaction.response.send_message("You've already entered the giveaway!", ephemeral=True)
            return

        self.entries.add(user.id)

        embed = self.message.embeds[0]
        for index, field in enumerate(embed.fields):
            if field.name == "Entries:":
                embed.set_field_at(index, name="Entries:", value=str(len(self.entries)), inline=False)
                break

        await self.message.edit(embed=embed)
        await interaction.response.send_message(f"You've successfully entered the giveaway for {self.prize}!", ephemeral=True)

    async def end_giveaway(self):
        self.ended = True
        for item in self.children:
            item.disabled = True

        await self.message.edit(view=self)

class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="giveaway",
        description="Start a new giveaway",
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    @restrict_command()
    async def giveaway(
        self,
        interaction: nextcord.Interaction,
        prize: str,
        duration: int,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="Select the channel for the giveaway", 
            required=True
        ),
        winners: int = 1
    ):
        local_tz = pytz.timezone("America/New_York")
        end_time = datetime.now(local_tz) + timedelta(minutes=duration)
        timestamp = int(end_time.timestamp())

        embed = nextcord.Embed(
            title=f"{prize}",
            description=(
                f"**Ends:** <t:{timestamp}:R>\n"
                f"**Hosted by:** {interaction.user.mention}\n"
                f"**Winners:** {winners}"
            ),
            color=nextcord.Color.blurple()
        )
        embed.add_field(name="Entries:", value="0", inline=False)

        giveaway_message = await channel.send(embed=embed)

        view = GiveawayView(self, prize, end_time, interaction.user, winners, giveaway_message)
        await giveaway_message.edit(view=view)

        await interaction.response.send_message(f"Giveaway started in {channel.mention} for **{prize}**!", ephemeral=True)

        asyncio.create_task(self.wait_for_giveaway_end(duration * 60, view, giveaway_message))

    async def wait_for_giveaway_end(self, sleep_time, view, giveaway_message):
        await asyncio.sleep(sleep_time)
        await view.end_giveaway()
        await self.end_giveaway(view, giveaway_message)

    async def end_giveaway(self, view, giveaway_message):
        try:
            if len(view.entries) > 0:
                entries_list = list(view.entries)
                winners_list = random.sample(entries_list, k=min(view.winners, len(entries_list)))
                winner_mentions = ", ".join([f"<@{winner_id}>" for winner_id in winners_list])

                embed = nextcord.Embed(
                    title="🎉 Giveaway Ended! 🎉",
                    description=f"Congratulations to: {winner_mentions}",
                    color=nextcord.Color.gold()
                )
                await giveaway_message.channel.send(embed=embed)
            else:
                embed = nextcord.Embed(
                    title="Giveaway Ended!",
                    description="No valid participants. Better luck next time!",
                    color=nextcord.Color.red()
                )
                await giveaway_message.channel.send(embed=embed)
        except Exception as e:
            print(f"Error ending giveaway: {e}")

def setup(bot):
    cog = GiveawayCog(bot)
    bot.add_cog(cog)
    
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.append(cog.giveaway)
