import nextcord
from nextcord.ext import commands
from utils.database import add_points, add_invite, get_economy_setting

class InviteTrackerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}
        self.bot.loop.create_task(self.load_config())
        bot.loop.create_task(self.setup_invites())

    async def load_config(self):
        self.invite_payment = int(await get_economy_setting("invite_reward") or 10)

    async def setup_invites(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            self.invites[guild.id] = await self.fetch_invites(guild)

    async def fetch_invites(self, guild):
        try:
            invites = await guild.invites()
            return {invite.code: invite for invite in invites}
        except Exception:
            return {}

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.invites[guild.id] = await self.fetch_invites(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if invite.guild.id in self.invites:
            self.invites[invite.guild.id][invite.code] = invite

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if invite.guild.id in self.invites and invite.code in self.invites[invite.guild.id]:
            del self.invites[invite.guild.id][invite.code]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        new_invites = await self.fetch_invites(guild)
        for code, invite in new_invites.items():
            if (
                code not in self.invites[guild.id]
                or invite.uses > self.invites[guild.id][code].uses
            ):
                print(
                    f"Member {member.display_name} joined using invite from {invite.inviter.display_name}."
                )
                await add_points(
                    str(invite.inviter.id),
                    invite.inviter.display_name,
                    self.invite_payment,
                )
                await add_invite(str(invite.inviter.id), invite.inviter.display_name)
                break
        self.invites[guild.id] = new_invites

def setup(bot):
    bot.add_cog(InviteTrackerCog(bot))
