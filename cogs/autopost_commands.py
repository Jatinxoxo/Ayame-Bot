# cogs/autopost_commands.py

import discord
from discord import app_commands
from discord.ext import commands
from scraper import fetch_image, fetch_gif
from eporner_fetcher import fetch_eporner_video
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES
import asyncio

class StopButton(discord.ui.View):
    def __init__(self, media_type: str, user_id: int, stop_callback):
        super().__init__(timeout=180)  # View expires in 3 minutes
        self.media_type = media_type
        self.user_id = user_id
        self.stop_callback = stop_callback

    @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction_button: discord.Interaction, button: discord.ui.Button):
        if interaction_button.user.id != self.user_id:
            await interaction_button.response.send_message("❌ Only the user who started the autopost can stop it.", ephemeral=True)
            return

        await self.stop_callback(interaction_button, self.media_type)
        await interaction_button.response.send_message(f"⏹️ Autopost for **{self.media_type}** stopped in this channel.", ephemeral=True)
        self.stop()

class AutoPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_autoposts = {
            "image": {},
            "gif": {},
            "clip": {}
        }

    async def stop_autopost(self, interaction: discord.Interaction, media_type: str):
        self.active_autoposts[media_type].pop(interaction.channel.id, None)

    async def send_autopost(self, interaction, category, fetch_func, media_type: str):
        channel_id = interaction.channel.id

        if not interaction.channel.is_nsfw():
            await interaction.followup.send("🚫 This command can only be used in NSFW channels.", ephemeral=True)
            return

        if channel_id in self.active_autoposts[media_type]:
            await interaction.followup.send(f"❌ An autopost for {media_type} is already running in this channel.", ephemeral=True)
            return

        self.active_autoposts[media_type][channel_id] = interaction.user.id
        await interaction.followup.send(f"▶️ Started autoposting {media_type}s for category: **{category}**", ephemeral=True)

        while channel_id in self.active_autoposts[media_type]:
            post = await fetch_func(category)
            if post:
                embed = discord.Embed(
                    title=f"{post.get('title')} ({post.get('duration', 'N/A')} min)" if media_type == "clip" else post.get("title"),
                    url=post.get("url"),
                    color=discord.Color.dark_purple()
                )

                preview_url = (
                    post["url"] if media_type == "clip" and post["url"].endswith(".mp4")
                    else post.get("thumbnail") or "https://cdn.discordapp.com/embed/404.png"
                ) if media_type == "clip" else post["url"]

                embed.set_image(url=preview_url)
                view = StopButton(media_type, interaction.user.id, self.stop_autopost)

                await interaction.channel.send(embed=embed, view=view, delete_after=300)
            else:
                await interaction.channel.send(
                    "⚠️ Failed to fetch content. Trying again in 12 seconds...",
                    delete_after=10
                )

            await asyncio.sleep(12)

    @app_commands.command(name="autopost_image", description="Auto-post NSFW images every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_image(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_IMAGE_CATEGORIES:
            await interaction.response.send_message("❌ Invalid image category.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self.send_autopost(interaction, category, fetch_image, "image")

    @app_commands.command(name="autopost_gif", description="Auto-post NSFW gifs every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_gif(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_GIF_CATEGORIES:
            await interaction.response.send_message("❌ Invalid gif category.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self.send_autopost(interaction, category, fetch_gif, "gif")

    @app_commands.command(name="autopost_clip", description="Auto-post NSFW full videos every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_clip(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_CLIP_CATEGORIES:
            await interaction.response.send_message("❌ Invalid clip category.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self.send_autopost(interaction, category, fetch_eporner_video, "clip")

async def setup(bot):
    await bot.add_cog(AutoPost(bot))
