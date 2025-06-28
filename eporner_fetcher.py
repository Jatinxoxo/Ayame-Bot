import aiohttp
import random
import asyncio
import logging
import ssl
import certifi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_eporner_video(category: str, max_retries: int = 3):
    """
    Fetch a random Eporner video by category.

    Args:
        category (str): Search keyword/category.
        max_retries (int): Number of retry attempts on failure.

    Returns:
        dict | None: Video metadata or None on failure.
    """
    base_url = "https://www.eporner.com/api/v2/video/search/"
    page = random.randint(1, 10)
    params = {
        "query": category,
        "per_page": 20,
        "page": page,
        "thumbsize": "big",
        "format": "json"
    }

    # Use certifi-based SSL context for proper certificate validation
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔍 Searching Eporner for: '{category}' (Page {page})")
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(base_url, params=params) as response:
                    logger.info(f"📥 HTTP Status: {response.status}")
                    if response.status != 200:
                        logger.warning(f"❌ Failed with HTTP status {response.status}")
                        return None

                    data = await response.json()

            videos = data.get("videos", [])
            if not videos:
                logger.warning("❌ No videos found.")
                return None

            video = random.choice(videos)

            # Handle thumbnail structure (dict or string)
            thumb = video.get("default_thumb", "")
            thumbnail = thumb.get("src") if isinstance(thumb, dict) else thumb

            result = {
                "title": video.get("title", "Untitled Clip"),
                "url": video.get("url", ""),
                "thumbnail": thumbnail,
                "duration": str(video.get("length_min", "N/A"))
            }

            logger.info(f"✅ Title: {result['title']}")
            logger.info(f"🔗 URL: {result['url']}")
            logger.info(f"🖼️ Thumbnail: {result['thumbnail']}")
            return result

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"⚠️ Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                logger.error("❌ All retries failed.")
                return None
        except Exception as e:
            logger.exception(f"❌ Unexpected error: {e}")
            return None
