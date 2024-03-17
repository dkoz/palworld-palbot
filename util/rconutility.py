import asyncio
import base64
from gamercon_async import GameRCON, GameRCONBase64, ClientError
import time

class RconUtility:
    def __init__(self, servers, timeout=120, encoding_info_ttl=600):
        self.servers = servers
        self.timeout = timeout
        self.memory_encoding = {}
        self.encoding_info_ttl = encoding_info_ttl

    async def check_encoding(self, server_name):
        current_time = time.time()
        encoding_info = self.memory_encoding.get(server_name)
        
        if encoding_info and (current_time - encoding_info['timestamp'] < self.encoding_info_ttl):
            return encoding_info['needs_base64']

        server = self.servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found.")

        try:
            async with GameRCON(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"]) as rcon:
                response = await asyncio.wait_for(rcon.send("Info"), timeout=self.timeout)
                needs_base64 = self.base64_encoded(response)
        except ClientError as e:
            print(f"Error connecting to server {server_name}: {e}")
            needs_base64 = False

        self.memory_encoding[server_name] = {'needs_base64': needs_base64, 'timestamp': current_time}
        return needs_base64

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

        try:
            needs_base64 = await self.check_encoding(server_name)
            ProtocolClass = GameRCONBase64 if needs_base64 else GameRCON

            async with ProtocolClass(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"]) as rcon:
                response = await asyncio.wait_for(rcon.send(command), timeout=self.timeout)
                if needs_base64 and self.base64_encoded(response):
                    response = base64.b64decode(response).decode('utf-8')
                return response
        except ClientError as e:
            return f"Failed to execute command on server {server_name}: {e}"
        except asyncio.TimeoutError as e:
            return f"Command execution on server {server_name} timed out."
