import discord
from discord.ext import commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")  # Store your bot token in an environment variable
GUILD_ID = int(os.getenv("GUILD_ID"))  # Your Discord server ID
MODMAIL_CATEGORY_ID = int(os.getenv("MODMAIL_CATEGORY_ID"))  # ID of modmail category
CUSTOM_EMOJI_ID = int(os.getenv("CUSTOM_EMOJI_ID"))  # Custom emoji ID for the button

# Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.dm_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="^", intents=intents)
bot.remove_command("help")  # Remove default help command

class CloseButton(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="︵︵ close ♡", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.name.startswith("thread—"):
            return await interaction.response.send_message("⚠️ This button can only be used in a modmail channel.", ephemeral=True)

        user = bot.get_user(self.user_id)
        if user:
            try:
                close_embed = discord.Embed(
                    title="<a:pnk_sparkle:1353665702313197629>　　ﾉ　　thread closed.",
                    description="✧ contact us again if needed!",
                    color=discord.Color.red()
                )
                await user.send(embed=close_embed)
            except discord.Forbidden:
                pass  # User might have DMs disabled

        # Notify staff in the modmail channel
        embed = discord.Embed(
            title="STAFF! modmail closed 💩💩💩",
            description=f"✧ this modmail thread has been closed by {interaction.user.mention}. channel will be deleted shortlyyy",
            color=discord.Color.red()
        )
        await interaction.channel.send(embed=embed)
        await interaction.channel.delete()

    async def on_timeout(self):
        self.clear_items()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} and ready to receive modmail!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    # Handle DMs (User sends a message to the bot)
    if isinstance(message.channel, discord.DMChannel):
        guild = bot.get_guild(GUILD_ID)
        category = discord.utils.get(guild.categories, id=MODMAIL_CATEGORY_ID)
        if not category:
            print("⚠️ Modmail category not found!")
            return

        # Check if a modmail thread already exists for this user
        existing_channel = discord.utils.get(guild.text_channels, name=f"thread—{message.author.id}")
        if existing_channel:
            modmail_channel = existing_channel
        else:
            # Create a new modmail thread
            modmail_channel = await guild.create_text_channel(
                name=f"thread—{message.author.id}",
                category=category
            )
            embed = discord.Embed(
                title="<a:w_catrolling:1353670148518707290>　　ﾉ　　new thread opened.",
                description=f"✧ **submitting a blacklist?**\nprovide doc link immediately & add more details!\n✧ **verifying?**\nmake sure you read everything in the verify channel first. when you're ready, please send the necessary info!\n✧ **others?**\nno we don't do partnerships. no we are not hiring pms. modmail is for important dms only!",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=message.author.avatar.url)

            # Fetch custom emoji
            custom_emoji = discord.utils.get(guild.emojis, id=CUSTOM_EMOJI_ID)
            emoji_str = str(custom_emoji) if custom_emoji else "❌"  # Default to ❌ if emoji is not found

            # Add button with custom emoji
            view = CloseButton(message.author.id)
            view.children[0].emoji = emoji_str  # Set button emoji

            await modmail_channel.send(embed=embed, view=view)

        # Forward the user's message to the modmail channel as an embed
        embed = discord.Embed(
            title="<a:NatsuGroove:1353422820335554632>　　ﾉ　　user message:",
            description=message.content,
            color=discord.Color.green()
        )
        embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
        await modmail_channel.send(embed=embed)

        # Send confirmation message to user
        confirm_embed = discord.Embed(
            title="message sent! ⁠♡",
            description="you will receive replies from our staff team shortly.",
            color=discord.Color.green()
        )
        await message.author.send(embed=confirm_embed)

    await bot.process_commands(message)

@bot.command()
async def reply(ctx, member: discord.Member, *, response):
    """Allows staff to reply to a user's modmail"""
    try:
        embed = discord.Embed(
            description=response,
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Reply from {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await member.send(embed=embed)

        confirm_embed = discord.Embed(
            title="reply sent! ♡",
            description=f"your response has been sent to {member.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=confirm_embed)

    except discord.Forbidden:
        error_embed = discord.Embed(
            title="⚠️ Error",
            description="I can't send messages to this user. They might have DMs disabled.",
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)

bot.run(TOKEN)
