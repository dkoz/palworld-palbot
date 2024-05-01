import json
import os
import nextcord
from nextcord.ext import commands
from util.rconutility import RconUtility
import asyncio

class PalguardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.load_pals()
        self.load_items()
        self.load_eggs()
        self.rcon_util = RconUtility(self.servers)
        self.timeout = 30

    def load_config(self):
        config_path = "config.json"
        with open(config_path) as config_file:
            config = json.load(config_file)
            self.servers = config["PALWORLD_SERVERS"]

    def load_pals(self):
        pals_path = os.path.join("gamedata", "pals.json")
        with open(pals_path) as pals_file:
            self.pals = json.load(pals_file)["creatures"]

    def load_items(self):
        items_path = os.path.join("gamedata", "items.json")
        with open(items_path) as items_file:
            self.items = json.load(items_file)["items"]

    def load_eggs(self):
        eggs_path = os.path.join("gamedata", "eggs.json")
        with open(eggs_path) as eggs_file:
            self.eggs = json.load(eggs_file)["eggs"]

    async def autocomplete_server(
        self, interaction: nextcord.Interaction, current: str
    ):
        choices = [
            server for server in self.servers if current.lower() in server.lower()
        ]
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

    @nextcord.slash_command(
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    async def palguard(self, _interaction: nextcord.Interaction):
        pass

    @palguard.subcommand(name="reload", description="Reload server configuration.")
    async def reloadcfg(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(server, "reloadcfg")
        await interaction.followup.send(f"**Response:** {response}")

    @reloadcfg.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palguard.subcommand(description="Give a Pal to a player.")
    async def givepal(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description="SteamID/UID of the player."),
        palid: str = nextcord.SlashOption(
            description="The ID of the Pal.", autocomplete=True
        ),
        level: str = nextcord.SlashOption(description="Level of the Pal"),
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        pal_id = next((pal["id"] for pal in self.pals if pal["name"] == palid), None)
        if not pal_id:
            await interaction.followup.send("Pal ID not found.", ephemeral=True)
            return
        asyncio.create_task(
            self.rcon_util.rcon_command(server, f"givepal {steamid} {pal_id} {level}")
        )
        embed = nextcord.Embed(
            title=f"Palguard Pal - {server}", color=nextcord.Color.blue()
        )
        embed.description = f"Giving {palid} to {steamid}."
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

    @palguard.subcommand(description="Give an item to a player.")
    async def giveitem(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description="SteamID/UID of the player."),
        itemid: str = nextcord.SlashOption(
            description="The ID of the Item.", autocomplete=True
        ),
        amount: str = nextcord.SlashOption(description="Item amount"),
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        item_id = next(
            (item["id"] for item in self.items if item["name"] == itemid), None
        )
        if not item_id:
            await interaction.followup.send("Item ID not found.", ephemeral=True)
            return
        asyncio.create_task(
            self.rcon_util.rcon_command(server, f"give {steamid} {item_id} {amount}")
        )
        embed = nextcord.Embed(
            title=f"Palguard Item - {server}", color=nextcord.Color.blue()
        )
        embed.description = f"Giving {itemid} to {steamid}."
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

    @palguard.subcommand(description="Give experience to a player.")
    async def giveexp(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description="SteamID/UID of the player."),
        amount: str = nextcord.SlashOption(description="Experience amount"),
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        asyncio.create_task(
            self.rcon_util.rcon_command(server, f"give_exp {steamid} {amount}")
        )
        embed = nextcord.Embed(
            title=f"Palguard Experience - {server}", color=nextcord.Color.blue()
        )
        embed.description = f"Giving {amount} experience to {steamid}."
        await interaction.followup.send(embed=embed)

    @giveexp.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palguard.subcommand(description="Give an egg to a player.")
    async def giveegg(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description="SteamID/UID of the player."),
        eggid: str = nextcord.SlashOption(
            description="The ID of the Egg.", autocomplete=True
        ),
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        egg_id = next((egg["id"] for egg in self.eggs if egg["name"] == eggid), None)
        if not egg_id:
            await interaction.followup.send("Egg ID not found.", ephemeral=True)
            return
        asyncio.create_task(
            self.rcon_util.rcon_command(server, f"giveegg {steamid} {egg_id}")
        )
        embed = nextcord.Embed(
            title=f"Palguard Egg - {server}", color=nextcord.Color.blue()
        )
        embed.description = f"Giving {eggid} to {steamid}."
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

    @palguard.subcommand(name="help", description="List of Palguard commands.")
    async def palguardhelp(
        self,
        interaction: nextcord.Interaction,
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        response = await self.rcon_util.rcon_command(server, "getrconcmds")
        await interaction.followup.send(f"{response}")

    @palguardhelp.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

    @palguard.subcommand(description="Give a Lifmunk Effigy relics to a player.")
    async def giverelic(
        self,
        interaction: nextcord.Interaction,
        steamid: str = nextcord.SlashOption(description="SteamID/UID of the player."),
        amount: str = nextcord.SlashOption(description="Lifmunk Effigy relic amount"),
        server: str = nextcord.SlashOption(
            description="Select a server", autocomplete=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        asyncio.create_task(
            self.rcon_util.rcon_command(server, f"give_relic {steamid} {amount}")
        )
        embed = nextcord.Embed(
            title=f"Palguard Relic - {server}", color=nextcord.Color.blurple()
        )
        embed.description = f"Giving {amount} Lifmunk Effigy relics to {steamid}."
        await interaction.followup.send(embed=embed)
        
    @giverelic.on_autocomplete("server")
    async def on_autocomplete_rcon(
        self, interaction: nextcord.Interaction, current: str
    ):
        await self.autocomplete_server(interaction, current)

def setup(bot):
    config_path = "config.json"
    with open(config_path) as config_file:
        config = json.load(config_file)

    if config.get("PALGUARD_ACTIVE", False):
        cog = PalguardCog(bot)
        bot.add_cog(cog)
        if not hasattr(bot, "all_slash_commands"):
            bot.all_slash_commands = []
        bot.all_slash_commands.extend(
            [
                cog.palguard,
                cog.reloadcfg,
                cog.givepal,
                cog.giveitem,
                cog.giveexp,
                cog.giveegg,
                cog.giverelic,
            ]
        )
    else:
        print("Palguard disabled by default. Please enable it in config.json")