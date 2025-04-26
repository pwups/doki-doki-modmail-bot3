import discord
from discord.ext import commands
from discord import app_commands, ui
import io

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
MOD_ROLE_ID = 1355839481982488626  # Replace with your moderator role ID
CUSTOM_EMOJI = "<a:04_pink_mail:1353838679268921427>"  # Replace with your emoji

class CloseButton(ui.View):
    def __init__(self, channel, user):
        super().__init__(timeout=None)
        self.channel = channel
        self.user = user

    @ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("ticket closed.", ephemeral=True)
        embed = discord.Embed(title="ticket closed 🔒", color=discord.Color.red())
        embed.description = "your ticket with staff was closed. contact us again if needed!"
        embed.set_footer(text="sending a new response will open a new ticket.", icon_url=self.channel.guild.icon.url)
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

@bot.event
async def on_message(message):
    await bot.process_commands(message)

# User DMs the bot
    if message.guild is None and not message.author.bot:
        guild = bot.get_guild(GUILD_ID)
        category = guild.get_channel(CATEGORY_ID)
        existing = ticket_channels.get(message.author.id)

        if not existing:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.get_role(MOD_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            channel = await guild.create_text_channel(
                name=f"ticket-{message.author.name}",
                category=category,
                overwrites=overwrites
            )
            ticket_channels[message.author.id] = channel

            embed = discord.Embed(
                title="ticket created 🔓",
                description="our staff team will respond when they are available. please be patient!",
                color=discord.Color.blurple()
            )
            embed.set_footer(text="your message has been sent", icon_url=guild.icon.url)
            await message.author.send(embed=embed)

            await channel.send(embed=discord.Embed(
                description=f"new ticket created by {message.author.mention}",
                color=discord.Color.green()
            ), view=CloseButton(channel, message.author))

        else:
            channel = existing

        await forward_to_ticket(channel, message.author, message.content, message.author.display_avatar.url, message.attachments)

    # Moderator messages in ticket channel
    elif message.guild and not message.author.bot:
        if message.channel.category_id == CATEGORY_ID:
            for user_id, chan in ticket_channels.items():
                if chan.id == message.channel.id:
                    user = await bot.fetch_user(user_id)
                    embed = discord.Embed(description=message.content, color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
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
    embed = discord.Embed(description=content, color=discord.Color.green())
    embed.set_author(name=author.name, icon_url=avatar_url)

    files = []
    for attachment in attachments:
        fp = await attachment.read()
        files.append(discord.File(io.BytesIO(fp), filename=attachment.filename))

    await channel.send(embed=embed, files=files if files else None)

bot.run("MTM1MzY2NzMxMTIxNDUzMDU3MA.G4FVlN.DQYspocc_vgZRrhA2p8_1ox_wPHrnAVK0PFzw0")
