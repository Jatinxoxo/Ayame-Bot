import aiohttp
from bs4 import BeautifulSoup

async def fetch_spankbang_video(category):
    try:
        url = f"https://spankbang.com/s/{category.replace(' ', '+')}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        video_card = soup.select_one(".video-thumb")
        if not video_card:
            return None

        video_page_link = "https://spankbang.com" + video_card.get("href")
        thumbnail_url = video_card.select_one("img").get("src") if video_card.select_one("img") else None
        title = video_card.get("title", "Untitled Clip")

        # Now fetch the actual video URL
        async with aiohttp.ClientSession() as session:
            async with session.get(video_page_link) as video_response:
                if video_response.status != 200:
                    return None
                video_html = await video_response.text()

        video_soup = BeautifulSoup(video_html, "html.parser")
        script_tag = video_soup.find("script", string=lambda s: "sources" in s if s else False)

        if not script_tag:
            return None

        # Try to extract mp4 URL from the sources JSON-like string
        import re, json
        sources_match = re.search(r'sources\s*:\s*(\[[^\]]+\])', script_tag.string)
        if not sources_match:
            return None

        sources_json = sources_match.group(1).replace("'", '"')
        sources = json.loads(sources_json)

        video_url = next((src["src"] for src in sources if src["src"].endswith(".mp4")), None)
        if not video_url:
            return None

        return {
            "title": title,
            "url": video_url,
            "thumbnail": thumbnail_url or "https://spankbang.com/images/logo.png"
        }

    except Exception as e:
        print(f"[Fetch Clip Error] {e}")
        return None
