import os
import discord
from discord.ext import commands, tasks
import random
import pytz
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing from environment variables.")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.presences = True
intents.message_content = True

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

@tasks.loop(seconds=60)
async def update_status():
    if bot.guilds:
        status_template = random.choice(STATUS_MESSAGES)
        status_text = status_template.format(
            members=get_total_members(),
            online=get_total_online(),
            servers=len(bot.guilds),
            tokyo_time=get_tokyo_time()
        )
        activity = discord.Game(name=status_text)
        await bot.change_presence(status=discord.Status.dnd, activity=activity)

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    update_status.start()

bot.run(BOT_TOKEN)
