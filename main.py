import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# Load .env file locally
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

# Event: on_ready
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Streaming(
            name="Serving YamiHime 🔞",
            url="https://twitch.tv/YOUR_CHANNEL"  # Replace with your actual or fake link
        )
    )
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} — Commands synced and streaming status set.")

# Main async startup
async def main():
    extensions = [
        "cogs.post_commands",
        "cogs.autopost_commands",
        "cogs.category_commands"
    ]

    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"🔄 Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load {ext}: {e}")

    await bot.start(BOT_TOKEN)

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())
