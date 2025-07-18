import os
import asyncio
import discord
from discord.ext import commands, tasks  # ✅ Fixed: imported tasks
from dotenv import load_dotenv
import itertools

# Load .env file (for local development)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Please set it in your environment or Railway dashboard.")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Placeholder for messages to rotate
status_messages = itertools.cycle([])

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    update_status_messages()
    update_presence.start()

def update_status_messages():
    guild = discord.utils.get(bot.guilds)
    if not guild:
        return

    total = guild.member_count
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    boosts = guild.premium_subscription_count
    tier = guild.premium_tier

    global status_messages
    status_messages = itertools.cycle([
        f"🌸 Blossoming with {total} petals",
        f"✨ {online} kawaii souls online",
        f"🔮 Boosted by {boosts} stars",
        f"🌌 Yugen Orb: Tier {tier} ascension",
        f"🎐 Watching the realm grow...",
        f"🍥 Breathing with {total} members",
        f"🎴 {online} ninjas meditating now"
    ])

@tasks.loop(seconds=60)
async def update_presence():
    try:
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
