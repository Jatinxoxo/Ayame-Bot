# cogs/post_commands.py

import discord
from discord import app_commands
from discord.ext import commands
from scraper import fetch_image, fetch_gif
from eporner_fetcher import fetch_eporner_video
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES

class PostCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post_image", description="Post a single NSFW image from a chosen category.")
    @app_commands.describe(category="Choose a category")
    async def post_image(self, interaction: discord.Interaction, category: str):
        if not interaction.channel.is_nsfw():
            await interaction.response.send_message("🚫 This command can only be used in NSFW channels.", ephemeral=True)
            return

        if category not in NSFW_IMAGE_CATEGORIES:
            await interaction.response.send_message("❌ Invalid image category.", ephemeral=True)
            return

        await interaction.response.defer()
        post = await fetch_image(category)
        if post:
            embed = discord.Embed(title=post["title"], url=post["url"], color=discord.Color.magenta())
            embed.set_image(url=post["url"])
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("⚠️ Failed to fetch image.", delete_after=10)

    @app_commands.command(name="post_gif", description="Post a single NSFW gif from a chosen category.")
    @app_commands.describe(category="Choose a category")
    async def post_gif(self, interaction: discord.Interaction, category: str):
        if not interaction.channel.is_nsfw():
            await interaction.response.send_message("🚫 This command can only be used in NSFW channels.", ephemeral=True)
            return

        if category not in NSFW_GIF_CATEGORIES:
            await interaction.response.send_message("❌ Invalid gif category.", ephemeral=True)
            return

        await interaction.response.defer()
        post = await fetch_gif(category)
        if post:
            embed = discord.Embed(title=post["title"], url=post["url"], color=discord.Color.orange())
            embed.set_image(url=post["url"])
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("⚠️ Failed to fetch gif.", delete_after=10)

    @app_commands.command(name="post_clip", description="Post a full NSFW video from a chosen category.")
    @app_commands.describe(category="Choose a category")
    async def post_clip(self, interaction: discord.Interaction, category: str):
        if not interaction.channel.is_nsfw():
            await interaction.response.send_message("🚫 This command can only be used in NSFW channels.", ephemeral=True)
            return

        if category not in NSFW_CLIP_CATEGORIES:
            await interaction.response.send_message("❌ Invalid clip category.", ephemeral=True)
            return

        await interaction.response.defer()
        post = await fetch_eporner_video(category)
        if post:
            embed = discord.Embed(
                title=f"{post['title']} ({post['duration']} min)",
                url=post["url"],
                color=discord.Color.red()
            )

            video_url = post.get("url") or ""
            thumbnail_url = post.get("thumbnail") or "https://cdn.discordapp.com/embed/404.png"
            preview_url = video_url if video_url.endswith(".mp4") else thumbnail_url

            embed.set_image(url=preview_url)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("⚠️ Failed to fetch clip.", delete_after=10)

    @app_commands.command(name="list", description="List all available NSFW categories.")
    async def list_categories(self, interaction: discord.Interaction):
        image_cats = ", ".join(NSFW_IMAGE_CATEGORIES)
        gif_cats = ", ".join(NSFW_GIF_CATEGORIES)
        clip_cats = ", ".join(NSFW_CLIP_CATEGORIES)

        embed = discord.Embed(title="📂 NSFW Categories", color=discord.Color.blue())
        embed.add_field(name="🖼️ Images", value=image_cats or "None", inline=False)
        embed.add_field(name="🎞️ GIFs", value=gif_cats or "None", inline=False)
        embed.add_field(name="📹 Clips", value=clip_cats or "None", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(PostCommands(bot))
