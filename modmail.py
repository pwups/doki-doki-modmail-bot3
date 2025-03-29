import discord
from discord.ext import commands
import os
import asyncio
import io
import aiohttp
import random
import logging
from flask import Flask
from threading import Thread

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ModMailBot')

# Define the intents
intents = discord.Intents.default()
intents.message_content = True

# Bot initialization
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store user:channel mappings
active_tickets = {}

# Dictionary to store channel:user mappings (for reverse lookup)
channel_user_map = {}

# Embed colors
EMBED_COLORS = [
    0xE0BBFF,  # Light Purple
    0xFFC0CB,  # Light Pink
    0xD2B48C,  # Light Brown
    0xFFDAB9   # Light Orange
]

# Close Ticket Button
class CloseTicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        
        if channel.id in channel_user_map:
            user_id = channel_user_map[channel.id]
            user = await bot.fetch_user(user_id)
            
            # Send closing message to user
            embed = discord.Embed(
                title="<a:pnk_sparkle:1353665702313197629>　　ﾉ　　thread closed.",
                description="✧ contact us again if needed!",
                color=random.choice(EMBED_COLORS)
            )
            embed.set_footer(text=f"Closed by {interaction.user.name}")
            
            try:
                await user.send(embed=embed)
                
                # Remove from mapping dictionaries
                if user_id in active_tickets:
                    del active_tickets[user_id]
                if channel.id in channel_user_map:
                    del channel_user_map[channel.id]
                
                # Confirm closure in channel
                await interaction.response.send_message("Ticket closed. This channel will be deleted in 5 seconds.")
                await asyncio.sleep(5)
                await channel.delete()
                
            except discord.errors.Forbidden:
                await interaction.response.send_message("Could not message the user. They may have blocked the bot or disabled DMs.")
            except Exception as e:
                logger.error(f"Error closing ticket: {e}")
                await interaction.response.send_message(f"Error closing ticket: {e}")
        else:
            await interaction.response.send_message("This doesn't appear to be a valid ticket channel.")

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')
    # Register the close ticket button
    bot.add_view(CloseTicketButton())

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Process commands if it's a command
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    # Handle DMs from users
    if isinstance(message.channel, discord.DMChannel):
        await handle_dm(message)
    
    # Handle messages in ModMail channels
    elif not isinstance(message.channel, discord.DMChannel) and message.channel.id in channel_user_map:
        await handle_staff_reply(message)

async def handle_dm(message):
    user_id = message.author.id
    
    # React with custom emoji
    # Note: You need to replace "mail_emoji" with your actual emoji ID or name
    try:
        # Example with Unicode emoji, replace with your custom emoji
        await message.add_reaction(discord.utils.get(bot.emojis, name="Pink_hearts"))
        # For custom emoji, use: await message.add_reaction(discord.utils.get(bot.emojis, name="your_emoji_name"))
    except Exception as e:
        logger.error(f"Failed to add reaction: {e}")
    
    # Check if user already has an active ticket
    if user_id in active_tickets:
        # Forward message to existing ticket channel
        channel = bot.get_channel(active_tickets[user_id])
        
        if channel:
            # Create embed for forwarding message
            embed = discord.Embed(
                description=message.content,
                color=random.choice(EMBED_COLORS)
            )
            embed.set_author(name=f"{message.author.name}#{message.author.discriminator}", 
                            icon_url=message.author.avatar.url if message.author.avatar else None)
            embed.timestamp = message.created_at
            
            # Send embed
            await channel.send(embed=embed)
            
            # Handle attachments if any
            if message.attachments:
                for attachment in message.attachments:
                    # Download attachment
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status == 200:
                                data = await resp.read()
                                file = discord.File(io.BytesIO(data), filename=attachment.filename)
                                await channel.send(f"Attachment from {message.author.name}:", file=file)
        else:
            # Channel was deleted or not found
            del active_tickets[user_id]
            # Create a new ticket
            await create_ticket(message)
    else:
        # Create a new ticket
        await create_ticket(message)

async def create_ticket(message):
    user_id = message.author.id
    user = message.author
    guild = None
    
    # Find the first guild the bot is in (this could be enhanced to support multiple guilds)
    for g in bot.guilds:
        guild = g
        break
    
    if not guild:
        await message.author.send("Error: Bot is not in any server.")
        return
    
    # Create a new channel for this ticket
    category = discord.utils.get(guild.categories, name="ModMail Tickets")
    
    # Create category if it doesn't exist
    if not category:
        try:
            category = await guild.create_category("ModMail Tickets")
            # Set permissions for the category to be staff-only
            for role in guild.roles:
                # Skip @everyone role
                if role.name == "@everyone":
                    await category.set_permissions(role, read_messages=False, send_messages=False)
                # Set permissions for roles that might be staff
                elif any(keyword in role.name.lower() for keyword in ["Literature Club", "co found", "admin", "moderator", "helper"]):
                    await category.set_permissions(role, read_messages=True, send_messages=True)
        except discord.errors.Forbidden:
            await message.author.send("Error: I don't have permission to create channels in the server.")
            return
    
    # Create channel name
    channel_name = f"thread—{user.name}"
    # Remove invalid characters for Discord channel names
    channel_name = ''.join(c for c in channel_name if c.isalnum() or c in ['-', '_']).lower()
    
    try:
        # Create channel
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            topic=f"modmail thread from {user.name} / ({user.id})"
        )
        
        # Store the mappings
        active_tickets[user_id] = channel.id
        channel_user_map[channel.id] = user_id
        
        # Send introduction embed with Close Ticket button
        embed = discord.Embed(
            title="new modmail thread! ♡",
            description=f"a new thread has been opened by {user.mention}",
            color=random.choice(EMBED_COLORS)
        )
        
        # Add the first message from the user
        embed.add_field(name="First Message", value=message.content or "(No message content)", inline=False)
        
        # Send initial embed with close button
        await channel.send(embed=embed, view=CloseTicketButton())
        
        # Send confirmation to user
        user_embed = discord.Embed(
            title="<a:w_catrolling:1353670148518707290>　　ﾉ　　new thread opened.",
            description="✧ **submitting a blacklist?**\nprovide doc link immediately & add more details!\n✧ **verifying?**\nmake sure you read everything in the verify channel first. when you're ready, please send the necessary info!\n✧ **others?**\nno we don't do partnerships. no we are not hiring pms. modmail is for important dms only!",
            color=random.choice(EMBED_COLORS)
        )
        await user.send(embed=user_embed)
        
        # Forward attachments if any
        if message.attachments:
            await channel.send(f"attachments from {user.name} :")
            for attachment in message.attachments:
                # Download attachment
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            file = discord.File(io.BytesIO(data), filename=attachment.filename)
                            await channel.send(file=file)
        
    except discord.errors.Forbidden:
        await message.author.send("Error: I don't have permission to create channels in the server.")
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        await message.author.send(f"An error occurred while creating your ticket: {e}")

