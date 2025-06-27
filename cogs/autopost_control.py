import discord
from discord import app_commands
from discord.ext import commands, tasks
from scraper import fetch_image, fetch_gif
from spankbang_fetcher import fetch_spankbang_video
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES
import asyncio

class AutoPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_autoposts = {
            "image": None,
            "gif": None,
            "clip": None
        }

    async def send_autopost(self, interaction, category, fetch_func, media_type):
        if self.active_autoposts[media_type]:
            await interaction.response.send_message(f"❌ An autopost for {media_type} is already running.", ephemeral=True)
            return

        self.active_autoposts[media_type] = interaction.user.id
        await interaction.response.send_message(f"▶️ Started autoposting {media_type}s for category: **{category}**")

        async def stop_button():
            class StopButton(discord.ui.View):
                @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.red)
                async def stop(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                    if self.active_autoposts[media_type] == interaction_button.user.id:
                        self.active_autoposts[media_type] = None
                        await interaction_button.response.send_message("⏹️ Autopost stopped.", ephemeral=True)
                        self.stop()

            return StopButton()

        view = await stop_button()

        while self.active_autoposts[media_type] == interaction.user.id:
            post = await fetch_func(category, interaction)
            if post:
                embed = discord.Embed(title=post["title"], url=post.get("url"), color=discord.Color.dark_purple())
                embed.set_image(url=post["thumbnail"] if media_type == "clip" else post["url"])
                await interaction.channel.send(embed=embed, view=view)
            else:
                await interaction.channel.send("⚠️ Failed to fetch content. Trying again in 12 seconds...")
            await asyncio.sleep(12)

    @app_commands.command(name="autopost_image", description="Auto-post NSFW images every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_image(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_IMAGE_CATEGORIES:
            await interaction.response.send_message("❌ Invalid image category.", ephemeral=True)
            return
        await self.send_autopost(interaction, category, fetch_image, "image")

    @app_commands.command(name="autopost_gif", description="Auto-post NSFW gifs every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_gif(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_GIF_CATEGORIES:
            await interaction.response.send_message("❌ Invalid gif category.", ephemeral=True)
            return
        await self.send_autopost(interaction, category, fetch_gif, "gif")

    @app_commands.command(name="autopost_clip", description="Auto-post NSFW video clips every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_clip(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_CLIP_CATEGORIES:
            await interaction.response.send_message("❌ Invalid clip category.", ephemeral=True)
            return
        await self.send_autopost(interaction, category, fetch_spankbang_video, "clip")

async def setup(bot):
    await bot.add_cog(AutoPost(bot))
