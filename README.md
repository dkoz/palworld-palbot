# Palbot Palword Bot
![Discord](https://img.shields.io/discord/1009881575187566632?style=flat-square&label=support)
 
 The official Palbot repo for Palworld Discord Bot. Invite the verified [Palbot](https://discord.com/api/oauth2/authorize?client_id=1197954327642378352&permissions=8&scope=bot%20applications.commands).

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