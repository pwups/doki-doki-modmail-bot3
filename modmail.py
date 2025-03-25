
import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
MODMAIL_CATEGORY_ID = int(os.getenv("MODMAIL_CATEGORY_ID"))
CUSTOM_EMOJI_ID = int(os.getenv("CUSTOM_EMOJI_ID"))

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.dm_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="^", intents=intents)
bot.remove_command("help")

class CloseButton(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="︵︵ close ♡", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.name.startswith("thread—"):
            return await interaction.response.send_message("⚠️ This button can only be used in a modmail channel.", ephemeral=True)

        await interaction.response.defer()
        
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
                pass

        embed = discord.Embed(
            title="STAFF! modmail closed 💩💩💩",
            description=f"✧ this modmail thread has been closed by {interaction.user.mention}. channel will be deleted shortlyyy",
            color=discord.Color.red()
        )
        await interaction.channel.send(embed=embed)
        await interaction.channel.delete()

async def handle_modmail(message):
    guild = bot.get_guild(GUILD_ID)
    category = discord.utils.get(guild.categories, id=MODMAIL_CATEGORY_ID)
    if not category:
        print("⚠️ Modmail category not found!")
        return

    existing_channel = discord.utils.get(guild.text_channels, name=f"thread—{message.author.id}")
    if existing_channel:
        modmail_channel = existing_channel
    else:
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

        custom_emoji = discord.utils.get(guild.emojis, id=CUSTOM_EMOJI_ID)
        emoji_str = str(custom_emoji) if custom_emoji else "❌"

        view = CloseButton(message.author.id)
        view.children[0].emoji = emoji_str

        await modmail_channel.send(embed=embed, view=view)

    embed = discord.Embed(
        title="<a:NatsuGroove:1353422820335554632>　　ﾉ　　user message:",
        description=message.content,
        color=discord.Color.green()
    )
    embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
    
    if message.attachments:
        embed.add_field(name="Attachments", value="\n".join(a.url for a in message.attachments))
    
    await modmail_channel.send(embed=embed)

    confirm_embed = discord.Embed(
        title="message sent! ⁠♡",
        description="you will receive replies from our staff team shortly.",
        color=discord.Color.green()
    )
    try:
        await message.author.send(embed=confirm_embed)
    except discord.Forbidden:
        pass

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} and ready to receive modmail!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        await handle_modmail(message)
    elif message.channel.name.startswith("thread—") and not message.content.startswith(bot.command_prefix):
        user_id = int(message.channel.name.split("—")[1])
        user = bot.get_user(user_id)
        
        if user:
            embed = discord.Embed(
                description=message.content,
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Reply from {message.author.name}", icon_url=message.author.avatar.url)
            
            if message.attachments:
                embed.add_field(name="Attachments", value="\n".join(a.url for a in message.attachments))
            
            try:
                await user.send(embed=embed)
                await message.add_reaction("✅")
            except discord.Forbidden:
                await message.channel.send("⚠️ Cannot send message to this user. They might have DMs disabled.")
                await message.add_reaction("❌")

    await bot.process_commands(message)

@bot.command()
async def reply(ctx, member: discord.Member, *, response):
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

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=10000)

def start():
    Thread(target=run).start()
    bot.run(TOKEN)

if __name__ == "__main__":
    start()
