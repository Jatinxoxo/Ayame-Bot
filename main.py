import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import random
import pytz
from datetime import datetime

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

# Professional kawaii status messages - optimized for Discord's character limit
STATUS_MESSAGES = [
    "🌸 {members:,} members across {servers} servers",
    "✨ {online:,} online • {servers} communities",
    "🍥 Serving {servers} servers • {members:,} users",
    "🌌 {online:,} active • Premium Tier 3",
    "🕒 Tokyo {tokyo_time} • {members:,} members",
    "🎴 {servers} servers • Eating virtual mochi",
    "🌘 {online:,} online • Anime time desu~",
    "💫 {members:,} kawaii members • {servers} homes",
    "🎋 {online:,} active • Protecting {servers} servers",
    "🌙 Tokyo {tokyo_time} • {online:,} night owls",
    "🎨 Creating magic in {servers} servers",
    "🌸 {members:,} friends • Premium experience",
    "⭐ {online:,} online • Spreading kawaii vibes",
    "🎪 Managing {servers} communities daily",
    "🌟 {members:,} total • Professional service"
]

start_time = datetime.utcnow()  # 🕐 Track bot startup time

def get_total_members():
    """Get total members across all servers"""
    return sum(guild.member_count or 0 for guild in bot.guilds)

def get_total_online():
    """Get total online members across all servers"""
    return sum(
        1 for guild in bot.guilds for member in guild.members
        if member.status != discord.Status.offline
    )

def get_tokyo_time():
    """Get current Tokyo time formatted"""
    tz = pytz.timezone('Asia/Tokyo')
    return datetime.now(tz).strftime('%I:%M%p').lower()

def format_status_text(template):
    """Format status text with current stats"""
    return template.format(
        members=get_total_members(),
        online=get_total_online(),
        servers=len(bot.guilds),
        tokyo_time=get_tokyo_time()
    )

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"🌸 Connected to {len(bot.guilds)} servers")
    print(f"👥 Serving {get_total_members():,} total members")
    await bot.wait_until_ready()
    update_presence.start()

@tasks.loop(seconds=60)
async def update_presence():
    """Update bot presence with rotating kawaii professional status"""
    try:
        status_template = random.choice(STATUS_MESSAGES)
        status_text = format_status_text(status_template)
        
        # Ensure text fits Discord's limit (128 characters for activity name)
        if len(status_text) > 128:
            # Fallback to shorter format if needed
            status_text = f"🌸 {get_total_members():,} members • {len(bot.guilds)} servers"
        
        activity = discord.Game(name=status_text)
        await bot.change_presence(status=discord.Status.online, activity=activity)
        
        # Optional: Log status updates for debugging
        # print(f"🔄 Status updated: {status_text}")
        
    except Exception as e:
        print(f"❌ Presence update failed: {e}")

@bot.event
async def on_guild_join(guild):
    """Update presence when joining a new server"""
    print(f"🎉 Joined new server: {guild.name} ({guild.member_count} members)")
    # Force immediate status update
    if update_presence.is_running():
        update_presence.restart()

@bot.event
async def on_guild_remove(guild):
    """Update presence when leaving a server"""
    print(f"👋 Left server: {guild.name}")
    # Force immediate status update
    if update_presence.is_running():
        update_presence.restart()

INITIAL_EXTENSIONS = [
    "cogs.post_commands",
    "cogs.autopost_commands",
    "cogs.category_commands"
]

async def main():
    """Main bot startup function"""
    for ext in INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"🔄 Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load extension {ext}: {e}")
    
    print("🚀 Starting bot...")
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())