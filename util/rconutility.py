import asyncio
import base64
from gamercon_async import GameRCON, GameRCONBase64

class RconUtility:
    def __init__(self, servers, timeout=30):
        self.servers = servers
        self.timeout = timeout
        self.memory_encoding = {}

    async def check_encoding(self, server_name):
        if server_name in self.memory_encoding:
            return self.memory_encoding[server_name]

        server = self.servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found.")

        async with GameRCON(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"]) as rcon:
            response = await asyncio.wait_for(rcon.send("Info"), timeout=self.timeout)
            self.memory_encoding[server_name] = self.base64_encoded(response)
            return self.memory_encoding[server_name]

    def base64_encoded(self, s):
        try:
            if not s:
                return False
            return base64.b64encode(base64.b64decode(s)).decode('utf-8') == s
        except Exception:
            return False

    async def rcon_command(self, server_name, command):
        server = self.servers.get(server_name)
        if not server:
            return "Server not found."

        needs_base64 = await self.check_encoding(server_name)
        ProtocolClass = GameRCONBase64 if needs_base64 else GameRCON

        async with ProtocolClass(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"]) as rcon:
            response = await asyncio.wait_for(rcon.send(command), timeout=self.timeout)
            if needs_base64 and self.base64_encoded(response):
                response = base64.b64decode(response).decode('utf-8')
            return response
