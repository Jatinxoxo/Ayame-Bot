import aiohttp
from bs4 import BeautifulSoup
import re
import json

async def fetch_spankbang_video(category):
    try:
        search_url = f"https://spankbang.com/s/{category.replace(' ', '+')}"

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    print(f"[SpankBang] Bad response: {response.status}")
                    return None
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        video_card = soup.select_one(".video-thumb")
        if not video_card:
            print("[SpankBang] No video card found")
            return None

        video_page_link = "https://spankbang.com" + video_card.get("href")
        thumbnail_url = video_card.select_one("img").get("src") if video_card.select_one("img") else None
        title = video_card.get("title", "Untitled Clip")

        async with aiohttp.ClientSession() as session:
            async with session.get(video_page_link, timeout=aiohttp.ClientTimeout(total=10)) as video_response:
                if video_response.status != 200:
                    print(f"[SpankBang] Failed to fetch video page: {video_response.status}")
                    return None
                video_html = await video_response.text()

        video_soup = BeautifulSoup(video_html, "html.parser")
        script_tag = video_soup.find("script", string=lambda s: "sources" in s if s else False)
        if not script_tag:
            print("[SpankBang] No sources script tag found")
            return None

        sources_match = re.search(r'sources\s*:\s*(\[[^\]]+\])', script_tag.string)
        if not sources_match:
            print("[SpankBang] Could not find sources JSON")
            return None

        sources_json = sources_match.group(1).replace("'", '"')
        sources = json.loads(sources_json)

        video_url = next((src["src"] for src in sources if src["src"].endswith(".mp4")), None)
        if not video_url:
            print("[SpankBang] No valid MP4 link found")
            return None

        return {
            "title": title,
            "url": video_url,
            "thumbnail": thumbnail_url or "https://spankbang.com/images/logo.png"
        }

    except Exception as e:
        print(f"[SpankBang ERROR] {e}")
        return None
