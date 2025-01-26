import json
import os
import nextcord
from nextcord.ext import commands
from src.utils.rconutility import RconUtility
import asyncio
from src.utils.database import get_server_details, server_autocomplete
from src.utils.translations import t
from src.utils.errorhandling import restrict_command

class PalguardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_servers())
        self.rcon_util = RconUtility()
        self.servers = []
        self.load_pals()
        self.load_items()
        self.load_eggs()

    async def load_servers(self):
        self.servers = await server_autocomplete()

    def load_pals(self):
        pals_path = os.path.join("src", "gamedata", "pals.json")
        with open(pals_path, "r", encoding="utf-8") as pals_file:
            self.pals = json.load(pals_file)["creatures"]

    def load_items(self):
        items_path = os.path.join("src", "gamedata", "items.json")
        with open(items_path, "r", encoding="utf-8") as items_file:
            self.items = json.load(items_file)["items"]

    def load_eggs(self):
        eggs_path = os.path.join("src", "gamedata", "eggs.json")
        with open(eggs_path, "r", encoding="utf-8") as eggs_file:
            self.eggs = json.load(eggs_file)["eggs"]

    async def autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        if interaction.guild is None:
            return []
        server_names = await server_autocomplete()
        choices = [server for server in server_names if current.lower() in server.lower()][:25]
        await interaction.response.send_autocomplete(choices)

    async def autocomplete_palid(self, interaction: nextcord.Interaction, current: str):
        choices = [
            pal["name"] for pal in self.pals if current.lower() in pal["name"].lower()
        ][:25]
        await interaction.response.send_autocomplete(choices)

    async def autocomplete_itemid(
        self, interaction: nextcord.Interaction, current: str
    ):
        choices = [
            item["name"]
            for item in self.items
            if current.lower() in item["name"].lower()
        ][:25]
        await interaction.response.send_autocomplete(choices)

    async def autocomplete_eggid(self, interaction: nextcord.Interaction, current: str):
        choices = [
            egg["name"] for egg in self.eggs if current.lower() in egg["name"].lower()
        ][:25]
        await interaction.response.send_autocomplete(choices)

    async def get_server_info(self, server_name: str):
        details = await get_server_details(server_name)
        if details:
            return {
                "name": server_name,
                "host": details[0],
                "port": details[1],
                "password": details[2],
            }
        return None

    @nextcord.slash_command(default_member_permissions=nextcord.Permissions(administrator=True))
    async def palguard(self, _interaction: nextcord.Interaction):
        await self.load_servers()

    @palguard.subcommand(name="reload", description=t("PalguardCog", "reloadcfg.description"))
    @restrict_command()
    async def reloadcfg(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "reloadcfg.server_not_found").format(server=server), ephemeral=True
            )
            return
        response = await self.rcon_util.rcon_command(server_info, "reloadcfg")
        await interaction.followup.send(t("PalguardCog", "reloadcfg.response").format(response=response))

    @reloadcfg.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palguard.subcommand(description=t("PalguardCog", "givepal.description"))
    @restrict_command()
    async def givepal(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description=t("PalguardCog", "description.userid")),
        palid: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.palid"), autocomplete=True
        ),
        level: str = nextcord.SlashOption(description=t("PalguardCog", "description.level")),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "givepal.server_not_found").format(server=server), ephemeral=True
            )
            return
        pal_id = next((pal["id"] for pal in self.pals if pal["name"] == palid), None)
        if not pal_id:
            await interaction.followup.send(t("PalguardCog", "givepal.pal_not_found"), ephemeral=True)
            return
        response = await asyncio.create_task(
            self.rcon_util.rcon_command(
                server_info, f"givepal {steamid} {pal_id} {level}"
            )
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "givepal.title").format(server=server), color=nextcord.Color.blue()
        )
        embed.description = t("PalguardCog", "givepal.response").format(response=response, palid=palid, steamid=steamid)
        await interaction.followup.send(embed=embed)

    @givepal.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @givepal.on_autocomplete("palid")
    async def on_autocomplete_pals(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_palid(interaction, current)

    @palguard.subcommand(description=t("PalguardCog", "giveitem.description"))
    @restrict_command()
    async def giveitem(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description=t("PalguardCog", "description.userid")),
        itemid: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.itemid"), autocomplete=True
        ),
        amount: str = nextcord.SlashOption(description=t("PalguardCog", "description.amount")),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "giveitem.server_not_found").format(server=server), ephemeral=True
            )
            return
        item_id = next(
            (item["id"] for item in self.items if item["name"] == itemid), None
        )
        if not item_id:
            await interaction.followup.send(t("PalguardCog", "giveitem.item_not_found"), ephemeral=True)
            return
        response = await asyncio.create_task(
            self.rcon_util.rcon_command(
                server_info, f"give {steamid} {item_id} {amount}"
            )
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "giveitem.title").format(server=server), color=nextcord.Color.blue()
        )
        embed.description = t("PalguardCog", "giveitem.response").format(response=response, itemid=itemid, steamid=steamid)
        await interaction.followup.send(embed=embed)

    @giveitem.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @giveitem.on_autocomplete("itemid")
    async def on_autocomplete_items(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_itemid(interaction, current)

    @palguard.subcommand(description=t("PalguardCog", "delitem.description"))
    @restrict_command()
    async def delitem(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description=t("PalguardCog", "description.userid")),
        itemid: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.itemid"), autocomplete=True
        ),
        amount: str = nextcord.SlashOption(description=t("PalguardCog", "description.amount")),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "delitem.server_not_found").format(server=server), ephemeral=True
            )
            return
        item_id = next(
            (item["id"] for item in self.items if item["name"] == itemid), None
        )
        if not item_id:
            await interaction.followup.send(t("PalguardCog", "delitem.item_not_found"), ephemeral=True)
            return
        response = await asyncio.create_task(
            self.rcon_util.rcon_command(
                server_info, f"delitem {steamid} {item_id} {amount}"
            )
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "delitem.title").format(server=server), color=nextcord.Color.blue()
        )
        embed.description = t("PalguardCog", "delitem.response").format(response=response, itemid=itemid, amount=amount, steamid=steamid)
        await interaction.followup.send(embed=embed)

    @delitem.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @delitem.on_autocomplete("itemid")
    async def on_autocomplete_items(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_itemid(interaction, current)

    @palguard.subcommand(description=t("PalguardCog", "giveexp.description"))
    @restrict_command()
    async def giveexp(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description=t("PalguardCog", "description.userid")),
        amount: str = nextcord.SlashOption(description=t("PalguardCog", "description.amount")),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "giveexp.server_not_found").format(server=server), ephemeral=True
            )
            return
        response = await asyncio.create_task(
            self.rcon_util.rcon_command(server_info, f"give_exp {steamid} {amount}")
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "giveexp.title").format(server=server), color=nextcord.Color.blue()
        )
        embed.description = t("PalguardCog", "giveexp.response").format(response=response, amount=amount, steamid=steamid)
        await interaction.followup.send(embed=embed)

    @giveexp.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palguard.subcommand(description=t("PalguardCog", "giveegg.description"))
    @restrict_command()
    async def giveegg(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description=t("PalguardCog", "description.userid")),
        eggid: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.eggid"), autocomplete=True
        ),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "giveegg.server_not_found").format(server=server), ephemeral=True
            )
            return
        egg_id = next((egg["id"] for egg in self.eggs if egg["name"] == eggid), None)
        if not egg_id:
            await interaction.followup.send(t("PalguardCog", "giveegg.egg_not_found"), ephemeral=True)
            return
        response = await asyncio.create_task(
            self.rcon_util.rcon_command(server_info, f"giveegg {steamid} {egg_id}")
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "giveegg.title").format(server=server), color=nextcord.Color.blue()
        )
        embed.description = t("PalguardCog", "giveegg.response").format(response=response, eggid=eggid, steamid=steamid)
        await interaction.followup.send(embed=embed)

    @giveegg.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @giveegg.on_autocomplete("eggid")
    async def on_autocomplete_eggs(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_eggid(interaction, current)

    @palguard.subcommand(name="help", description=t("PalguardCog", "palguardhelp.description"))
    @restrict_command()
    async def palguardhelp(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "palguardhelp.server_not_found").format(server=server), ephemeral=True
            )
            return
        response = await self.rcon_util.rcon_command(server_info, "getrconcmds")
        await interaction.followup.send(f"{response}")

    @palguardhelp.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palguard.subcommand(description=t("PalguardCog", "giverelic.description"))
    @restrict_command()
    async def giverelic(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description=t("PalguardCog", "description.userid")),
        amount: str = nextcord.SlashOption(description=t("PalguardCog", "description.amount")),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "giverelic.server_not_found").format(server=server), ephemeral=True
            )
            return
        response = await asyncio.create_task(
            self.rcon_util.rcon_command(server_info, f"give_relic {steamid} {amount}")
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "giverelic.title").format(server=server), color=nextcord.Color.blurple()
        )
        embed.description = t("PalguardCog", "giverelic.response").format(response=response, amount=amount, steamid=steamid)
        await interaction.followup.send(embed=embed)

    @giverelic.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palguard.subcommand(description=t("PalguardCog", "deletepals.description"))
    @restrict_command()
    async def deletepals(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description=t("PalguardCog", "description.userid")),
        palfilter: str = nextcord.SlashOption(description=t("PalguardCog", "description.palfilter")),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "deletepals.server_not_found").format(server=server), ephemeral=True
            )
            return
        response = await self.rcon_util.rcon_command(server_info, f"deletepals {steamid} {palfilter}")
        embed = nextcord.Embed(
            title=t("PalguardCog", "deletepals.title").format(server=server),
            description=t("PalguardCog", "deletepals.response").format(response=response),
            color=nextcord.Color.blurple()
        )
        await interaction.followup.send(embed=embed)
        
    @deletepals.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palguard.subcommand(description=t("PalguardCog", "settime.description"))
    @restrict_command()
    async def settime(
        self,
        interaction: nextcord.Interaction,
        time: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.time"),
            choices={"Day": "day", "Night": "night"}
        ),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"),
            autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "settime.server_not_found").format(server=server), ephemeral=True
            )
            return
        response = await asyncio.create_task(
            self.rcon_util.rcon_command(server_info, f"settime {time}")
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "settime.title").format(server=server, time=time.capitalize()),
            color=nextcord.Color.green()
        )
        embed.description = t("PalguardCog", "settime.response").format(response=response, time=time)
        await interaction.followup.send(embed=embed)

    @settime.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palguard.subcommand(description=t("PalguardCog", "resetoilrig.description"))
    @restrict_command()
    async def resetoilrig(
        self,
        interaction: nextcord.Interaction,
        level: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.level"),
            choices={"Level 30": "lv30", "Level 55": "lv55", "Level 60": "lv60", "All": "all"}
        ),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"),
            autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "resetoilrig.server_not_found").format(server=server), ephemeral=True
            )
            return
        response = await asyncio.create_task(
            self.rcon_util.rcon_command(server_info, f"resetoilrig {level}")
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "resetoilrig.title").format(server=server, level=level.upper()),
            color=nextcord.Color.orange()
        )
        embed.description = t("PalguardCog", "resetoilrig.response").format(response=response, level=level)
        await interaction.followup.send(embed=embed)

    @resetoilrig.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    # Palguard Whitelist Functions
    @nextcord.slash_command(
        name="whitelist",
        description=t("PalguardCog", "whitelist.description"),
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    async def whitelist(self, interaction: nextcord.Interaction):
        pass

    @whitelist.subcommand(name="add", description=t("PalguardCog", "whitelistadd.description"))
    @restrict_command()
    async def whitelistadd(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description=t("PalguardCog", "description.userid")),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "whitelistadd.server_not_found").format(server=server), ephemeral=True
            )
            return
        asyncio.create_task(
            self.rcon_util.rcon_command(server_info, f"whitelist_add {steamid}")
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "whitelistadd.title").format(server=server), color=nextcord.Color.green()
        )
        embed.description = t("PalguardCog", "whitelistadd.response").format(steamid=steamid)
        await interaction.followup.send(embed=embed)

    @whitelistadd.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @whitelist.subcommand(name="remove", description=t("PalguardCog", "whitelistremove.description"))
    @restrict_command()
    async def whitelistremove(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description=t("PalguardCog", "description.userid")),
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "whitelistremove.server_not_found").format(server=server), ephemeral=True
            )
            return
        asyncio.create_task(
            self.rcon_util.rcon_command(server_info, f"whitelist_remove {steamid}")
        )
        embed = nextcord.Embed(
            title=t("PalguardCog", "whitelistremove.title").format(server=server), color=nextcord.Color.red()
        )
        embed.description = t("PalguardCog", "whitelistremove.response").format(steamid=steamid)
        await interaction.followup.send(embed=embed)

    @whitelistremove.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    # whitelist_get
    @whitelist.subcommand(name="get", description=t("PalguardCog", "whitelistget.description"))
    @restrict_command()
    async def whitelistget(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description=t("PalguardCog", "description.server"), autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        server_info = await self.get_server_info(server)
        if not server_info:
            await interaction.followup.send(
                t("PalguardCog", "whitelistget.server_not_found").format(server=server), ephemeral=True
            )
            return
        response = await self.rcon_util.rcon_command(server_info, "whitelist_get")
        await interaction.followup.send(f"{t('PalguardCog', 'whitelistget.whitelist')}\n{response}")

    @whitelistget.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

def setup(bot):
    cog = PalguardCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, "all_slash_commands"):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend(
        [
            cog.palguard,
            cog.whitelist
        ]
    )
