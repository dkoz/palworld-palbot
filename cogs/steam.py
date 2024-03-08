import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
import datetime
from util import steam_protocol

class Steam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="steam", description="Search up a steam profile URL.")
    async def steam(self, interaction: Interaction, profile_url: str = SlashOption(description="The full URL to the Steam profile")):
        await interaction.response.defer()

        try:
            steamid64 = steam_protocol.extract_steamid64(profile_url)
            if not steamid64:
                vanity_url = steam_protocol.extract_vanity_url(profile_url)
                if vanity_url:
                    steamid64 = await steam_protocol.resolve_vanity_url(vanity_url)
                    if not steamid64:
                        await interaction.followup.send("Could not resolve Steam profile URL.")
                        return
                else:
                    await interaction.followup.send("Invalid Steam profile URL.")
                    return

            summary_data, bans_data = await steam_protocol.fetch_steam_profile(steamid64)
        except steam_protocol.InvalidSteamAPIKeyException:
            await interaction.followup.send("Error: Invalid Steam API Key. Please configure a valid API key.")
            return

        await self.display_steam_profile(interaction, summary_data, bans_data)

    async def display_steam_profile(self, interaction, summary_data, bans_data):
        player = summary_data['response']['players'][0] if summary_data['response']['players'] else None
        ban_info = bans_data['players'][0] if bans_data['players'] else None
        
        if player and ban_info:
            embed = Embed(title=player.get('personaname'), url=f"https://steamcommunity.com/profiles/{player.get('steamid')}", color=0x1b2838)
            embed.set_thumbnail(url=player.get('avatarfull'))

            if player.get('realname'):
                embed.add_field(name="Real Name", value=player.get('realname'), inline=False)
            
            if player.get('gameextrainfo'):
                embed.add_field(name="Playing", value=player.get('gameextrainfo'), inline=False)

            embed.add_field(name="SteamID64", value=f"```{player.get('steamid')}```", inline=False)
            
            creation_date = datetime.datetime.utcfromtimestamp(player.get('timecreated')).strftime('%Y-%m-%d') if player.get('timecreated') else 'Not available'
            embed.add_field(name="Account Creation", value=creation_date, inline=False)
            
            if player.get('loccountrycode'):
                embed.add_field(name="Country", value=player.get('loccountrycode'), inline=False)
            
            vac_banned = "Yes" if ban_info['VACBanned'] else "No"
            embed.add_field(name="VAC Banned", value=vac_banned, inline=False)

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Profile not found.")

def setup(bot):
    bot.add_cog(Steam(bot))
