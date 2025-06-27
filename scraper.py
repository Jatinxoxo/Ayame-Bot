import aiohttp
import random
from nsfw_data import NSFW_IMAGE_CATEGORIES, NSFW_GIF_CATEGORIES, NSFW_CLIP_CATEGORIES

BASE_URL = "https://nekobot.xyz/api/image?type="

async def fetch_from_nekobot(category: str):
    url = f"{BASE_URL}{category}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"Failed to fetch Nekobot content: HTTP {resp.status}")
                return None
            data = await resp.json()
            if not data.get("success"):
                print("Nekobot API returned failure.")
                return None
            return {
                "title": category.capitalize(),
                "media": data["message"],
                "url": data["message"]
            }

async def fetch_image(category: str):
    if category not in NSFW_IMAGE_CATEGORIES:
        print(f"Invalid image category: {category}")
        return None
    return await fetch_from_nekobot(category)

async def fetch_gif(category: str):
    if category not in NSFW_GIF_CATEGORIES:
        print(f"Invalid gif category: {category}")
        return None
    return await fetch_from_nekobot(category)

async def fetch_clip(category: str):
    if category not in NSFW_CLIP_CATEGORIES:
        print(f"Invalid clip category: {category}")
        return None
    return await fetch_from_nekobot(category)
