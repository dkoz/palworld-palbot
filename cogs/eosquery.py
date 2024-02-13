from nextcord.ext import commands
import nextcord
from util.eos import PalworldProtocol
import util.constants as constants

class EOSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.palworld_protocol = PalworldProtocol(
            client_id='xyza78916PZ5DF0fAahu4tnrKKyFpqRE',
            client_secret='j0NapLEPm3R3EOrlQiM8cRLKq3Rt02ZVVwT0SkZstSg',
            deployment_id='0a18471f93d448e2a1f60e47e03d3413',
            epic_api='https://api.epicgames.dev'
        )

    # This command is still a work in progress.
    @nextcord.slash_command(name="query", description="Query EOS for your server's status. (Experimental)")
    async def queryserver(self, interaction: nextcord.Interaction, server_ip: str):
        access_token = await self.palworld_protocol.get_access_token()
        server_info_list = await self.palworld_protocol.query_server_info(access_token, server_ip)
        if not server_info_list:
            await interaction.response.send_message(f"No server found with IP: {server_ip}", ephemeral=True)
            return

        if server_info_list:
            server_info = server_info_list[0]
            embed = self.create_server_info_embed(server_info)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Multiple servers found, showing the first one.", ephemeral=True)
            server_info = server_info_list[0]
            embed = self.create_server_info_embed(server_info)
            await interaction.followup.send(embed=embed)

    def create_server_info_embed(self, server_info):
        embed = nextcord.Embed(title=f"{server_info['serverName']}", description=server_info['description'],color=nextcord.Color.green())
        embed.add_field(name="Map Name", value=server_info['mapName'], inline=True)
        embed.add_field(name="Players Online", value=f"{server_info['players']}/{server_info['maxPublicPlayers']}", inline=True)
        embed.add_field(name="Days Running", value=str(server_info['daysRunning']), inline=True)
        embed.add_field(name="Version", value=server_info['serverVersion'], inline=True)
        embed.add_field(name="Connection", value=f"```{server_info['serverIP']}:{str(server_info['serverPort'])}```", inline=False)
        embed.set_footer(text=constants.FOOTER_TEXT, icon_url=constants.FOOTER_IMAGE)
        return embed

def setup(bot):
    bot.add_cog(EOSCog(bot))
