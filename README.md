# Palbot - Your Palworld Companion
![Discord](https://img.shields.io/discord/1009881575187566632?style=flat-square&label=support)
 
 Welcome to Palbot, your ultimate companion for Palworld server management! Palbot is a versatile bot designed to enhance your Palworld experience with a range of powerful features.

 Welcome to the official Palbot repository for Palworld Discord Bot. Invite the verified [Palbot](https://discord.com/api/oauth2/authorize?client_id=1197954327642378352&permissions=8&scope=bot%20applications.commands) to your server today!

 You can find Linux and Windows installation guides on our [wiki](https://github.com/dkoz/palworld-bot/wiki).

## Features:
- **RCON Integration:** Seamlessly control your server using RCON commands.
- **Server Query:** Retrieve real-time information about your server's status, including player count and connection info.
- **Whitelist Management:** Easily manage your server's whitelist and create a database of players SteamID, PlayUID, and other information for secure access control.
- **Player Logging:** Keep track of player activity by logging join and leave events on your server.
- **Scheduled Restarts:** Automate server reboots at set intervals for updates and maintenance, enhancing stability while minimizing disruption to players. This requires implementing a watchdog mechanism to detect when the server stops and automatically restarts it, similar to capabilities found in game panels or batch scripts.

## Config Example
```
{
    "PALWORLD_SERVERS": {
        "Palworld Server 1": {
            "RCON_HOST": "127.0.0.1",
            "RCON_PORT": 25575,
            "RCON_PASS": "rcon_password"
        },
        "Palworld Other Server": {
            "RCON_HOST": "127.0.0.1",
            "RCON_PORT": 25575,
            "RCON_PASS": "rcon_password",
            "SERVER_PORT": 8211,
            "QUERY_CHANNEL": CHANNEL_ID,
            "CONNECTION_CHANNEL": CHANNEL_ID
        }
    }
}
```
Configuration Explained:
- RCON_HOST: This is the IP address to your server.
- RCON_PORT: This is the port to your rcon, not the connection port.
- RCON_PASS: This is the password to access your rcon.
- SERVER_PORT: This is the connection port to your server.
- QUERY_CHANNEL: Channel ID where the query status will be posted.
- CONNECTION_CHANNEL: Channel ID where the player join logs will be posted.