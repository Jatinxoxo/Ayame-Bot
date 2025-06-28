import discord
from discord.ext import commands

class CategoryCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Future category-related utilities can be added here.

async def setup(bot):
    await bot.add_cog(CategoryCommands(bot))
