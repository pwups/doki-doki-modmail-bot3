import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import io

TOKEN = os.environ.get("TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.dm_messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
ticket_channels = {}

GUILD_ID = 1353378102650339450  # Replace with your guild ID
CATEGORY_ID = 1353378102650339451  # Replace with the category ID where ticket channels go
MOD_ROLE_ID = 1365973809789800549  # Replace with your moderator role ID
CUSTOM_EMOJI = "<a:04_pink_mail:1353838679268921427>"  # Replace with your emoji

# Define custom hex colors
LIGHT_PINK = discord.Color.from_str("#FFB6C1")
LIGHT_PURPLE = discord.Color.from_str("#D8BFD8")
LIGHT_RED = discord.Color.from_str("#FFA07A")
LIGHT_YELLOW = discord.Color.from_str("#FFFACD")

class CloseButton(ui.View):
    def __init__(self, channel, user):
        super().__init__(timeout=None)
        self.channel = channel
        self.user = user

    @ui.button(label="︵︵ close ♡", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket closed.", ephemeral=True)
        embed = discord.Embed(
            title="<a:pnk_sparkle:1353665702313197629>　　ﾉ　　ticket closed.",
            color=LIGHT_RED
        )
        embed.description = "your ticket with staff was closed. contact us again if needed!"
        embed.set_footer(text="sending a new message will open a new ticket.", icon_url=self.channel.guild.icon.url)
        await self.user.send(embed=embed)
        await self.channel.delete()

@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced commands: {synced}")
    except Exception as e:
        print(f"Sync error: {e}")

    # Set custom status
    activity = discord.Activity(type=discord.ActivityType.watching, name="doki hub's dms ☆")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.guild is None and not message.author.bot:
        guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"Guild with ID {GUILD_ID} not found.")
        return

    category = guild.get_channel(CATEGORY_ID)
    if not category:
        print(f"Category with ID {CATEGORY_ID} not found.")
        return  # Stop if the category doesn't exist!

    existing_channel = ticket_channels.get(message.author.id)

    if not existing_channel or not bot.get_channel(existing_channel.id):
        # Continue safely knowing category exists
        mod_role = guild.get_role(MOD_ROLE_ID)
        if not mod_role:
            print(f"Mod role with ID {MOD_ROLE_ID} not found.")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            mod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        # Create the ticket channel under the found category
        channel = await guild.create_text_channel(
            name=f"ticket—{message.author.name}",
            category=category,
            overwrites=overwrites
        )
        ticket_channels[message.author.id] = channel

            embed = discord.Embed(
                title="<a:w_catrolling:1353670148518707290>　　ﾉ　　new ticket opened.",
                description="our staff team will respond when they are available. please be patient!",
                color=LIGHT_PINK
            )
            embed.set_footer(text="your message has been sent", icon_url=guild.icon.url)
            await message.author.send(embed=embed)

            await channel.send(embed=discord.Embed(
                description=f"New ticket created by {message.author.mention}",
                color=LIGHT_YELLOW
            ), view=CloseButton(channel, message.author))

        else:
            channel = bot.get_channel(existing_channel.id)

        if channel:
            await forward_to_ticket(channel, message.author, message.content, message.author.display_avatar.url, message.attachments)
        else:
            print(f"Could not find or create a valid channel for {message.author}.")

    elif message.guild and not message.author.bot:
        if message.channel.category_id == CATEGORY_ID:
            for user_id, chan in ticket_channels.items():
                if chan.id == message.channel.id:
                    user = await bot.fetch_user(user_id)
                    embed = discord.Embed(
                        description=message.content,
                        color=LIGHT_PURPLE,
                        timestamp=discord.utils.utcnow()
                    )
                    embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
                    embed.set_footer(text="ʚ doki hub staff", icon_url=message.guild.icon.url)

                    files = []
                    for attachment in message.attachments:
                        fp = await attachment.read()
                        files.append(discord.File(io.BytesIO(fp), filename=attachment.filename))

                    try:
                        await user.send(embed=embed, files=files if files else None)
                    except discord.Forbidden:
                        await message.channel.send("Could not DM the user.")
                    break

async def forward_to_ticket(channel, author, content, avatar_url, attachments):
    embed = discord.Embed(description=content, color=LIGHT_YELLOW)
    embed.set_author(name=author.name, icon_url=avatar_url)

    files = []
    for attachment in attachments:
        fp = await attachment.read()
        files.append(discord.File(io.BytesIO(fp), filename=attachment.filename))

    try:
        await channel.send(embed=embed, files=files if files else None)
    except discord.NotFound:
        print(f"Channel {channel.id} not found when trying to forward a message.")

bot.run(TOKEN)
