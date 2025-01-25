import asyncio
import base64
from gamercon_async import (
    GameRCON,
    GameRCONBase64,
    ClientError,
    TimeoutError,
    InvalidPassword,
)
import time
import logging

class RconUtility:
    def __init__(self, timeout=30, encoding_info_ttl=50):
        self.timeout = timeout
        self.memory_encoding = {}
        self.encoding_info_ttl = encoding_info_ttl

    async def check_encoding(self, server_info):
        current_time = time.time()
        encoding_info = self.memory_encoding.get(server_info["name"])

        if encoding_info and (
            current_time - encoding_info["timestamp"] < self.encoding_info_ttl
        ):
            return encoding_info["needs_base64"]

        try:
            async with GameRCON(
                server_info["host"],
                server_info["port"],
                server_info["password"],
                self.timeout,
            ) as rcon:
                response = await rcon.send("Info")
                needs_base64 = self.base64_encoded(response)
        except (ClientError, TimeoutError, InvalidPassword) as e:
            logging.error(f"Error connecting to server {server_info['name']}: {e}")
            needs_base64 = False

        self.memory_encoding[server_info["name"]] = {
            "needs_base64": needs_base64,
            "timestamp": current_time,
        }
        return needs_base64

    def base64_encoded(self, s):
        try:
            if not s:
                return False
            return base64.b64encode(base64.b64decode(s)).decode("utf-8") == s
        except Exception:
            return False

    async def rcon_command(self, server_info, command):
        try:
            needs_base64 = await self.check_encoding(server_info)
            ProtocolClass = GameRCONBase64 if needs_base64 else GameRCON

            async with ProtocolClass(
                server_info["host"],
                server_info["port"],
                server_info["password"],
                self.timeout,
            ) as rcon:
                response = await rcon.send(command)
                if needs_base64 and self.base64_encoded(response):
                    response = base64.b64decode(response).decode("utf-8")
                return response
        except (ClientError, TimeoutError, InvalidPassword) as e:
            return f"Failed to execute command on server {server_info['name']}: {e}"
        except asyncio.TimeoutError:
            return f"Command execution on server {server_info['name']} timed out."
        except ConnectionResetError as e:
            return f"Connection reset by peer: {e}"
