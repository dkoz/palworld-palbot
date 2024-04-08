import nextcord
from nextcord.ext import commands
import aiohttp
import json
from util.economy_system import get_steam_id, add_points

# This is for https://serverlist.gg

class VoteRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            self.economy_config = json.load(config_file)
        self.economy_config = self.economy_config.get("ECONOMY_SETTINGS", {})
        self.currency = self.economy_config.get("currency", "points")
        self.vote_reward = self.economy_config.get("vote_reward", 100)
        self.server_slug = self.economy_config.get("vote_slug", "server_slug")
        self.api_key = self.economy_config.get("vote_apikey", "api_key")

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

    @nextcord.slash_command(name="claimreward", description="Claim your vote reward.")
    async def votereward(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        steam_id = get_steam_id(user_id)
        if steam_id is None:
            await interaction.response.send_message("Your Steam ID is not linked.", ephemeral=True)
            return
        
        vote_status = await self.vote_status(steam_id)
        if vote_status == "1":
            await self.claim_reward(steam_id)
            add_points(user_id, interaction.user.display_name, self.vote_reward)
            await interaction.response.send_message(f"Thank you for voting! Your reward of {self.vote_reward} {self.currency} has been claimed.", ephemeral=True)
        else:
            await interaction.response.send_message("You either haven't voted in the last 12 hours or already claimed your reward.", ephemeral=True)

def setup(bot):
    config_path = "config.json"
    with open(config_path) as config_file:
        config = json.load(config_file)

    economy_settings = config.get("ECONOMY_SETTINGS", {})
    # Check for both enabled and vote_enabled keys
    if not economy_settings.get("enabled", False) or not economy_settings.get("vote_enabled", False):
        return

    bot.add_cog(VoteRewards(bot))