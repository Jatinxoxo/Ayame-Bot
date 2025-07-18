import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import random
import pytz
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing!")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Short kawaii status messages - optimized for Discord member list
STATUS_MESSAGES = [
    "🌸 {members:,} members",
    "✨ {online:,} online",
    "🍥 {servers} servers",
    "🌌 Tier 3 Premium",
    "🕒 {tokyo_time}",
    "🎴 Eating mochi",
    "🌘 Anime time",
    "💫 {members:,} kawaii",
    "🎋 {online:,} active",
    "🌙 Night mode",
    "🎨 Creating magic",
    "🌸 Premium bot",
    "⭐ Kawaii vibes",
    "🎪 Bot manager",
    "🌟 Professional"
]

start_time = datetime.utcnow()  # 🕐 Track bot startup time

def get_total_members():
    """Get total members across all servers with error handling"""
    try:
        total = sum(guild.member_count or 0 for guild in bot.guilds)
        logger.debug(f"Total members calculated: {total}")
        return total
    except Exception as e:
        logger.error(f"Error calculating total members: {e}")
        return 0

def get_total_online():
    """Get total online members across all servers with error handling"""
    try:
        online_count = 0
        for guild in bot.guilds:
            try:
                for member in guild.members:
                    if member.status != discord.Status.offline:
                        online_count += 1
            except Exception as e:
                logger.warning(f"Error counting online members in {guild.name}: {e}")
                continue
        logger.debug(f"Total online members: {online_count}")
        return online_count
    except Exception as e:
        logger.error(f"Error calculating total online members: {e}")
        return 0

def get_tokyo_time():
    """Get current Tokyo time formatted with JST"""
    try:
        tz = pytz.timezone('Asia/Tokyo')
        time_str = datetime.now(tz).strftime('%I:%M%p JST').lower()
        logger.debug(f"Tokyo time: {time_str}")
        return time_str
    except Exception as e:
        logger.error(f"Error getting Tokyo time: {e}")
        return "error"

def format_status_text(template):
    """Format status text with current stats and error handling"""
    try:
        formatted = template.format(
            members=get_total_members(),
            online=get_total_online(),
            servers=len(bot.guilds),
            tokyo_time=get_tokyo_time()
        )
        logger.debug(f"Formatted status: {formatted}")
        return formatted
    except Exception as e:
        logger.error(f"Error formatting status text: {e}")
        return "🌸 Bot Active"

@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"🌸 Connected to {len(bot.guilds)} servers")
    logger.info(f"👥 Serving {get_total_members():,} total members")
    logger.info(f"⚡ Bot startup time: {start_time}")
    
    await bot.wait_until_ready()
    if not update_presence.is_running():
        update_presence.start()
        logger.info("🔄 Presence update task started")

@tasks.loop(seconds=60)
async def update_presence():
    """Update bot presence with rotating kawaii professional status"""
    try:
        if not bot.guilds:
            logger.warning("No guilds available, skipping presence update")
            return
            
        status_template = random.choice(STATUS_MESSAGES)
        status_text = format_status_text(status_template)
        
        # Ensure text fits Discord's member list limit (30 characters max)
        if len(status_text) > 30:
            fallback_text = f"🌸 {get_total_members():,}"
            if len(fallback_text) > 30:
                status_text = "🌸 Bot Active"
            else:
                status_text = fallback_text
            logger.warning(f"Status text too long, using fallback: {status_text}")
        
        activity = discord.Game(name=status_text)
        await bot.change_presence(status=discord.Status.online, activity=activity)
        
        logger.info(f"🔄 Status updated: {status_text}")
        
    except discord.HTTPException as e:
        logger.error(f"❌ Discord HTTP error during presence update: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error during presence update: {e}")

@update_presence.before_loop
async def before_update_presence():
    """Wait for bot to be ready before starting presence updates"""
    await bot.wait_until_ready()
    logger.info("🎯 Presence update task ready to start")

@update_presence.error
async def update_presence_error(error):
    """Handle presence update task errors"""
    logger.error(f"❌ Presence update task error: {error}")
    # Restart the task after 60 seconds
    await asyncio.sleep(60)
    if not update_presence.is_running():
        update_presence.restart()
        logger.info("🔄 Presence update task restarted after error")

@bot.event
async def on_guild_join(guild):
    """Update presence when joining a new server"""
    logger.info(f"🎉 Joined new server: {guild.name} (ID: {guild.id}) - {guild.member_count} members")
    # Force immediate status update
    if update_presence.is_running():
        update_presence.restart()
        logger.info("🔄 Presence update restarted due to guild join")

@bot.event
async def on_guild_remove(guild):
    """Update presence when leaving a server"""
    logger.info(f"👋 Left server: {guild.name} (ID: {guild.id})")
    # Force immediate status update
    if update_presence.is_running():
        update_presence.restart()
        logger.info("🔄 Presence update restarted due to guild leave")

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle bot errors"""
    logger.error(f"❌ Bot error in event {event}: {args}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        logger.debug(f"Command not found: {ctx.message.content}")
        return
    logger.error(f"❌ Command error in {ctx.command}: {error}")

# Health check command
@bot.command(name='status')
async def bot_status(ctx):
    """Show bot status information"""
    try:
        uptime = datetime.utcnow() - start_time
        embed = discord.Embed(title="🤖 Bot Status", color=0xFF69B4)
        embed.add_field(name="🌸 Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="👥 Total Members", value=f"{get_total_members():,}", inline=True)
        embed.add_field(name="✨ Online Members", value=f"{get_total_online():,}", inline=True)
        embed.add_field(name="🕒 Tokyo Time", value=get_tokyo_time(), inline=True)
        embed.add_field(name="⏰ Uptime", value=f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m", inline=True)
        embed.add_field(name="🔄 Status Updates", value="Every 60 seconds", inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await ctx.send("❌ Error getting bot status")

INITIAL_EXTENSIONS = [
    "cogs.post_commands",
    "cogs.autopost_commands",
    "cogs.category_commands"
]

async def main():
    """Main bot startup function with enhanced error handling"""
    try:
        # Load extensions
        for ext in INITIAL_EXTENSIONS:
            try:
                await bot.load_extension(ext)
                logger.info(f"🔄 Loaded extension: {ext}")
            except Exception as e:
                logger.error(f"❌ Failed to load extension {ext}: {e}")
        
        logger.info("🚀 Starting bot...")
        await bot.start(BOT_TOKEN)
        
    except discord.LoginFailure:
        logger.error("❌ Invalid bot token!")
        raise
    except discord.HTTPException as e:
        logger.error(f"❌ Discord HTTP error: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during startup: {e}")
        raise
    finally:
        if not bot.is_closed():
            await bot.close()
            logger.info("🛑 Bot connection closed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot shutdown by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise