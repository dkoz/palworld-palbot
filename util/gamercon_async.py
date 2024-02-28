# This is directly from my gamercon repo.
# You can find my repo here: https://github.com/dkoz/gamercon-async
import asyncio
import struct

class ClientError(Exception):
    pass

class InvalidPassword(Exception):
    pass

class TimeoutError(Exception):
    pass

class GameRCON:
    def __init__(self, host, port, password, timeout=15):
        self.host = host
        self.port = int(port)
        self.password = password
        self.timeout = timeout
        self._auth = None
        self._reader = None
        self._writer = None

    async def __aenter__(self):
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Timeout while connecting to {self.host}:{self.port}")
        except Exception as e:
            raise ClientError(f"Error connecting to {self.host}:{self.port} - {e}")
        
        await self._authenticate()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def _authenticate(self):
        if not self._auth:
            try:
                await self._send(3, self.password)
            except Exception as e:
                raise InvalidPassword(f"Authentication failed - {e}")
            self._auth = True

    async def _read_data(self, leng):
        try:
            data = await asyncio.wait_for(
                self._reader.read(leng), 
                timeout=self.timeout
            )
            return data
        except asyncio.TimeoutError:
            raise TimeoutError("Timeout while reading data from server")

    async def _send(self, typen, message):
        if not self._writer:
            raise ClientError('Not connected.')

        encoded_message = message.encode('utf-8')
        out = struct.pack('<li', 0, typen) + encoded_message + b'\x00\x00'
        out_len = struct.pack('<i', len(out))
        self._writer.write(out_len + out)
        await self._writer.drain()

        in_len = struct.unpack('<i', await self._read_data(4))[0]
        in_payload = await self._read_data(in_len)

        in_id, in_type = struct.unpack('<ii', in_payload[:8])
        in_data, in_padd = in_payload[8:-2], in_payload[-2:]

        if in_padd != b'\x00\x00':
            raise ClientError('Incorrect padding.')
        if in_id == -1:
            raise InvalidPassword('Incorrect password.')

        try:
            data = in_data.decode('utf-8')
        except UnicodeDecodeError:
            data = "Command executed successfully, but response was not decodable."
            
        return data

    async def send(self, cmd):
        if not self._auth:
            raise ClientError("Client not authenticated.")

        result = await self._send(2, cmd)
        return result

async def main():
    async with GameRCON("127.0.0.1", 25575, "pass", timeout=10) as rcon:
        response = await rcon.send("Info")
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
