import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
import datetime
import pytz
from utils import steam_protocol

class Steam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="steam", description="Search up a steam profile by URL, SteamID, or custom name.")
    async def steam(
        self,
        interaction: Interaction,
        identifier: str = SlashOption(description="The full URL to the Steam profile, SteamID64, or custom name"),
    ):
        await interaction.response.defer()

        try:
            if identifier.isdigit() and len(identifier) == 17:
                steamid64 = identifier
            else:
                steamid64 = steam_protocol.extract_steamid64(identifier)
                if not steamid64:
                    vanity_url = steam_protocol.extract_vanity_url(identifier)
                    if vanity_url:
                        steamid64 = await steam_protocol.resolve_vanity_url(vanity_url)
                        if not steamid64:
                            await interaction.followup.send(
                                "Could not resolve Steam profile URL or custom name."
                            )
                            return
                    else:
                        steamid64 = await steam_protocol.resolve_vanity_url(identifier)
                        if not steamid64:
                            await interaction.followup.send("Invalid Steam profile URL, SteamID, or custom name.")
                            return

            summary_data, bans_data = await steam_protocol.fetch_steam_profile(
                steamid64
            )
        except steam_protocol.InvalidSteamAPIKeyException:
            await interaction.followup.send(
                "Error: Invalid Steam API Key. Please configure a valid API key."
            )
            return

        await self.display_steam_profile(interaction, summary_data, bans_data)

    async def display_steam_profile(self, interaction, summary_data, bans_data):
        if summary_data and "response" in summary_data and "players" in summary_data["response"] and len(summary_data["response"]["players"]) > 0:
            player = summary_data["response"]["players"][0]
            ban_info = bans_data["players"][0] if "players" in bans_data else None
            
            if 'timecreated' in player:
                account_creation_date = datetime.datetime.utcfromtimestamp(player['timecreated'])
                account_age = (datetime.datetime.utcnow() - account_creation_date).days // 365
            else:
                account_creation_date = None
                account_age = "Unknown"

            embed = Embed(
                title=player['personaname'],
                url=f"https://steamcommunity.com/profiles/{player['steamid']}",
                color=nextcord.Color.blue()
            )
            embed.set_thumbnail(url=player['avatarfull'])
            embed.add_field(name="Profile Info", value=f"**Name:** {player.get('realname', 'Unknown')}\n**Country:** {player.get('loccountrycode', 'Unknown')}\n**Account Age:** {account_age} years", inline=True)
            embed.add_field(name="SteamID", value=f"**SteamID64:** ```{player['steamid']}```", inline=True)
            
            if ban_info is not None:
                ban_info_str = f"**VAC Banned:** {ban_info['VACBanned']}\n"
                ban_info_str += f"**Bans:** {ban_info['NumberOfVACBans']} (Last: {ban_info['DaysSinceLastBan']} days ago)\n"
                ban_info_str += f"**Trade Banned:** {ban_info['EconomyBan']}"
                embed.add_field(name="Ban Info", value=ban_info_str, inline=True)

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Profile not found.")

def setup(bot):
    bot.add_cog(Steam(bot))
