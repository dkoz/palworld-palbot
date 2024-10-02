import nextcord
from nextcord.ext import commands
import aiohttp
from utils.database import (
    get_steam_id,
    add_points,
    get_economy_setting
)
from utils.translations import t
from utils.errorhandling import restrict_command

class VoteRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.currency = None
        self.vote_reward = None
        self.server_slug = None
        self.api_key = None
        bot.loop.create_task(self.load_settings())

    async def load_settings(self):
        self.currency = await get_economy_setting("currency_name")
        self.vote_reward = int(await get_economy_setting("vote_reward"))
        self.server_slug = await get_economy_setting("vote_slug")
        self.api_key = await get_economy_setting("vote_apikey")

    async def vote_status(self, steam_id):
        url = f"https://serverlist.gg/api/rewards/{self.server_slug}&key={self.api_key}&steamid={steam_id}&type=check"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

    async def claim_reward(self, steam_id):
        url = f"https://serverlist.gg/api/rewards/{self.server_slug}&key={self.api_key}&steamid={steam_id}&type=claim"
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as response:
                return await response.text()

    @nextcord.slash_command(name="claimreward", description=t("VoteCog", "vote.description"))
    @restrict_command()
    async def votereward(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        steam_id = await get_steam_id(user_id)
        if steam_id is None:
            await interaction.response.send_message(t("VoteCog", "vote.invalid_steam"), ephemeral=True)
            return
        
        vote_status = await self.vote_status(steam_id)
        if vote_status == "1":
            await self.claim_reward(steam_id)
            await add_points(user_id, interaction.user.display_name, self.vote_reward)
            await interaction.response.send_message(t("VoteCog", "vote.vote_success"), ephemeral=True)
        elif vote_status == "2":
            await interaction.response.send_message(t("VoteCog", "vote.vote_claimed"), ephemeral=True)
        else:
            await interaction.response.send_message(t("VoteCog", "vote.vote_error"), ephemeral=True)

def setup(bot):
    bot.add_cog(VoteRewards(bot))
