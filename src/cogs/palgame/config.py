import nextcord
from nextcord.ext import commands, tasks
from src.utils.palgame import get_palgame_settings, update_palgame_settings

class PalGameSettingsModal(nextcord.ui.Modal):
    def __init__(self, cog):
        super().__init__(title="PalGame Settings")
        self.cog = cog

        self.add_item(nextcord.ui.TextInput(
            label="Battle Cooldown (seconds)",
            placeholder="Enter the cooldown for battles in seconds",
            default_value=str(cog.settings.get("battle_cooldown", 90)),
            style=nextcord.TextInputStyle.short
        ))

        self.add_item(nextcord.ui.TextInput(
            label="Battle Rewards (min/max)",
            placeholder="Enter rewards as 'min,max' for battles",
            default_value=f"{cog.settings.get('battle_reward_min', 20)},"
                          f"{cog.settings.get('battle_reward_max', 50)}",
            style=nextcord.TextInputStyle.short
        ))

        self.add_item(nextcord.ui.TextInput(
            label="Catch Cooldown (seconds)",
            placeholder="Enter the cooldown for catching Pals in seconds",
            default_value=str(cog.settings.get("catch_cooldown", 90)),
            style=nextcord.TextInputStyle.short
        ))

        self.add_item(nextcord.ui.TextInput(
            label="Catch Rewards (min/max)",
            placeholder="Enter rewards as 'min,max' for catching",
            default_value=f"{cog.settings.get('catch_reward_min', 10)},"
                          f"{cog.settings.get('catch_reward_max', 50)}",
            style=nextcord.TextInputStyle.short
        ))

        self.add_item(nextcord.ui.TextInput(
            label="Battle Experience",
            placeholder="Enter the experience gained from battles",
            default_value=str(cog.settings.get("battle_experience", 100)),
            style=nextcord.TextInputStyle.short
        ))

    async def callback(self, interaction: nextcord.Interaction):
        try:
            battle_cooldown = int(self.children[0].value)
            battle_rewards = list(map(int, self.children[1].value.split(',')))
            catch_cooldown = int(self.children[2].value)
            catch_rewards = list(map(int, self.children[3].value.split(',')))
            battle_experience = int(self.children[4].value)

            if len(battle_rewards) != 2 or len(catch_rewards) != 2:
                raise ValueError("Rewards must be in 'min,max' format.")

            new_settings = {
                "battle_cooldown": battle_cooldown,
                "battle_reward_min": battle_rewards[0],
                "battle_reward_max": battle_rewards[1],
                "catch_cooldown": catch_cooldown,
                "catch_reward_min": catch_rewards[0],
                "catch_reward_max": catch_rewards[1],
                "battle_experience": battle_experience
            }

            await update_palgame_settings(new_settings)
            await self.cog.refresh_settings()

            await interaction.response.send_message("PalGame settings updated successfully!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid input! Ensure rewards are in 'min,max' format.", ephemeral=True)

class AdventureSettingsModal(nextcord.ui.Modal):
    def __init__(self, cog):
        super().__init__(title="Adventure Settings")
        self.cog = cog

        self.add_item(nextcord.ui.TextInput(
            label="Adventure Cooldown (seconds)",
            placeholder="Enter the cooldown for adventures in seconds",
            default_value=str(cog.settings.get("adventure_cooldown", 90)),
            style=nextcord.TextInputStyle.short
        ))

        self.add_item(nextcord.ui.TextInput(
            label="Adventure Rewards (min/max)",
            placeholder="Enter rewards as 'min,max' for adventures",
            default_value=f"{cog.settings.get('adventure_reward_min', 50)},"
                          f"{cog.settings.get('adventure_reward_max', 200)}",
            style=nextcord.TextInputStyle.short
        ))
        
        self.add_item(nextcord.ui.TextInput(
            label="Adventure Experience (min/max)",
            placeholder="Enter experience as 'min,max' for adventures",
            default_value=f"{cog.settings.get('adventure_experience_min', 100)},"
                          f"{cog.settings.get('adventure_experience_max', 500)}",
            style=nextcord.TextInputStyle.short
        ))
        
    async def callback(self, interaction: nextcord.Interaction):
        try:
            adventure_cooldown = int(self.children[0].value)
            adventure_rewards = list(map(int, self.children[1].value.split(',')))
            adventure_experience = list(map(int, self.children[2].value.split(',')))

            if len(adventure_rewards) != 2 or len(adventure_experience) != 2:
                raise ValueError("Rewards must be in 'min,max' format.")

            new_settings = {
                "adventure_cooldown": adventure_cooldown,
                "adventure_reward_min": adventure_rewards[0],
                "adventure_reward_max": adventure_rewards[1],
                "adventure_experience_min": adventure_experience[0],
                "adventure_experience_max": adventure_experience[1]
            }

            await update_palgame_settings(new_settings)
            await self.cog.refresh_settings()

            await interaction.response.send_message("Adventure settings updated successfully!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid input!", ephemeral=True)
        

class PalGameSettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = {}
        self.refresh_settings.start()

    @tasks.loop(minutes=1)
    async def refresh_settings(self):
        self.settings = await get_palgame_settings()

    @refresh_settings.before_loop
    async def before_refresh_settings(self):
        await self.bot.wait_until_ready()

    @nextcord.slash_command(
        name="gamesettings",
        description="Manage PalGame settings",
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    async def palgame(self, interaction: nextcord.Interaction):
        pass

    @palgame.subcommand(name="core", description="Edit the PalGame settings")
    async def settings(self, interaction: nextcord.Interaction):
        modal = PalGameSettingsModal(self)
        await interaction.response.send_modal(modal)
        
    @palgame.subcommand(name="adventure", description="Manage Adventure settings")
    async def adventure(self, interaction: nextcord.Interaction):
        modal = AdventureSettingsModal(self)
        await interaction.response.send_modal(modal)

def setup(bot):
    bot.add_cog(PalGameSettingsCog(bot))
