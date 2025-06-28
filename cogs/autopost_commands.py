import discord
from discord import app_commands
from discord.ext import commands
from scraper import fetch_image, fetch_gif
from spankbang_fetcher import fetch_spankbang_video
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES
import asyncio
import logging

class AutoPostControls(discord.ui.View):
    def __init__(self, media_type: str, user_id: int, guild_id: int, cog_instance):
        super().__init__(timeout=300)  # 5 minute timeout
        self.media_type = media_type
        self.user_id = user_id
        self.guild_id = guild_id
        self.cog = cog_instance

    @discord.ui.button(label="⏹️ Stop AutoPost", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_autopost(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has permission to stop
        if interaction.user.id != self.user_id and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You don't have permission to stop this autopost.", ephemeral=True)
            return
        
        # Stop the autopost
        success = await self.cog.stop_autopost_by_type(self.guild_id, self.media_type, interaction.user.id)
        
        if success:
            # Disable all buttons in this view
            for item in self.children:
                item.disabled = True
            
            embed = discord.Embed(
                title="⏹️ AutoPost Stopped",
                description=f"**{self.media_type.title()}** autopost has been stopped.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ AutoPost was already stopped or not found.", ephemeral=True)

    @discord.ui.button(label="📊 Status", style=discord.ButtonStyle.secondary, emoji="📊")
    async def show_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        active_posts = self.cog.get_active_autoposts(self.guild_id)
        
        if not active_posts:
            status_msg = "No active autoposts in this server."
        else:
            status_lines = []
            for media_type, user_id in active_posts.items():
                user = interaction.guild.get_member(user_id)
                username = user.display_name if user else f"User ID: {user_id}"
                status_lines.append(f"• **{media_type.title()}**: Started by {username}")
            status_msg = "\n".join(status_lines)
        
        embed = discord.Embed(
            title="📊 AutoPost Status",
            description=status_msg,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AutoPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_autoposts = {
            "image": {},
            "gif": {},
            "clip": {}
        }
        self.retry_counts = {}  # Track retry attempts per guild/media type

    def get_active_autoposts(self, guild_id: int) -> dict:
        """Get all active autoposts for a guild"""
        active = {}
        for media_type, guilds in self.active_autoposts.items():
            if guild_id in guilds:
                active[media_type] = guilds[guild_id]
        return active

    async def stop_autopost_by_type(self, guild_id: int, media_type: str, user_id: int = None) -> bool:
        """Stop autopost by type. Returns True if stopped, False if not found."""
        if guild_id in self.active_autoposts[media_type]:
            # If user_id is provided, only stop if it matches (unless user has manage permissions)
            current_user = self.active_autoposts[media_type][guild_id]
            
            self.active_autoposts[media_type].pop(guild_id, None)
            
            # Clear retry count
            retry_key = f"{guild_id}_{media_type}"
            self.retry_counts.pop(retry_key, None)
            
            return True
        return False

    async def send_autopost(self, interaction: discord.Interaction, category: str, fetch_func, media_type: str):
        """Main autopost logic with improved error handling"""
        
        # Check if autopost is already running
        if interaction.guild.id in self.active_autoposts[media_type]:
            current_user = self.active_autoposts[media_type][interaction.guild.id]
            user = interaction.guild.get_member(current_user)
            username = user.display_name if user else f"User ID: {current_user}"
            
            embed = discord.Embed(
                title="❌ AutoPost Already Running",
                description=f"A **{media_type}** autopost is already active in this server.\nStarted by: **{username}**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Start autopost
        self.active_autoposts[media_type][interaction.guild.id] = interaction.user.id
        retry_key = f"{interaction.guild.id}_{media_type}"
        self.retry_counts[retry_key] = 0
        
        # Send confirmation with controls
        embed = discord.Embed(
            title="▶️ AutoPost Started",
            description=f"**Category**: {category}\n**Type**: {media_type.title()}\n**Interval**: 12 seconds",
            color=discord.Color.green()
        )
        embed.set_footer(text="Use the buttons below to control this autopost")
        
        view = AutoPostControls(media_type, interaction.user.id, interaction.guild.id, self)
        await interaction.response.send_message(embed=embed, view=view)

        # Main autopost loop
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while self.active_autoposts[media_type].get(interaction.guild.id) == interaction.user.id:
            try:
                post = await fetch_func(category)
                
                if post:
                    # Reset failure counter on success
                    consecutive_failures = 0
                    self.retry_counts[retry_key] = 0
                    
                    # Create embed based on media type
                    embed = discord.Embed(
                        title=post.get("title", "Content"),
                        color=discord.Color.dark_purple()
                    )
                    
                    if media_type == "clip":
                        embed.set_image(url=post.get("thumbnail", ""))
                        if post.get("url"):
                            embed.url = post["url"]
                    else:
                        embed.set_image(url=post.get("url", ""))
                    
                    await interaction.followup.send(embed=embed)
                    
                else:
                    # Handle fetch failure
                    consecutive_failures += 1
                    self.retry_counts[retry_key] = self.retry_counts.get(retry_key, 0) + 1
                    
                    if consecutive_failures >= max_consecutive_failures:
                        # Stop autopost after too many failures
                        embed = discord.Embed(
                            title="⚠️ AutoPost Stopped",
                            description=f"Stopped due to {max_consecutive_failures} consecutive failures.\nCategory may be unavailable.",
                            color=discord.Color.orange()
                        )
                        await interaction.followup.send(embed=embed)
                        break
                    else:
                        # Temporary failure message
                        failure_embed = discord.Embed(
                            title="⚠️ Fetch Failed",
                            description=f"Retrying... ({consecutive_failures}/{max_consecutive_failures})",
                            color=discord.Color.orange()
                        )
                        msg = await interaction.followup.send(embed=failure_embed)
                        
                        # Delete the failure message after 8 seconds
                        await asyncio.sleep(8)
                        try:
                            await msg.delete()
                        except discord.NotFound:
                            pass
                        
                        # Wait remaining time (12 - 8 = 4 seconds)
                        await asyncio.sleep(4)
                        continue

            except Exception as e:
                logging.error(f"AutoPost error in guild {interaction.guild.id}: {e}")
                consecutive_failures += 1
                
                if consecutive_failures >= max_consecutive_failures:
                    error_embed = discord.Embed(
                        title="❌ AutoPost Error",
                        description="Stopped due to repeated errors.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=error_embed)
                    break

            # Wait for next iteration
            await asyncio.sleep(12)

        # Clean up when loop ends
        self.active_autoposts[media_type].pop(interaction.guild.id, None)
        self.retry_counts.pop(retry_key, None)

    @app_commands.command(name="autopost_image", description="Auto-post images every 12 seconds")
    @app_commands.describe(category="Choose a category")
    async def autopost_image(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_IMAGE_CATEGORIES:
            available = ", ".join(NSFW_IMAGE_CATEGORIES[:5])  # Show first 5
            embed = discord.Embed(
                title="❌ Invalid Category",
                description=f"Available categories: {available}...",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await self.send_autopost(interaction, category, fetch_image, "image")

    @app_commands.command(name="autopost_gif", description="Auto-post GIFs every 12 seconds")
    @app_commands.describe(category="Choose a category")
    async def autopost_gif(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_GIF_CATEGORIES:
            available = ", ".join(NSFW_GIF_CATEGORIES[:5])  # Show first 5
            embed = discord.Embed(
                title="❌ Invalid Category",
                description=f"Available categories: {available}...",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await self.send_autopost(interaction, category, fetch_gif, "gif")

    @app_commands.command(name="autopost_clip", description="Auto-post video clips every 12 seconds")
    @app_commands.describe(category="Choose a category")
    async def autopost_clip(self, interaction: discord.Interaction, category: str):
        if category not in NSFW_CLIP_CATEGORIES:
            available = ", ".join(NSFW_CLIP_CATEGORIES[:5])  # Show first 5
            embed = discord.Embed(
                title="❌ Invalid Category",
                description=f"Available categories: {available}...",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await self.send_autopost(interaction, category, fetch_spankbang_video, "clip")

    @app_commands.command(name="stopall", description="Stop all active autoposts in this server")
    async def stop_all(self, interaction: discord.Interaction):
        stopped_types = []
        
        for media_type in self.active_autoposts:
            if interaction.guild.id in self.active_autoposts[media_type]:
                current_user = self.active_autoposts[media_type][interaction.guild.id]
                
                # Allow stopping if user is the owner or has manage permissions
                if (interaction.user.id == current_user or 
                    interaction.user.guild_permissions.manage_messages):
                    
                    self.active_autoposts[media_type].pop(interaction.guild.id, None)
                    stopped_types.append(media_type)

        if stopped_types:
            types_str = ", ".join([t.title() for t in stopped_types])
            embed = discord.Embed(
                title="✅ AutoPosts Stopped",
                description=f"Stopped: **{types_str}**",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="⚠️ No AutoPosts Found",
                description="No active autoposts to stop in this server.",
                color=discord.Color.orange()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="autopost_status", description="Check active autoposts in this server")
    async def autopost_status(self, interaction: discord.Interaction):
        active_posts = self.get_active_autoposts(interaction.guild.id)
        
        if not active_posts:
            embed = discord.Embed(
                title="📊 AutoPost Status",
                description="No active autoposts in this server.",
                color=discord.Color.blue()
            )
        else:
            status_lines = []
            for media_type, user_id in active_posts.items():
                user = interaction.guild.get_member(user_id)
                username = user.display_name if user else f"User ID: {user_id}"
                retry_key = f"{interaction.guild.id}_{media_type}"
                retry_count = self.retry_counts.get(retry_key, 0)
                
                status_line = f"• **{media_type.title()}**: {username}"
                if retry_count > 0:
                    status_line += f" ⚠️ ({retry_count} retries)"
                status_lines.append(status_line)
            
            embed = discord.Embed(
                title="📊 AutoPost Status",
                description="\n".join(status_lines),
                color=discord.Color.green()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoPost(bot))