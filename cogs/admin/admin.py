import nextcord
from nextcord.ext import commands
from nextcord.ext.commands import has_permissions
import datetime

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="admin", alias="a", description="Show list of admin commands.", invoke_without_command=True)
    @has_permissions(administrator=True)
    async def admin(self, ctx):
        prefix = ctx.prefix

        embed = nextcord.Embed(
            title="Administrative Commands",
            description=f"`{prefix}admin kick` - Kick a user\n"
                        f"`{prefix}admin ban` - Ban a user\n"
                        f"`{prefix}admin unban` - Unban a user\n"
                        f"`{prefix}admin purge` - Purge messages\n"
                        f"`{prefix}admin purgeuser` - Purge messages from a user\n"
                        f"`{prefix}admin mute` - Mute a user\n"
                        f"`{prefix}admin unmute` - Unmute a user\n"
                        f"`{prefix}admin timeout` - Timeout a user",
            color=nextcord.Color.blue()
        )
        await ctx.send(embed=embed)

    @admin.command(name="kick")
    @has_permissions(kick_members=True)
    async def kick(self, ctx, member: nextcord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member} has been kicked.")

    @admin.command(name="ban")
    @has_permissions(ban_members=True)
    async def ban(self, ctx, member: nextcord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f"{member} has been banned.")

    @admin.command(name="unban")
    @has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split("#")
        
        for ban_entry in banned_users:
            user = ban_entry.user
            
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f"{user.mention} has been unbanned.")
                return
        
        await ctx.send(f"{member} was not found.", ephemeral=True)

    @admin.command(name="purge")
    @has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"{amount} messages have been deleted.", ephemeral=True)

    @admin.command(name="purgeuser")
    @has_permissions(manage_messages=True)
    async def purgeuser(self, ctx, member: nextcord.Member, amount: int):
        def is_member(message):
            return message.author == member

        await ctx.channel.purge(limit=amount + 1, check=is_member)
        await ctx.send(f"{amount} messages from {member} have been deleted.", ephemeral=True)
        
    @admin.command(name="mute")
    @has_permissions(mute_members=True)
    async def mute(self, ctx, member: nextcord.Member):
        await member.edit(mute=True)
        await ctx.send(f"{member.mention} has been muted.", ephemeral=True)

    @admin.command(name="unmute")
    @has_permissions(mute_members=True)
    async def unmute(self, ctx, member: nextcord.Member):
        await member.edit(mute=False)
        await ctx.send(f"{member.mention} has been unmuted.", ephemeral=True)

    @admin.command(name="timeout")
    @has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: nextcord.Member, duration: int, *, reason=None):
        if duration <= 0:
            await ctx.send("Please provide a valid duration in minutes.")
            return

        timeout_duration = datetime.timedelta(minutes=duration)
        await member.timeout(timeout_duration, reason=reason)
        await ctx.send(f"{member.mention} has been timed out for {duration} minutes. Reason: {reason or 'No reason provided.'}")

def setup(bot):
    bot.add_cog(AdminCog(bot))