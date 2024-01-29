import nextcord
from nextcord.ext import commands
import config
import os

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix=config.bot_prefix, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'{bot.user} is ready! Created by koz')
    activity = nextcord.Activity(type=nextcord.ActivityType.playing, name=config.bot_activity)
    await bot.change_presence(activity=activity)

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

if __name__ == '__main__':
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
    bot.run(config.bot_token)