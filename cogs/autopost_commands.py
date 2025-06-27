import discord
from discord import app_commands
from discord.ext import commands
from scraper import fetch_image, fetch_gif
from spankbang_fetcher import fetch_spankbang_video
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES
import asyncio

class StopButton(discord.ui.View):
    def __init__(self, guild_id, media_type):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.media_type = media_type
        self.add_item(discord.ui.Button(label="⏹️ Stop", style=discord.ButtonStyle.red, custom_id=f"stop:{media_type}:{guild_id}"))

class AutoPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_autoposts = {}  # { guild_id: { media_type: True/False } }
        self.bot.add_view(self.get_stop_view("image", 0))  # pre-register persistent StopButton views
        self.bot.add_view(self.get_stop_view("gif", 0))
        self.bot.add_view(self.get_stop_view("clip", 0))

    def get_stop_view(self, media_type, guild_id):
        return StopButton(guild_id, media_type)

    async def stop_media_autopost(self, guild_id: int, media_type: str):
        if guild_id in self.active_autoposts:
            self.active_autoposts[guild_id][media_type] = False

    def is_nsfw_channel(self, interaction: discord.Interaction) -> bool:
        return isinstance(interaction.channel, discord.TextChannel) and interaction.channel.is_nsfw()

    async def send_autopost(self, interaction, category, fetch_func, media_type):
        guild_id = interaction.guild.id

        if not self.active_autoposts.get(guild_id):
            self.active_autoposts[guild_id] = {"image": False, "gif": False, "clip": False}

        if self.active_autoposts[guild_id][media_type]:
            await interaction.response.send_message(f"❌ {media_type.capitalize()} autopost is already running in this server.", ephemeral=True)
            return

        self.active_autoposts[guild_id][media_type] = True
        await interaction.response.send_message(f"▶️ Started autoposting **{media_type}s** for category: **{category}**")

        failures = 0
        while self.active_autoposts[guild_id][media_type]:
            post = await fetch_func(category)
            if post:
                failures = 0
                embed = discord.Embed(title=post.get("title", media_type.title()), url=post.get("url"), color=discord.Color.dark_purple())
                embed.set_image(url=post["thumbnail"] if media_type == "clip" else post["url"])
                view = StopButton(guild_id, media_type)
                await interaction.channel.send(embed=embed, view=view)
            else:
                failures += 1
                await interaction.channel.send("⚠️ Failed to fetch content. Retrying in 12 seconds...")

                if failures >= 3:
                    await interaction.channel.send(f"⚠️ Multiple failed fetches for {media_type}. Attempting to restart...")
                    self.active_autoposts[guild_id][media_type] = False
                    await asyncio.sleep(5)
                    self.active_autoposts[guild_id][media_type] = True
                    failures = 0

                await asyncio.sleep(12)

    @app_commands.command(name="autopost_image", description="Auto-post NSFW images every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_image(self, interaction: discord.Interaction, category: str):
        if not self.is_nsfw_channel(interaction):
            await interaction.response.send_message("❌ This command can only be used in NSFW channels.", ephemeral=True)
            return
        if category not in NSFW_IMAGE_CATEGORIES:
            await interaction.response.send_message("❌ Invalid image category.", ephemeral=True)
            return
        asyncio.create_task(self.send_autopost(interaction, category, fetch_image, "image"))

    @app_commands.command(name="autopost_gif", description="Auto-post NSFW gifs every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_gif(self, interaction: discord.Interaction, category: str):
        if not self.is_nsfw_channel(interaction):
            await interaction.response.send_message("❌ This command can only be used in NSFW channels.", ephemeral=True)
            return
        if category not in NSFW_GIF_CATEGORIES:
            await interaction.response.send_message("❌ Invalid gif category.", ephemeral=True)
            return
        asyncio.create_task(self.send_autopost(interaction, category, fetch_gif, "gif"))

    @app_commands.command(name="autopost_clip", description="Auto-post NSFW video clips every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_clip(self, interaction: discord.Interaction, category: str):
        if not self.is_nsfw_channel(interaction):
            await interaction.response.send_message("❌ This command can only be used in NSFW channels.", ephemeral=True)
            return
        if category not in NSFW_CLIP_CATEGORIES:
            await interaction.response.send_message("❌ Invalid clip category.", ephemeral=True)
            return
        asyncio.create_task(self.send_autopost(interaction, category, fetch_spankbang_video, "clip"))

    @app_commands.command(name="stop_autopost", description="Stop all running autoposts in this server.")
    async def stop_autopost(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.active_autoposts or not any(self.active_autoposts[guild_id].values()):
            await interaction.response.send_message("ℹ️ No autoposts are currently running in this server.", ephemeral=True)
            return

        for media_type in ["image", "gif", "clip"]:
            self.active_autoposts[guild_id][media_type] = False

        await interaction.response.send_message("🛑 All autoposts have been stopped for this server.", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.type == discord.InteractionType.component:
            return

        if interaction.data.get("custom_id", "").startswith("stop:"):
            try:
                parts = interaction.data["custom_id"].split(":")
                media_type = parts[1]
                guild_id = int(parts[2])
                await self.stop_media_autopost(guild_id, media_type)
                await interaction.response.send_message(f"✅ Stopped autoposting **{media_type}**.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to stop autopost: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoPost(bot))
