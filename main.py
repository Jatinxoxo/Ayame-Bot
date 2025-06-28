import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables (required for local testing only)
load_dotenv()

# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Set status (Streaming)
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    activity = discord.Streaming(name="Taming Servers", url="https://twitch.tv/yamihime")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)

# Load all cog extensions
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

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())
