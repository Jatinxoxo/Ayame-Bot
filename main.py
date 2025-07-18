import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import itertools
import datetime
import random

# Load environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing!")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

status_messages = itertools.cycle([])
start_time = datetime.datetime.utcnow()

def get_uptime():
    delta = datetime.datetime.utcnow() - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}m"

def get_japan_time():
    jst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    return jst.strftime("%I:%M %p")

def update_status_messages():
    global status_messages
    status_messages = itertools.cycle([
        f"⏳ Uptime: {get_uptime()}",
        f"🍥 In {len(bot.guilds)} servers",
        f"🕒 Tokyo: {get_japan_time()}",
        f"🎴 {random.choice(['Believe in you', 'Eat the mochi', 'Blossom now', 'Ramen > Everything'])}",
        f"{random.choice(['🌕', '🌗', '🌘', '🌑'])} Anime time",
        f"💻 Code. Deploy. Repeat.",
        f"🌀 Summoning new vibes",
        f"📦 Packing chakra"
    ])

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.wait_until_ready()
    update_status_messages()
    update_presence.start()

@tasks.loop(seconds=60)
async def update_presence():
    try:
        update_status_messages()  # Refresh values like uptime/time
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
