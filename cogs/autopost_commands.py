# cogs/autopost_commands.py

import discord
from discord import app_commands
from discord.ext import commands
from scraper import fetch_image, fetch_gif
from eporner_fetcher import fetch_eporner_video
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES

class AutoPostButton(discord.ui.View):
    def __init__(self, media_type: str, category: str, user_id: int, fetch_func):
        super().__init__(timeout=180)  # View expires in 3 minutes
        self.media_type = media_type
        self.category = category
        self.user_id = user_id
        self.fetch_func = fetch_func

    @discord.ui.button(label="⟳", style=discord.ButtonStyle.blurple)
    async def next(self, interaction_button: discord.Interaction, button: discord.ui.Button):
        if interaction_button.user.id != self.user_id:
            await interaction_button.response.send_message("❌ Only the user who started the autopost can fetch the next content.", ephemeral=True)
            return

        await interaction_button.response.defer(thinking=False)  # Prevents "interaction failed" message

        post = await self.fetch_func(self.category)
        if not post:
            await interaction_button.followup.send("⚠️ Failed to fetch content. Try again.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{post.get('title')} ({post.get('duration', 'N/A')} min)" if self.media_type == "clip" else post.get("title"),
            url=post.get("url"),
            color=discord.Color.dark_purple()
        )

        preview_url = (
            post["url"] if self.media_type == "clip" and post["url"].endswith(".mp4")
            else post.get("thumbnail") or "https://cdn.discordapp.com/embed/404.png"
        ) if self.media_type == "clip" else post["url"]

        embed.set_image(url=preview_url)
        await interaction_button.channel.send(embed=embed, view=self)


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
        await interaction.followup.send(f"▶️ Manual post enabled for **{media_type}** category: **{category}**", ephemeral=True)

        view = AutoPostButton(media_type, category, interaction.user.id, fetch_func)
        await interaction.channel.send(content=f"🖱️ Click ⟳ to post the next **{media_type}** from **{category}**", view=view)

    @app_commands.command(name="autopost_image", description="Auto-post NSFW images (click to fetch next).")
    @app_commands.describe(category="Choose a category")
    async def autopost_image(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_IMAGE_CATEGORIES:
            await interaction.response.send_message("❌ Invalid image category.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self.send_autopost(interaction, category, fetch_image, "image")

    @app_commands.command(name="autopost_gif", description="Auto-post NSFW gifs (click to fetch next).")
    @app_commands.describe(category="Choose a category")
    async def autopost_gif(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_GIF_CATEGORIES:
            await interaction.response.send_message("❌ Invalid gif category.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self.send_autopost(interaction, category, fetch_gif, "gif")

    @app_commands.command(name="autopost_clip", description="Auto-post NSFW full videos (click to fetch next).")
    @app_commands.describe(category="Choose a category")
    async def autopost_clip(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_CLIP_CATEGORIES:
            await interaction.response.send_message("❌ Invalid clip category.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self.send_autopost(interaction, category, fetch_eporner_video, "clip")

async def setup(bot):
    await bot.add_cog(AutoPost(bot))
