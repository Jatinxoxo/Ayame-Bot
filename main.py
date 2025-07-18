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

STATUS_MESSAGES = [
    "🌸 {members} members",
    "✨ {online} online",
    "🍥 {servers} servers",
    "🌌 Tier 3",
    "🕒 Tokyo: {tokyo_time}",
    "🎴 Eat the mochi",
    "🌘 Anime time"
]

start_time = datetime.utcnow()  # 🕐 Track bot startup time

def get_total_members():
    return sum(guild.member_count or 0 for guild in bot.guilds)

def get_total_online():
    return sum(
        1 for guild in bot.guilds for member in guild.members
        if member.status != discord.Status.offline
    )

def get_tokyo_time():
    tz = pytz.timezone('Asia/Tokyo')
    return datetime.now(tz).strftime('%I:%M %p')

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.wait_until_ready()
    update_presence.start()

@tasks.loop(seconds=60)
async def update_presence():
    try:
        status_template = random.choice(STATUS_MESSAGES)
        status_text = status_template.format(
            members=get_total_members(),
            online=get_total_online(),
            servers=len(bot.guilds),
            tokyo_time=get_tokyo_time()
        )
        activity = discord.Game(name=status_text)
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
