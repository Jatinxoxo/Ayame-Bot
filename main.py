import discord
from discord.ext import commands
import asyncio
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")


INITIAL_EXTENSIONS = [
    "cogs.post_commands",
    "cogs.autopost_commands",
    "cogs.category_commands"
]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync();
    await bot.change_presence(
        activity=discord.Streaming(
            name="AkariX",
            url="https://twitch.tv/Mommyvideos",  # replace with your Twitch
        )
    )
    print(f"✅ Logged in as {bot.user} and commands synced.")

async def main():
    async with bot:
        for ext in INITIAL_EXTENSIONS:
            try:
                await bot.load_extension(ext)
                print(f"🔄 Loaded extension: {ext}")
            except Exception as e:
                print(f"❌ Failed to load extension {ext}: {e}")
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
