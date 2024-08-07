import aiohttp
import re
import asyncio
from utils.settings import steam_api_key

class InvalidSteamAPIKeyException(Exception):
    pass

async def resolve_vanity_url(vanity_url):
    url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={steam_api_key}&vanityurl={vanity_url}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 403:
                raise InvalidSteamAPIKeyException("Invalid Steam API Key.")
            data = await response.json()
            if data["response"]["success"] == 1:
                return data["response"]["steamid"]
            return None

def extract_steamid64(url):
    match = re.search(r"steamcommunity\.com/profiles/(\d+)", url)
    return match.group(1) if match else None

def extract_vanity_url(url):
    match = re.search(r"steamcommunity\.com/id/([^/]+)", url)
    return match.group(1) if match else None

async def fetch_steam_profile(steamid64):
    summary_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={steam_api_key}&steamids={steamid64}"
    bans_url = f"https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={steam_api_key}&steamids={steamid64}"

    async with aiohttp.ClientSession() as session:
        summary_response, bans_response = await asyncio.gather(
            session.get(summary_url), session.get(bans_url)
        )
        if summary_response.status == 403 or bans_response.status == 403:
            raise InvalidSteamAPIKeyException("Invalid Steam API Key.")
        summary_data = await summary_response.json()
        bans_data = await bans_response.json()
        return summary_data, bans_data
