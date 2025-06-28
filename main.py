import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load .env file in local development (safe for Railway too)
load_dotenv()

# Token pulled from environment variable
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# List of cog extensions to load
INITIAL_EXTENSIONS = [
    "cogs.post_commands",
    "cogs.autopost_commands",
    "cogs.category_commands"
]

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# When bot is ready
@bot.event
async def on_ready():
    await bot.tree.sync()

    # Register persistent views
    from cogs.autopost_commands import StopButton
    for media_type in ["image", "gif", "clip"]:
        bot.add_view(StopButton(guild_id=0, media_type=media_type))

    await bot.change_presence(
        activity=discord.Streaming(
            name="touch me with your prefix!",
            url="https://twitch.tv/Mommyvideos",  # Replace with actual stream
        )
    )
    print(f"✅ Logged in as {bot.user} and commands synced.")


# Main async loop
async def main():
    async with bot:
        for ext in INITIAL_EXTENSIONS:
            try:
                await bot.load_extension(ext)
                print(f"🔄 Loaded extension: {ext}")
            except Exception as e:
                print(f"❌ Failed to load extension {ext}: {e}")
        await bot.start(BOT_TOKEN)

# Entry point
if __name__ == "__main__":
    if BOT_TOKEN is None:
        raise RuntimeError("❌ DISCORD_TOKEN is not set in environment variables.")
    asyncio.run(main())
