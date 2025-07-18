import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import itertools
import datetime
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

status_messages = itertools.cycle([])
start_time = datetime.datetime.utcnow()

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.wait_until_ready()
    update_status_messages()
    update_presence.start()

def format_uptime():
    delta = datetime.datetime.utcnow() - start_time
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes = rem // 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def update_status_messages():
    total_members = sum(g.member_count or 0 for g in bot.guilds)
    online_members = sum(1 for g in bot.guilds for m in g.members if m.status != discord.Status.offline)
    tokyo_time = datetime.datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%I:%M %p")
    total_guilds = len(bot.guilds)
    highest_tier = max((g.premium_tier for g in bot.guilds), default=0)

    global status_messages
    status_messages = itertools.cycle([
        f"⏳ Uptime: {format_uptime()}",
        f"🌸 {total_members} members",
        f"✨ {online_members} online",
        f"🍥 {total_guilds} servers",
        f"🌌 Tier {highest_tier}",
        f"🕒 Tokyo: {tokyo_time}",
        "🎴 Eat the mochi",
        "🌘 Anime time"
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
