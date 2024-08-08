import asyncio
from nextcord.ext import commands
import nextcord
from utils.database import get_server_details, server_autocomplete
from utils.rconutility import RconUtility

class StatusTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rcon_util = RconUtility()
        self.servers = []
        self.bot.loop.create_task(self.load_servers())
        self.bot.loop.create_task(self.update_status())

    async def load_servers(self):
        self.servers = await server_autocomplete()

    async def update_status(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                total_players = await self.get_total_players()
                status_message = f"{total_players} players"
                await self.bot.change_presence(
                    activity=nextcord.Activity(
                        type=nextcord.ActivityType.watching, name=status_message
                    )
                )
            except ConnectionResetError:
                print("Connection was reset. Retrying in 30 seconds...")
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error updating status: {e}")
            await asyncio.sleep(60)

    async def get_total_players(self):
        total_players = 0
        for server_name in self.servers:
            try:
                server_info = await get_server_details(server_name)
                if server_info and len(server_info) == 3:
                    server_dict = {
                        'name': server_name,
                        'host': server_info[0],
                        'port': server_info[1],
                        'password': server_info[2]
                    }
                    players_output = await self.rcon_util.rcon_command(
                        server_dict, "ShowPlayers"
                    )
                    players = self.parse_players(players_output)
                    total_players += len(players)
            except Exception as e:
                print(f"Failed to get player count for server '{server_name}': {e}")
        return total_players

    def parse_players(self, players_output):
        players = []
        lines = players_output.split("\n")
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 3:
                players.append(parts[0])
        return players

def setup(bot):
    bot.add_cog(StatusTracker(bot))
