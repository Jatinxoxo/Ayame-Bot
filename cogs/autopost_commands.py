import discord
from discord import app_commands
from discord.ext import commands
from scraper import fetch_image, fetch_gif
from spankbang_fetcher import fetch_spankbang_video
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES
import asyncio

class StopButton(discord.ui.View):
    def __init__(self, media_type, user_id, stop_callback):
        super().__init__(timeout=None)
        self.media_type = media_type
        self.user_id = user_id
        self.stop_callback = stop_callback

    @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction_button: discord.Interaction, button: discord.ui.Button):
        if interaction_button.user.id == self.user_id:
            await self.stop_callback(interaction_button, self.media_type)
            self.stop()

class AutoPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 🆕 Now tracking active autoposts per guild
        self.active_autoposts = {
            "image": {},
            "gif": {},
            "clip": {}
        }

    async def stop_autopost(self, interaction: discord.Interaction, media_type: str):
        self.active_autoposts[media_type].pop(interaction.guild.id, None)
        await interaction.response.send_message("⏹️ Autopost stopped in this server.", ephemeral=True)

    async def send_autopost(self, interaction, category, fetch_func, media_type):
        if interaction.guild.id in self.active_autoposts[media_type]:
            await interaction.response.send_message(f"❌ An autopost for {media_type} is already running in this server.", ephemeral=True)
            return

        self.active_autoposts[media_type][interaction.guild.id] = interaction.user.id
        await interaction.response.send_message(f"▶️ Started autoposting {media_type}s for category: **{category}**")

        while self.active_autoposts[media_type].get(interaction.guild.id) == interaction.user.id:
            post = await fetch_func(category)
            if post:
                embed = discord.Embed(title=post["title"], url=post.get("url"), color=discord.Color.dark_purple())
                embed.set_image(url=post["thumbnail"] if media_type == "clip" else post["url"])

                if media_type == "clip":
                    view = StopButton(media_type, interaction.user.id, self.stop_autopost)
                    await interaction.channel.send(embed=embed, view=view)
                else:
                    await interaction.channel.send(embed=embed)
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

    @app_commands.command(name="stopall", description="Stop all your active autoposts in this server.")
    async def stop_all(self, interaction: discord.Interaction):
        stopped_any = False
        for media_type in self.active_autoposts:
            if interaction.guild.id in self.active_autoposts[media_type]:
                self.active_autoposts[media_type].pop(interaction.guild.id, None)
                stopped_any = True

        if stopped_any:
            await interaction.response.send_message("✅ All active autoposts in this server have been stopped.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ No active autoposts are running in this server.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoPost(bot))
