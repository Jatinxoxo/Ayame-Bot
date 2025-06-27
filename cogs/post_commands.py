import discord
from discord import app_commands
from discord.ext import commands
from scraper import fetch_image, fetch_gif
from spankbang_fetcher import fetch_spankbang_video
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES

class PostCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post_image", description="Post a random NSFW image from a selected category.")
    @app_commands.describe(category="Choose a category")
    async def post_image(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_IMAGE_CATEGORIES:
            await interaction.response.send_message("❌ Invalid image category.", ephemeral=True)
            return

        await interaction.response.defer()
        post = await fetch_image(category)
        if not post:
            await interaction.followup.send("❌ No image found.")
            return

        embed = discord.Embed(title=post["title"], color=discord.Color.dark_purple())
        embed.set_image(url=post["url"])
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="post_gif", description="Post a random NSFW gif from a selected category.")
    @app_commands.describe(category="Choose a category")
    async def post_gif(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_GIF_CATEGORIES:
            await interaction.response.send_message("❌ Invalid gif category.", ephemeral=True)
            return

        await interaction.response.defer()
        post = await fetch_gif(category)
        if not post:
            await interaction.followup.send("❌ No gif found.")
            return

        embed = discord.Embed(title=post["title"], color=discord.Color.dark_purple())
        embed.set_image(url=post["url"])
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="post_clip", description="Post a random NSFW video clip from a selected category.")
    @app_commands.describe(category="Choose a category")
    async def post_clip(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_CLIP_CATEGORIES:
            await interaction.response.send_message("❌ Invalid clip category.", ephemeral=True)
            return

        await interaction.response.defer()
        post = await fetch_spankbang_video(category)
        if not post:
            await interaction.followup.send("❌ No clip found. It may have timed out or returned no content.")
            return

        embed = discord.Embed(title=post["title"], url=post["url"], color=discord.Color.dark_purple())
        embed.set_image(url=post["thumbnail"])
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PostCommands(bot))
