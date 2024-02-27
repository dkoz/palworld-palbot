import os
import json
from nextcord.ext import commands
import nextcord
from util.eos import PalworldProtocol
import util.constants as constants
import datetime

class EOSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.palworld_protocol = PalworldProtocol(
            client_id='xyza78916PZ5DF0fAahu4tnrKKyFpqRE',
            client_secret='j0NapLEPm3R3EOrlQiM8cRLKq3Rt02ZVVwT0SkZstSg',
            deployment_id='0a18471f93d448e2a1f60e47e03d3413',
            epic_api='https://api.epicgames.dev'
        )

    def load_config(self):
        config_path = os.path.join('data', 'config.json')
        with open(config_path) as config_file:
            config = json.load(config_file)
            self.servers = config["PALWORLD_SERVERS"]

    # This command is still a work in progress.
    @nextcord.slash_command(name="server", description="Query EOS for your server's status. (Currently Broken)")
    async def queryserver(self, interaction: nextcord.Interaction, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        await interaction.response.defer()

        server = self.servers.get(server)
        if not server:
            await interaction.followup.send(f"No server found with name: {server}", ephemeral=True)
            return

        server_ip = server["RCON_HOST"]
        server_port = server["SERVER_PORT"]
        access_token = await self.palworld_protocol.get_access_token()
        servers_info = await self.palworld_protocol.query_server_info(access_token, server_ip)
        
        filtered_servers = [s for s in servers_info if str(s['serverPort']) == str(server_port)]
        
        if not filtered_servers:
            await interaction.followup.send(f"No server found with IP: {server_ip} and port: {server_port}", ephemeral=True)
            return

        server_info = filtered_servers[0]
        embed = self.create_server_info_embed(server_info)
        await interaction.followup.send(embed=embed)

    @queryserver.on_autocomplete("server")
    async def server_autocomplete(self, interaction: nextcord.Interaction, current: str):
        choices = [server for server in self.servers if current.lower() in server.lower()]
        await interaction.response.send_autocomplete(choices)

    def create_server_info_embed(self, server_info):
        embed = nextcord.Embed(title=f"{server_info['serverName']}", description=server_info['description'], url=constants.TITLE_URL, color=nextcord.Color.blue())
        embed.add_field(name="Map Name", value=server_info['mapName'], inline=True)
        embed.add_field(name="Players Online", value=f"{server_info['players']}/{server_info['maxPublicPlayers']}", inline=True)
        embed.add_field(name="Days Running", value=str(server_info['daysRunning']), inline=True)
        embed.add_field(name="Version", value=server_info['serverVersion'], inline=True)
        embed.add_field(name="Password", value="Yes" if server_info['serverPassword'] else "No", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Connection", value=f"```{server_info['serverIP']}:{str(server_info['serverPort'])}```", inline=False)
        embed.set_footer(text=f"{constants.FOOTER_TEXT} • {datetime.datetime.now().strftime('%m-%d at %I:%M %p')}", icon_url=constants.FOOTER_IMAGE)
        return embed

def setup(bot):
    cog = EOSCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, 'all_slash_commands'):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend([
        cog.queryserver
    ])