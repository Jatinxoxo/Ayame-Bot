import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import itertools
from datetime import datetime
import pytz

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

start_time = datetime.utcnow()
status_messages = itertools.cycle([])

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.wait_until_ready()
    update_status_messages()
    update_presence.start()

def get_uptime():
    delta = datetime.utcnow() - start_time
    days, seconds = delta.days, delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return ' '.join(parts) or "0m"

def get_tokyo_time():
    tz = pytz.timezone('Asia/Tokyo')
    return datetime.now(tz).strftime('%I:%M %p')

def update_status_messages():
    total_members = sum(guild.member_count or 0 for guild in bot.guilds)
    online_members = sum(1 for guild in bot.guilds for m in guild.members if m.status != discord.Status.offline)
    total_servers = len(bot.guilds)

    global status_messages
    status_messages = itertools.cycle([
        f"⏳ Uptime: {get_uptime()}",
        f"🌸 {total_members} members",
        f"✨ {online_members} online",
        f"🍥 {total_servers} servers",
        f"🌌 Tier 3",
        f"🕒 Tokyo: {get_tokyo_time()}",
        f"🎴 Eat the mochi",
        f"🌘 Anime time"
    ])

@tasks.loop(seconds=60)
async def update_presence():
    try:
        update_status_messages()
        next_status = next(status_messages)
        activity = discord.Activity(type=discord.ActivityType.watching, name=next_status)
        await bot.change_presence(status=discord.Status.online, activity=activity)
    except Exception as e:
        print("Presence update failed:", e)

INITIAL_EXTENSIONS = [
    "cogs.post_commands",
    "cogs.autopost_commands",
    "cogs.category_commands"
]

async def main():
    for ext in INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"🔄 Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load extension {ext}: {e}")
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
