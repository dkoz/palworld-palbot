# EOS Protocol for Palworld Bot
# Please give credit if you use this in your project.
import aiohttp
import base64
import asyncio

class PalworldProtocol:
    def __init__(self, client_id, client_secret, deployment_id, epic_api):
        self.client_id = client_id
        self.client_secret = client_secret
        self.deployment_id = deployment_id
        self.epic_api = epic_api
        self.auth_by_external_token = True

    async def get_access_token(self):
        if self.auth_by_external_token:
            return await self.get_external_access_token()
        else:
            return await self.get_client_oauth_token()

    async def get_client_oauth_token(self):
        url = f'{self.epic_api}/auth/v1/oauth/token'
        auth = base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()
        headers = {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        body = 'grant_type=client_credentials&deployment_id={}'.format(self.deployment_id)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('access_token')
                response.raise_for_status()

    async def get_device_id_token(self):
        url = f'{self.epic_api}/auth/v1/accounts/deviceid'
        auth = base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()
        headers = {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        body = 'deviceModel=PC'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('access_token')
                response.raise_for_status()

    async def get_external_access_token(self):
        device_id_token = await self.get_device_id_token()
        if not device_id_token:
            return None
        url = f'{self.epic_api}/auth/v1/oauth/token'
        auth = base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()
        headers = {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        body = {
            'grant_type': 'external_auth',
            'external_auth_type': 'deviceid_access_token',
            'external_auth_token': device_id_token,
            'nonce': 'unique_nonce_value',
            'deployment_id': self.deployment_id,
            'display_name': 'UserDisplayName'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('access_token')
                response.raise_for_status()

    async def query_server_info(self, access_token, ip_address):
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        data = {
            "criteria": [
                {
                    "key": "attributes.ADDRESS_s",
                    "op": "EQUAL",
                    "value": ip_address
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.epic_api}/matchmaking/v1/{self.deployment_id}/filter', headers=headers, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.extract_server_data(data)
                response.raise_for_status()

    def extract_server_data(self, data):
        servers = []
        for session in data.get('sessions', []):
            server_info = {
                'deployment': session.get('deployment'),
                'id': session.get('id'),
                'maxPublicPlayers': session.get('settings', {}).get('maxPublicPlayers'),
                'totalPlayers': session.get('totalPlayers'),
                'serverName': session.get('attributes', {}).get('NAME_s', 'Unknown'),
                'serverIP': session.get('attributes', {}).get('ADDRESS_s', 'Unknown'),
                'serverPort': session.get('attributes', {}).get('GAMESERVER_PORT_l', 'Unknown'),
                'serverPassword': session.get('attributes', {}).get('ISPASSWORD_b', 'Unknown'),
                'mapName': session.get('attributes', {}).get('MAPNAME_s', 'Unknown'),
                'daysRunning': session.get('attributes', {}).get('DAYS_l', 'Unknown'),
                'serverVersion': session.get('attributes', {}).get('VERSION_s', 'Unknown'),
                'description': session.get('attributes', {}).get('DESCRIPTION_s', 'No description provided.'),
                'players': session.get('attributes', {}).get('PLAYERS_l', 0),
            }
            servers.append(server_info)
        return servers
