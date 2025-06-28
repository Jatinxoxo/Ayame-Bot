# test_fetcher.py
import asyncio
from eporner_fetcher import fetch_eporner_video

async def main():
    category = input("Enter category: ")
    result = await fetch_eporner_video(category)
    if not result:
        print("❌ Failed to fetch video.")
    else:
        print(f"✅ Title: {result['title']}")
        print(f"🔗 URL: {result['url']}")
        print(f"🖼️ Thumbnail: {result['thumbnail']}")

asyncio.run(main())
