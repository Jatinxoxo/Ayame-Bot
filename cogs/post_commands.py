import discord
from discord import app_commands
from discord.ext import commands
from scraper import fetch_image, fetch_gif
from spankbang_fetcher import fetch_spankbang_video
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES
import asyncio
import logging

class PostControls(discord.ui.View):
    def __init__(self, category: str, media_type: str, user_id: int, cog_instance):
        super().__init__(timeout=120)  # 2 minute timeout
        self.category = category
        self.media_type = media_type
        self.user_id = user_id
        self.cog = cog_instance
        self.is_fetching = False

    @discord.ui.button(label="🔄 New Post", style=discord.ButtonStyle.primary, emoji="🔄")
    async def fetch_new(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if already fetching to prevent spam
        if self.is_fetching:
            await interaction.response.send_message("⏳ Already fetching new content...", ephemeral=True)
            return
        
        # Allow anyone to fetch new content (not just original user)
        self.is_fetching = True
        
        # Update button to show loading
        button.disabled = True
        button.label = "⏳ Fetching..."
        await interaction.response.edit_message(view=self)
        
        try:
            # Fetch new content based on media type
            if self.media_type == "image":
                post = await fetch_image(self.category)
            elif self.media_type == "gif":
                post = await fetch_gif(self.category)
            elif self.media_type == "clip":
                post = await fetch_spankbang_video(self.category)
            else:
                post = None
            
            if post:
                # Create new embed
                color_map = {
                    "image": discord.Color.magenta(),
                    "gif": discord.Color.orange(),
                    "clip": discord.Color.red()
                }
                
                embed = discord.Embed(
                    title=post.get("title", f"New {self.media_type.title()}"),
                    color=color_map.get(self.media_type, discord.Color.blue())
                )
                
                if self.media_type == "clip":
                    embed.set_image(url=post.get("thumbnail", ""))
                    if post.get("url"):
                        embed.url = post["url"]
                        embed.add_field(name="🔗 Video Link", value=f"[Click here]({post['url']})", inline=False)
                else:
                    embed.set_image(url=post.get("url", ""))
                    if post.get("url"):
                        embed.url = post["url"]
                
                embed.set_footer(text=f"Category: {self.category} | Type: {self.media_type.title()}")
                
                # Reset button and update message
                button.disabled = False
                button.label = "🔄 New Post"
                
                await interaction.edit_original_response(embed=embed, view=self)
                
            else:
                # Handle fetch failure
                button.disabled = False
                button.label = "🔄 New Post"
                await interaction.edit_original_response(view=self)
                await interaction.followup.send("⚠️ Failed to fetch new content. Try again in a moment.", ephemeral=True)
                
        except Exception as e:
            logging.error(f"Error fetching new {self.media_type}: {e}")
            button.disabled = False
            button.label = "🔄 New Post"
            await interaction.edit_original_response(view=self)
            await interaction.followup.send("❌ An error occurred while fetching content.", ephemeral=True)
        
        finally:
            self.is_fetching = False

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_post(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only original user or users with manage_messages can delete
        if (interaction.user.id != self.user_id and 
            not interaction.user.guild_permissions.manage_messages):
            await interaction.response.send_message("❌ You don't have permission to delete this post.", ephemeral=True)
            return
        
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except discord.NotFound:
            pass  # Message already deleted
        except Exception as e:
            logging.error(f"Error deleting post: {e}")

    @discord.ui.button(label="📊 Info", style=discord.ButtonStyle.secondary, emoji="📊")
    async def show_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📊 Post Information",
            color=discord.Color.blue()
        )
        embed.add_field(name="📂 Category", value=self.category, inline=True)
        embed.add_field(name="🎭 Type", value=self.media_type.title(), inline=True)
        embed.add_field(name="👤 Requested by", value=f"<@{self.user_id}>", inline=True)
        embed.add_field(name="⏰ Controls expire", value="<t:" + str(int(self.timeout + discord.utils.utcnow().timestamp())) + ":R>", inline=False)
        embed.set_footer(text="Use 🔄 to fetch new content • 🗑️ to delete this post")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_timeout(self):
        # Disable all buttons when view times out
        for item in self.children:
            item.disabled = True
        
        # Try to edit the message to show expired controls
        try:
            embed = discord.Embed(
                title="⏰ Controls Expired",
                description="These controls have expired. Use the slash commands to create new posts.",
                color=discord.Color.dark_gray()
            )
            # This will only work if we store the message reference
        except:
            pass  # Ignore if we can't update

class PostCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_post_embed(self, post: dict, media_type: str, category: str) -> discord.Embed:
        """Create a standardized embed for posts"""
        color_map = {
            "image": discord.Color.magenta(),
            "gif": discord.Color.orange(),
            "clip": discord.Color.red()
        }
        
        embed = discord.Embed(
            title=post.get("title", f"{media_type.title()} Post"),
            color=color_map.get(media_type, discord.Color.blue())
        )
        
        if media_type == "clip":
            embed.set_image(url=post.get("thumbnail", ""))
            if post.get("url"):
                embed.url = post["url"]
                embed.add_field(name="🔗 Video Link", value=f"[Click here to watch]({post['url']})", inline=False)
        else:
            embed.set_image(url=post.get("url", ""))
            if post.get("url"):
                embed.url = post["url"]
        
        embed.set_footer(text=f"Category: {category} | Type: {media_type.title()}")
        return embed

    async def handle_post_command(self, interaction: discord.Interaction, category: str, 
                                 fetch_func, media_type: str, valid_categories: list):
        """Generic handler for all post commands"""
        
        # Validate category
        if category not in valid_categories:
            available = ", ".join(valid_categories[:8])  # Show first 8 categories
            more_text = f" (+{len(valid_categories) - 8} more)" if len(valid_categories) > 8 else ""
            
            embed = discord.Embed(
                title="❌ Invalid Category",
                description=f"**Available {media_type} categories:**\n{available}{more_text}",
                color=discord.Color.red()
            )
            embed.set_footer(text="Use /list to see all categories")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Defer response for longer operations
        await interaction.response.defer()
        
        try:
            # Fetch content with timeout
            post = await asyncio.wait_for(fetch_func(category), timeout=15.0)
            
            if post:
                # Create embed and controls
                embed = await self.create_post_embed(post, media_type, category)
                view = PostControls(category, media_type, interaction.user.id, self)
                
                await interaction.followup.send(embed=embed, view=view)
                
            else:
                # Handle fetch failure with retry option
                embed = discord.Embed(
                    title="⚠️ Fetch Failed",
                    description=f"Failed to fetch {media_type} from category: **{category}**",
                    color=discord.Color.orange()
                )
                embed.add_field(name="💡 Suggestions", 
                               value="• Try a different category\n• Check if the category name is correct\n• Try again in a moment", 
                               inline=False)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Request Timeout",
                description=f"The request for {media_type} took too long. Please try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logging.error(f"Error in {media_type} post command: {e}")
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An error occurred while processing your request.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="post_image", description="Post a single image from a chosen category")
    @app_commands.describe(category="Choose a category")
    async def post_image(self, interaction: discord.Interaction, category: str):
        await self.handle_post_command(interaction, category, fetch_image, "image", NSFW_IMAGE_CATEGORIES)

    @app_commands.command(name="post_gif", description="Post a single GIF from a chosen category")
    @app_commands.describe(category="Choose a category")
    async def post_gif(self, interaction: discord.Interaction, category: str):
        await self.handle_post_command(interaction, category, fetch_gif, "gif", NSFW_GIF_CATEGORIES)

    @app_commands.command(name="post_clip", description="Post a single video clip from a chosen category")
    @app_commands.describe(category="Choose a category")
    async def post_clip(self, interaction: discord.Interaction, category: str):
        await self.handle_post_command(interaction, category, fetch_spankbang_video, "clip", NSFW_CLIP_CATEGORIES)

    @app_commands.command(name="list", description="List all available categories")
    async def list_categories(self, interaction: discord.Interaction):
        # Create paginated category list for better readability
        def chunk_list(lst, chunk_size):
            for i in range(0, len(lst), chunk_size):
                yield lst[i:i + chunk_size]

        embed = discord.Embed(
            title="📂 Available Categories", 
            color=discord.Color.blue()
        )
        
        # Images
        if NSFW_IMAGE_CATEGORIES:
            image_chunks = list(chunk_list(NSFW_IMAGE_CATEGORIES, 8))
            image_text = ""
            for i, chunk in enumerate(image_chunks):
                if i == 0:
                    image_text = ", ".join(chunk)
                else:
                    image_text += f"\n{', '.join(chunk)}"
            embed.add_field(name="🖼️ Images", value=image_text or "None", inline=False)
        
        # GIFs
        if NSFW_GIF_CATEGORIES:
            gif_chunks = list(chunk_list(NSFW_GIF_CATEGORIES, 8))
            gif_text = ""
            for i, chunk in enumerate(gif_chunks):
                if i == 0:
                    gif_text = ", ".join(chunk)
                else:
                    gif_text += f"\n{', '.join(chunk)}"
            embed.add_field(name="🎞️ GIFs", value=gif_text or "None", inline=False)
        
        # Clips
        if NSFW_CLIP_CATEGORIES:
            clip_chunks = list(chunk_list(NSFW_CLIP_CATEGORIES, 8))
            clip_text = ""
            for i, chunk in enumerate(clip_chunks):
                if i == 0:
                    clip_text = ", ".join(chunk)
                else:
                    clip_text += f"\n{', '.join(chunk)}"
            embed.add_field(name="📹 Clips", value=clip_text or "None", inline=False)
        
        embed.set_footer(text="Use these category names with /post_image, /post_gif, or /post_clip")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="random_post", description="Post random content from any category")
    @app_commands.describe(
        media_type=app_commands.Choice(name="Image", value="image") or 
                   app_commands.Choice(name="GIF", value="gif") or 
                   app_commands.Choice(name="Clip", value="clip")
    )
    async def random_post(self, interaction: discord.Interaction, media_type: str = "image"):
        """Post random content from a random category"""
        import random
        
        # Select random category based on media type
        if media_type == "image" and NSFW_IMAGE_CATEGORIES:
            category = random.choice(NSFW_IMAGE_CATEGORIES)
            await self.handle_post_command(interaction, category, fetch_image, "image", NSFW_IMAGE_CATEGORIES)
        elif media_type == "gif" and NSFW_GIF_CATEGORIES:
            category = random.choice(NSFW_GIF_CATEGORIES)
            await self.handle_post_command(interaction, category, fetch_gif, "gif", NSFW_GIF_CATEGORIES)
        elif media_type == "clip" and NSFW_CLIP_CATEGORIES:
            category = random.choice(NSFW_CLIP_CATEGORIES)
            await self.handle_post_command(interaction, category, fetch_spankbang_video, "clip", NSFW_CLIP_CATEGORIES)
        else:
            embed = discord.Embed(
                title="❌ No Categories Available",
                description=f"No {media_type} categories are available.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(PostCommands(bot))