async def handle_staff_reply(message):
    channel_id = message.channel.id
    
    # Check if this is a valid ModMail channel
    if channel_id in channel_user_map:
        user_id = channel_user_map[channel_id]
        
        try:
            user = await bot.fetch_user(user_id)
            
            # Create embed for the user
            embed = discord.Embed(
                description=message.content,
                color=random.choice(EMBED_COLORS)
            )
            embed.set_author(name=f"{message.author.name} (Staff)", 
                            icon_url=message.author.avatar.url if message.author.avatar else None)
            embed.timestamp = message.created_at
            
            # Send embed to user
            await user.send(embed=embed)
            
            # Handle attachments if any
            if message.attachments:
                for attachment in message.attachments:
                    # Download attachment
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status == 200:
                                data = await resp.read()
                                file = discord.File(io.BytesIO(data), filename=attachment.filename)
                                await user.send(f"Attachment from staff:", file=file)
            
            # Add confirmation reaction to staff message
            await message.add_reaction("✅")
            
        except discord.errors.Forbidden:
            await message.channel.send("Error: Cannot send message to this user. They may have blocked the bot or left the server.")
        except Exception as e:
            logger.error(f"Error sending staff reply: {e}")
            await message.channel.send(f"Error sending message: {e}")

@bot.command(name="dm")
@commands.has_any_role("Staff", "Admin", "Moderator", "Support")  # Adjust roles as needed
async def dm_command(ctx, user_id: int, *, message: str):
    """Send a direct message to a user via the bot"""
    # Check if command is used in a server channel
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("This command can only be used in server channels.")
        return
    
    try:
        # Get the user
        user = await bot.fetch_user(user_id)
        
        # Create embed for the user
        embed = discord.Embed(
            description=message,
            color=random.choice(EMBED_COLORS)
        )
        embed.set_author(name=f"{ctx.author.name} (Staff)", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.timestamp = ctx.message.created_at
        
        # Send the embed
        await user.send(embed=embed)
        
        # Send confirmation
        await ctx.send(f"Message sent to {user.name}#{user.discriminator}.")
        
    except discord.errors.Forbidden:
        await ctx.send("Error: Cannot send message to this user. They may have blocked the bot or have DMs disabled.")
    except Exception as e:
        logger.error(f"Error in dm command: {e}")
        await ctx.send(f"Error sending message: {e}")

@bot.command(name="close")
@commands.has_any_role("Literature Club", "co found", "admin", "moderator", "helper")  # Adjust roles as needed
async def close_command(ctx):
    """Close the current ModMail ticket"""
    # Check if command is used in a ModMail channel
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("This command can only be used in server channels.")
        return
    
    channel_id = ctx.channel.id
    
    if channel_id in channel_user_map:
        user_id = channel_user_map[channel_id]
        user = await bot.fetch_user(user_id)
        
        # Send closing message to user
        embed = discord.Embed(
            title="<a:pnk_sparkle:1353665702313197629>　　ﾉ　　thread closed.",
            description="✧ contact us again if needed!",
            color=random.choice(EMBED_COLORS)
        )
        embed.set_footer(text=f"Closed by {ctx.author.name}")
        
        try:
            await user.send(embed=embed)
            
            # Remove from mapping dictionaries
            if user_id in active_tickets:
                del active_tickets[user_id]
            if channel_id in channel_user_map:
                del channel_user_map[channel_id]
            
            # Confirm closure in channel
            await ctx.send("Ticket closed. This channel will be deleted in 5 seconds.")
            await asyncio.sleep(5)
            await ctx.channel.delete()
            
        except discord.errors.Forbidden:
            await ctx.send("Could not message the user. They may have blocked the bot or disabled DMs.")
        except Exception as e:
            logger.error(f"Error closing ticket: {e}")
            await ctx.send(f"Error closing ticket: {e}")
    else:
        await ctx.send("This doesn't appear to be a valid ticket channel.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.MissingAnyRole):
        await ctx.send("You do not have the required role to use this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Bad argument: {error}")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send(f"An error occurred: {error}")

# Run the bot with the token from environment variable
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=10000)  # Change port if needed

def keep_alive():
    Thread(target=run).start()

# Bot Setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Run the bot with the token from environment variable
if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    
    if not token:
        logger.error("No token found in environment variables!")
        print("Error: Please set the DISCORD_TOKEN environment variable.")
    else:
        keep_alive()  # Start Flask server BEFORE bot runs
        bot.run(token)  # Run the bot with the correct token
