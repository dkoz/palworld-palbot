import nextcord
from nextcord.ext import commands
from util.economy_system import add_points, add_invite
import json

class InviteTrackerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}
        self.load_config()
        bot.loop.create_task(self.setup_invites())

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            self.economy_config = json.load(config_file)
        self.economy_config = self.economy_config.get("ECONOMY_SETTINGS", {})
        self.invite_payment = self.economy_config.get("invite_reward", 10)

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
        self.invites[invite.guild.id][invite.code] = invite

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if invite.code in self.invites[invite.guild.id]:
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
    config_path = "config.json"
    with open(config_path) as config_file:
        config = json.load(config_file)

    economy_settings = config.get("ECONOMY_SETTINGS", {})
    if not economy_settings.get("enabled", False):
        return

    bot.add_cog(InviteTrackerCog(bot))
