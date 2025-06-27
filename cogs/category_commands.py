import discord
from discord import app_commands
from discord.ext import commands
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES

class CategoryCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="list", description="List available NSFW categories for image, gif, and clip commands.")
    async def list_categories(self, interaction: discord.Interaction):
        image = ", ".join(NSFW_IMAGE_CATEGORIES)
        gif = ", ".join(NSFW_GIF_CATEGORIES)
        clip = ", ".join(NSFW_CLIP_CATEGORIES)

        embed = discord.Embed(title="📂 NSFW Content Categories", color=discord.Color.orange())
        embed.add_field(name="🖼️ Image Categories", value=image or "None", inline=False)
        embed.add_field(name="🎞️ GIF Categories", value=gif or "None", inline=False)
        embed.add_field(name="🎥 Clip Categories", value=clip or "None", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CategoryCommands(bot))
