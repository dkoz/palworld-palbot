import nextcord
from nextcord.ext import commands
import aiohttp
import json
import os
import asyncio
from util.economy_system import get_steam_id, add_points
from util.rconutility import RconUtility

# This is for https://serverlist.gg

class VoteRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.load_kits()
        self.rcon_util = RconUtility(self.servers)

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            config = json.load(config_file)
        self.servers = config.get("PALWORLD_SERVERS", {})
        self.economy_config = config.get("ECONOMY_SETTINGS", {})
        self.currency = self.economy_config.get("currency", "points")
        self.vote_reward = self.economy_config.get("vote_reward", 100)
        self.server_slug = self.economy_config.get("vote_slug", "server_slug")
        self.api_key = self.economy_config.get("vote_apikey", "api_key")

    def load_kits(self):
        config_path = os.path.join("gamedata", "kits.json")
        with open(config_path) as kits_file:
            self.kits = json.load(kits_file)

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
    
    @nextcord.slash_command(name="claimkit", description="Claim a kit as a vote reward.")
    async def claim_kit(self, interaction: nextcord.Interaction, kit_name: str = nextcord.SlashOption(description="Select a kit", autocomplete=True), server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        user_id = str(interaction.user.id)
        steam_id = get_steam_id(user_id)
        if steam_id is None:
            await interaction.response.send_message("Your Steam ID is not linked.", ephemeral=True)
            return

        vote_status = await self.vote_status(steam_id)
        if vote_status == "1":
            await self.claim_reward(steam_id)
            kit = self.kits.get(kit_name)
            if kit and kit.get("votereward", False):
                for command_template in kit["commands"]:
                    command = command_template.format(steamid=steam_id)
                    asyncio.create_task(self.rcon_util.rcon_command(server, command))
                    await asyncio.sleep(1)
                await interaction.response.send_message(f"Thank you for voting! {kit_name} kit has been claimed.", ephemeral=True)
            else:
                await interaction.response.send_message("Invalid kit selected.", ephemeral=True)
        else:
            await interaction.response.send_message("You either haven't voted in the last 12 hours or already claimed your reward.", ephemeral=True)

    @claim_kit.on_autocomplete("kit_name")
    async def autocomplete_kit_name(self, interaction: nextcord.Interaction, current: str):
        choices = [name for name, details in self.kits.items() if 'votereward' in details and current.lower() in name.lower()]
        await interaction.response.send_autocomplete(choices)

    @claim_kit.on_autocomplete("server")
    async def on_autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        choices = [server for server in self.servers if current.lower() in server.lower()]
        await interaction.response.send_autocomplete(choices)

def setup(bot):
    config_path = "config.json"
    with open(config_path) as config_file:
        config = json.load(config_file)

    economy_settings = config.get("ECONOMY_SETTINGS", {})
    # Check for both enabled and vote_enabled keys
    if not economy_settings.get("enabled", False) or not economy_settings.get("vote_enabled", False):
        return

    bot.add_cog(VoteRewards(bot))