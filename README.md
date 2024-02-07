# Palbot Palword Bot
![Discord](https://img.shields.io/discord/1009881575187566632?style=flat-square&label=support)
 
 The official Palbot repo for Palworld Discord Bot. Invite the verified [Palbot](https://discord.com/api/oauth2/authorize?client_id=1197954327642378352&permissions=8&scope=bot%20applications.commands).

 You can find Linux and Windows installation guides on our [wiki](https://github.com/dkoz/palworld-bot/wiki).

## Features
- RCON Protocol: Control your server remotely from discord with the built in rcon commands.
- Query Protocol: Query your server for information like online status, player count, and online players.
- Whitelist Protocol: The bot will constantly monitor your server for users not added to the list. They will be kicked from the server if not added.
- Connection Logs: Log players who connect to your server.

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

# Licensing
 I'm not assigning a license to this bot yet until I finished the core code base.