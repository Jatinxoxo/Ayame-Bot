import aiohttp
from bs4 import BeautifulSoup 
import random

SPANKBANG_BASE = "https://spankbang.party"
CATEGORIES = [
    "romantic", "couples", "softcore", "sensual", "passionate",
    "intimate", "massage", "mature", "schoolgirl", "exploration",
    "brunette", "blonde", "redhead", "closeup", "pov"
]

async def fetch_spankbang_video(category=None, interaction=None):
    if not category or category not in CATEGORIES:
        category = random.choice(CATEGORIES)

    url = f"{SPANKBANG_BASE}/s/{category}/1/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    print(f"❌ SpankBang fetch failed with status {resp.status}")
                    return None

                html = await resp.text()
                print("[DEBUG HTML START]\n", html[:1500], "\n[DEBUG HTML END]")
                soup = BeautifulSoup(html, "html.parser")

                video_cards = soup.select("a[href^='/']:has(img)") or soup.select(".video_item a")

                if not video_cards:
                    print("❌ No valid <a> tags with thumbnails found on SpankBang.")
                    return None

                candidates = [a for a in video_cards if a.select_one("img") and a.get("href")]
                if not candidates:
                    print("❌ No thumbnails available for teaser candidates.")
                    return None

                chosen = random.choice(candidates)
                video_url = SPANKBANG_BASE + chosen.get("href", "")
                img = chosen.select_one("img")

                # Post the video link separately to trigger Discord preview if possible
                if interaction:
                    try:
                        await interaction.channel.send(video_url)
                    except Exception as send_error:
                        print(f"[Post Clip URL Error] {send_error}")

                return {
                    "title": img.get("alt", "NSFW Video"),
                    "url": video_url,
                    "thumbnail": img.get("data-src") or img.get("src") or ""
                }

    except Exception as e:
        print(f"[SpankBang Error] {e}")
        return None
