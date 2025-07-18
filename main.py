import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import itertools

# Load environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing!")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # ✅ Needed for member stats

bot = commands.Bot(command_prefix="!", intents=intents)

status_messages = itertools.cycle([])

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.wait_until_ready()  # ✅ Ensure cache is ready
    update_status_messages()
    update_presence.start()

def update_status_messages():
    total_members = 0
    online_members = 0
    total_boosts = 0
    highest_tier = 0

    for guild in bot.guilds:
        total_members += guild.member_count or 0
        online_members += sum(1 for m in guild.members if m.status != discord.Status.offline)
        total_boosts += guild.premium_subscription_count or 0
        highest_tier = max(highest_tier, guild.premium_tier)

    global status_messages
    status_messages = itertools.cycle([
        f"🌸 Blossoming with {total_members} petals",
        f"✨ {online_members} kawaii souls online",
        f"🔮 Boosted by {total_boosts} stars",
        f"🌌 Highest Guild Tier: {highest_tier}",
        f"🎐 Watching the multiverse grow...",
        f"🍥 Across {len(bot.guilds)} guilds!",
        f"🎴 {online_members} ninjas meditating"
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
