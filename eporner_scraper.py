import aiohttp
import random
import os

EPORNER_API_KEY = os.getenv("EPORNER_API_KEY") or "your_api_key_here"

CATEGORIES = [
    "milf", "lesbian", "blowjob", "amateur", "teen",
    "big-tits", "anal", "cumshot", "public", "brunette",
    "creampie", "hardcore", "fingering", "deepthroat",
    "fetish", "facial", "mature", "schoolgirl"
]

async def fetch_eporner_video(category=None):
    if not category or category not in CATEGORIES:
        category = random.choice(CATEGORIES)

    params = {
        "query": category,
        "per_page": 30,
        "page": random.randint(1, 3),
        "thumbsize": "big",
        "order": "top-week",
        "lq": "1",
        "api_key": EPORNER_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.eporner.com/api/v2/video/search/", params=params) as resp:
            if resp.status != 200:
                print(f"❌ Eporner API failed with status {resp.status}")
                return None
            data = await resp.json()
            results = data.get("videos", [])
            if not results:
                print("❌ No videos returned from Eporner.")
                return None

            chosen = random.choice(results)
            return {
                "title": chosen.get("title"),
                "url": chosen.get("url"),
                "thumbnail": chosen.get("default_thumb")
            }

# Usage:
# post = await fetch_eporner_video("milf")
