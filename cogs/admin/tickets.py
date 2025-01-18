import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View
from nextcord.ext.commands import has_permissions, CommandInvokeError
import utils.constants as constants
import json
import os
from io import StringIO

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_folder = 'data'
        self.config_file = os.path.join(self.data_folder, 'tickets.json')
        self.data = self.load_config()
        self.ticket_counter = self.data.get('ticket_counter', 1)
        self.dm_on_close = self.data.get('dm_on_close', False)
        self.transcript_enabled = self.data.get('transcript_enabled', False)
        self.bot.loop.create_task(self.setup_buttons())

    def load_config(self):
        if not os.path.exists(self.config_file):
            os.makedirs(self.data_folder, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({'ticket_channel_id': None, 'log_channel_id': None, 'buttons': [], 'categories': [], 'ticket_counter': 1, 'dm_on_close': False, 'transcript_enabled': False}, f)
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f)

    async def setup_buttons(self):
        await self.bot.wait_until_ready()
        ticket_channel_id = self.data.get('ticket_channel_id')
        if ticket_channel_id:
            channel = self.bot.get_channel(ticket_channel_id)
            if channel:
                for button_info in self.data.get('buttons', []):
                    try:
                        message = await channel.fetch_message(button_info['message_id'])
                    except (nextcord.NotFound, nextcord.HTTPException):
                        continue

                    view = View(timeout=None)
                    for category in self.data.get('categories', []):
                        button = Button(label=category, style=nextcord.ButtonStyle.green, custom_id=f"create_ticket_{category}")
                        button.callback = self.button_callback
                        view.add_item(button)
                    await message.edit(view=view)

    @commands.group(name="tickets", description="Get list of available ticket commands.", invoke_without_command=True)
    @has_permissions(manage_channels=True)
    async def tickets(self, ctx):
        prefix = ctx.prefix
        embed = nextcord.Embed(
            title="Ticket System",
            description="Commands for setting up the ticket system.",
            color=nextcord.Color.orange()
        )
        embed.add_field(
            name="Commands",
            value=f"`{prefix}tickets channel` - Set the ticket channel\n"
                f"`{prefix}tickets logchannel` - Set the log channel\n"
                f"`{prefix}tickets addcategory` - Add a new ticket category\n"
                f"`{prefix}tickets removecategory` - Remove a ticket category\n"
                f"`{prefix}tickets transcript` - Toggle DM on close and transcript generation.\n"
                f"`{prefix}tickets role` - Add a role to the ticket system\n"
                f"`{prefix}tickets setup` - Setup guide for the ticket system",
        )
        embed.set_footer(text="Still in testing...", icon_url=constants.FOOTER_IMAGE)
        await ctx.send(embed=embed)
        
    # setup guide embed
    @tickets.command(name="setup")
    @has_permissions(manage_channels=True)
    async def setup(self, ctx):
        prefix = ctx.prefix
        embed = nextcord.Embed(
            title="Ticket System Setup Guide",
            description=f"Follow the steps below to set up the ticket system.",
            color=nextcord.Color.orange()
        )
        embed.add_field(
            name="Step 1: Create a Ticket Channel",
            value=f"Create a new text channel where users can create tickets. Use the `{prefix}tickets channel` command to set this channel.",
            inline=False
        )
        embed.add_field(
            name="Step 2: Set Log Channel (Optional)",
            value=f"Set a log channel to log ticket creations. Use the `{prefix}tickets logchannel` command to set this channel.",
            inline=False
        )
        embed.add_field(
            name="Step 3: Add Ticket Categories",
            value=f"Add ticket categories using the `{prefix}tickets addcategory` command. Users can create tickets in these categories.",
            inline=False
        )
        embed.add_field(
            name="Step 4: Add Ticket Roles",
            value=f"Add roles that can access the ticket system using the `{prefix}tickets role` command.",
            inline=False
        )
        embed.add_field(
            name="Step 5: Toggle DM on Close and Transcript Generation",
            value=f"Toggle DM on close and transcript generation using the `{prefix}tickets transcript <true/false> <true/false>` command.",
            inline=False
        )
        embed.set_footer(text="Still in testing...", icon_url=constants.FOOTER_IMAGE)
        await ctx.send(embed=embed)

    @tickets.command(name="transcript")
    @has_permissions(manage_channels=True)
    async def toggle_transcript(self, ctx, dm_on_close: bool, transcript_enabled: bool):
        self.data['dm_on_close'] = dm_on_close
        self.data['transcript_enabled'] = transcript_enabled
        self.save_config()
        await ctx.send(f"DM on close set to {dm_on_close}. Transcript generation set to {transcript_enabled}.")

    @tickets.command(name="addcategory")
    @has_permissions(manage_channels=True)
    async def add_category(self, ctx, *, category_name: str):
        if 'categories' not in self.data:
            self.data['categories'] = []
        self.data['categories'].append(category_name)
        self.save_config()
        await self.update_ticket_message(ctx)
        await ctx.send(f"Category '{category_name}' added to the ticket system.")

    @tickets.command(name="removecategory")
    @has_permissions(manage_channels=True)
    async def remove_category(self, ctx, *, category_name: str):
        if 'categories' in self.data and category_name in self.data['categories']:
            self.data['categories'].remove(category_name)
            self.save_config()
            await self.update_ticket_message(ctx)
            await ctx.send(f"Category '{category_name}' removed from the ticket system.")
        else:
            await ctx.send(f"Category '{category_name}' does not exist.")

    async def update_ticket_message(self, ctx):
        ticket_channel_id = self.data.get('ticket_channel_id')
        if ticket_channel_id:
            ticket_channel = self.bot.get_channel(ticket_channel_id)
            if ticket_channel:
                for button_info in self.data.get('buttons', []):
                    if button_info['channel_id'] == ticket_channel_id:
                        try:
                            message = await ticket_channel.fetch_message(button_info['message_id'])
                            await message.delete()
                        except (nextcord.NotFound, nextcord.HTTPException):
                            pass

                view = View(timeout=None)
                for category in self.data['categories']:
                    button = Button(label=category, style=nextcord.ButtonStyle.green, custom_id=f"create_ticket_{category}")
                    button.callback = self.button_callback
                    view.add_item(button)
                
                embed = nextcord.Embed(title="Support Tickets", description="Click a button below to create a new ticket in a specific category.")
                message = await ticket_channel.send(embed=embed, view=view)

                self.data['buttons'] = [{
                    'channel_id': ticket_channel.id,
                    'message_id': message.id,
                    'categories': self.data['categories']
                }]
                self.save_config()
            
    @tickets.command(name="role")
    @has_permissions(manage_channels=True)
    async def add_ticket_roles(self, ctx, *roles: nextcord.Role):
        if 'ticket_roles' not in self.data:
            self.data['ticket_roles'] = []

        for role in roles:
            if role.id not in self.data['ticket_roles']:
                self.data['ticket_roles'].append(role.id)

        self.save_config()
        role_mentions = " ".join([role.mention for role in roles])
        await ctx.send(f"Roles {role_mentions} added to ticket access.")

    @tickets.command(name="channel")
    @has_permissions(manage_channels=True)
    async def setup_ticket(self, ctx, channel: nextcord.TextChannel):
        self.data['ticket_channel_id'] = channel.id

        if 'ticket_roles' in self.data and self.data['ticket_roles']:
            overwrites = {
                ctx.guild.default_role: nextcord.PermissionOverwrite(view_channel=False)
            }
            for role_id in self.data['ticket_roles']:
                role = ctx.guild.get_role(role_id)
                if role:
                    overwrites[role] = nextcord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        manage_threads=True
                    )

            await channel.edit(overwrites=overwrites)
            await ctx.send(f"Ticket system set up in {channel.mention} with role-based access and Manage Threads permission.")
        else:
            await ctx.send(f"Ticket system set up in {channel.mention}.")

        self.save_config()
        await self.update_ticket_message(ctx)

    @tickets.command(name="logchannel")
    @has_permissions(manage_channels=True)
    async def setup_log(self, ctx, channel: nextcord.TextChannel):
        self.data['log_channel_id'] = channel.id
        self.save_config()
        await ctx.send(f"Ticket log channel set to {channel.mention}")

    async def button_callback(self, interaction: nextcord.Interaction):
        custom_id = interaction.data.get('custom_id')
        if custom_id.startswith("create_ticket_"):
            category = custom_id.split("_", 2)[2]
            await self.create_ticket(interaction, category)
        elif custom_id.startswith("close_ticket_"):
            thread_id = int(custom_id.split("_")[-1])
            thread = await self.bot.fetch_channel(thread_id)
            await self.close_ticket(interaction, thread)

    async def create_ticket(self, interaction: nextcord.Interaction, category: str):
        member = interaction.user
        ticket_channel_id = self.data.get('ticket_channel_id')
        if ticket_channel_id:
            ticket_channel = self.bot.get_channel(ticket_channel_id)
            thread = await ticket_channel.create_thread(name=f"ticket-{self.ticket_counter}-{member.display_name}", auto_archive_duration=60)
            self.ticket_counter += 1
            self.data['ticket_counter'] = self.ticket_counter
            self.save_config()

            if self.data.get('log_channel_id'):
                log_channel = self.bot.get_channel(self.data['log_channel_id'])
                if log_channel:
                    embed = nextcord.Embed(title="Ticket Opened", color=nextcord.Color.green())
                    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                    embed.add_field(name="Created By", value=f"{member.display_name}", inline=False)
                    embed.add_field(name="User ID", value=member.id, inline=False)
                    embed.add_field(name="Opened", value=interaction.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
                    embed.add_field(name="Category", value=category, inline=False)
                    embed.add_field(name="Ticket Name", value=thread.name, inline=False)
                    view = View(timeout=None)
                    view.add_item(Button(label="Go to Ticket", style=nextcord.ButtonStyle.link, url=thread.jump_url))
                    await log_channel.send(embed=embed, view=view)

            close_button = Button(label="Close Ticket", style=nextcord.ButtonStyle.red, custom_id=f"close_ticket_{thread.id}")
            close_button.callback = self.button_callback
            view = View(timeout=None)
            view.add_item(close_button)
            embed = nextcord.Embed(title="Your Ticket", description="Support will be with you shortly. Click the button to close this ticket.")
            embed.add_field(name="Explain your issue", value="Provide details about your issue to help us assist you.", inline=False)

            role_mentions = ''
            if 'ticket_roles' in self.data:
                role_mentions = ' '.join(
                    [
                        interaction.guild.get_role(role_id).mention
                        for role_id in self.data['ticket_roles']
                        if interaction.guild.get_role(role_id) is not None
                    ]
                )

            await thread.send(f"{member.mention} {role_mentions}", embed=embed, view=view)
            await interaction.response.send_message("Ticket created!", ephemeral=True)

    async def close_ticket(self, interaction: nextcord.Interaction, thread: nextcord.Thread):
        if not thread.archived:
            await interaction.response.send_message(
                embed=nextcord.Embed(title="Closed", description="Your ticket has been closed.", color=nextcord.Color.red()),
                ephemeral=True
            )
        await thread.edit(archived=True, locked=True)

        if self.transcript_enabled:
            messages = await thread.history(limit=100).flatten()
            transcript = StringIO()
            for msg in reversed(messages):
                transcript.write(f"{msg.author.display_name} [{msg.created_at}]: {msg.content}\n")

            transcript.seek(0)

            if self.dm_on_close:
                try:
                    await interaction.user.send(file=nextcord.File(transcript, filename=f"{thread.name}_transcript.txt"))
                except nextcord.Forbidden:
                    pass

            transcript.seek(0)

            if 'log_channel_id' in self.data:
                log_channel = self.bot.get_channel(self.data['log_channel_id'])
                if log_channel:
                    await log_channel.send(file=nextcord.File(transcript, filename=f"{thread.name}_transcript.txt"))

        self.data['buttons'] = [button for button in self.data['buttons'] if button['message_id'] != thread.last_message_id]
        self.save_config()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide the required arguments.")
        elif isinstance(error, CommandInvokeError):
            original = getattr(error, "original", error)
            await ctx.send(f"An error occurred: {original}")
        else:
            await ctx.send(f"An error occurred: {error}")

def setup(bot):
    bot.add_cog(TicketSystem(bot))
