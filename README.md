# Palbot Palword Bot
![Discord](https://img.shields.io/discord/1009881575187566632?style=flat-square&label=support)
 
 The official Palbot repo for Palworld Discord Bot. Invite the verified [Palbot](https://discord.com/api/oauth2/authorize?client_id=1197954327642378352&permissions=8&scope=bot%20applications.commands).

## Features
- RCON Protocol: Control your server remotely from discord with the built in rcon commands.
- Query Protocol: Query your server for information like online status, player count, and online players.
- Whitelist Protocol: The bot will constantly monitor your server for users not added to the list. They will be kicked from the server if not added.

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
            "QUERY_CHANNEL": 12345678910
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

## Setup on Linux
1. Create a new user and switch to it.
```
sudo adduser palbot
su - palbot
```
2. Clone the Arkon bot repository with the following commands
```
git clone https://github.com/dkoz/palworld-bot
cd palworld-bot
```
3. Now you need to create a virtual env and install the requirements.
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
4. Configure the environment variables.
```
cp .env.example .env
nano .env
```
5. Configure the server information.
```
cp data/config.json.example data/config.json
nano data/config.json
```
6. Now run the bot.
```
python main.py
```

# Licensing
 I'm not assigning a license to this bot yet until I finished the core code base.