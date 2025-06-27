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
            await self.stop_callback(interaction_button.guild.id, self.media_type)
            self.stop()

class AutopostStopView(discord.ui.View):
    def __init__(self, guild_id, active_types, stop_callback):
        super().__init__(timeout=30)
        self.guild_id = guild_id
        self.stop_callback = stop_callback
        self.active_types = active_types

        for media_type in active_types:
            label = f"⏹️ Stop {media_type.capitalize()}"
            self.add_item(discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.red,
                custom_id=f"stop_{media_type}"
            ))

        # Always include Stop All
        self.add_item(discord.ui.Button(
            label="🛑 Stop All",
            style=discord.ButtonStyle.blurple,
            custom_id="stop_all"
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        await interaction.response.defer(ephemeral=True)
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        await interaction.followup.send(f"❌ Error: {error}", ephemeral=True)

    async def on_interaction(self, interaction: discord.Interaction):
        try:
            cid = interaction.data.get("custom_id")
            if not cid:
                return

            if cid == "stop_all":
                for media_type in self.active_types:
                    await self.stop_callback(self.guild_id, media_type)
                await interaction.followup.send("✅ Stopped all autoposts in this server.", ephemeral=True)

            elif cid.startswith("stop_"):
                media_type = cid.replace("stop_", "")
                if media_type in self.active_types:
                    await self.stop_callback(self.guild_id, media_type)
                    await interaction.followup.send(f"✅ Stopped **{media_type}** autopost.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to stop autopost: {e}", ephemeral=True)

class AutoPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_autoposts = {}  # { guild_id: { "image": user_id, "gif": user_id, "clip": user_id } }

    async def stop_autopost(self, guild_id: int, media_type: str):
        if guild_id in self.active_autoposts:
            self.active_autoposts[guild_id][media_type] = None

    async def send_autopost(self, interaction, category, fetch_func, media_type):
        guild_id = interaction.guild.id

        if guild_id not in self.active_autoposts:
            self.active_autoposts[guild_id] = {
                "image": None,
                "gif": None,
                "clip": None
            }

        if self.active_autoposts[guild_id][media_type]:
            await interaction.response.send_message(f"❌ An autopost for {media_type} is already running in this server.", ephemeral=True)
            return

        self.active_autoposts[guild_id][media_type] = interaction.user.id
        await interaction.response.send_message(f"▶️ Started autoposting {media_type}s for category: **{category}**")

        while self.active_autoposts[guild_id][media_type] == interaction.user.id:
            post = await fetch_func(category)
            if post:
                embed = discord.Embed(title=post["title"], url=post.get("url"), color=discord.Color.dark_purple())
                embed.set_image(url=post["thumbnail"] if media_type == "clip" else post["url"])
                view = StopButton(media_type, interaction.user.id, self.stop_autopost)
                await interaction.channel.send(embed=embed, view=view)
            else:
                await interaction.channel.send("⚠️ Failed to fetch content. Trying again in 12 seconds...")
            await asyncio.sleep(12)

    def is_nsfw_channel(self, interaction: discord.Interaction) -> bool:
        return isinstance(interaction.channel, discord.TextChannel) and interaction.channel.is_nsfw()

    @app_commands.command(name="autopost_image", description="Auto-post NSFW images every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_image(self, interaction: discord.Interaction, category: str):
        if not self.is_nsfw_channel(interaction):
            await interaction.response.send_message("❌ You can only use this command in NSFW channels.", ephemeral=True)
            return
        if category not in NSFW_IMAGE_CATEGORIES:
            await interaction.response.send_message("❌ Invalid image category.", ephemeral=True)
            return
        asyncio.create_task(self.send_autopost(interaction, category, fetch_image, "image"))

    @app_commands.command(name="autopost_gif", description="Auto-post NSFW gifs every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_gif(self, interaction: discord.Interaction, category: str):
        if not self.is_nsfw_channel(interaction):
            await interaction.response.send_message("❌ You can only use this command in NSFW channels.", ephemeral=True)
            return
        if category not in NSFW_GIF_CATEGORIES:
            await interaction.response.send_message("❌ Invalid gif category.", ephemeral=True)
            return
        asyncio.create_task(self.send_autopost(interaction, category, fetch_gif, "gif"))

    @app_commands.command(name="autopost_clip", description="Auto-post NSFW video clips every 12 seconds.")
    @app_commands.describe(category="Choose a category")
    async def autopost_clip(self, interaction: discord.Interaction, category: str):
        if not self.is_nsfw_channel(interaction):
            await interaction.response.send_message("❌ You can only use this command in NSFW channels.", ephemeral=True)
            return
        if category not in NSFW_CLIP_CATEGORIES:
            await interaction.response.send_message("❌ Invalid clip category.", ephemeral=True)
            return
        asyncio.create_task(self.send_autopost(interaction, category, fetch_spankbang_video, "clip"))

    @app_commands.command(name="stop_autopost", description="Stop running autoposts in this server.")
    async def stop_autopost(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.active_autoposts:
            await interaction.response.send_message("ℹ️ No autoposts are running in this server.", ephemeral=True)
            return

        running = [
            media_type
            for media_type, user_id in self.active_autoposts[guild_id].items()
            if user_id is not None
        ]

        if not running:
            await interaction.response.send_message("ℹ️ No autoposts are currently running in this server.", ephemeral=True)
            return

        embed = discord.Embed(
            title="⏹️ Stop Autopost",
            description="Select which autoposts you want to stop:",
            color=discord.Color.red()
        )
        view = AutopostStopView(guild_id, running, self.stop_autopost)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoPost(bot))
