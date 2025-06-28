import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv  # Add this import

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

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    activity = discord.Streaming(name="Taming Servers", url="https://twitch.tv/yamihime")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)

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
