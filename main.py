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

# Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('This command does not exist.')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing a required argument.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown. Please try again later.")
    else:
        await ctx.send(f'An error occured: {error}')

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

if __name__ == '__main__':
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
    bot.run(config.bot_token)