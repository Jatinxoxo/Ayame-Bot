import os
import asyncio
import discord
import random
from discord.ext import commands, tasks
from dotenv import load_dotenv
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

# Year-round cozy vibes
base_statuses = [
    "🍙 eating mochi",
    "📺 watching anime",
    "🍵 sipping matcha",
    "🍜 slurping ramen",
    "🧸 cuddling plushies",
    "🐾 chasing butterflies",
    "🌸 under the sakura",
    "🎐 wind chime dreams",
    "📚 reading manga",
    "🛌 cozy kotatsu time"
]

def get_seasonal_statuses():
    month = datetime.utcnow().month
    if month in [12, 1, 2]:
        return ["⛄ building snow bunnies", "🎄 decorating bonsai"]
    elif month in [3, 4, 5]:
        return ["🌸 hanami picnic", "🎏 flying koinobori"]
    elif month in [6, 7, 8]:
        return ["🎆 watching fireworks", "🍉 eating watermelon"]
    elif month in [9, 10, 11]:
        return ["🍁 leaf peeping in Kyoto", "🎃 carving pumpkins"]
    return []

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    rotate_status.start()

@tasks.loop(seconds=60)
async def rotate_status():
    all_statuses = base_statuses + get_seasonal_statuses()
    status = random.choice(all_statuses)
    activity = discord.Activity(type=discord.ActivityType.watching, name=status)
    await bot.change_presence(status=discord.Status.online, activity=activity)

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
