"""
Douyin video extractor using Playwright.

Bypasses yt-dlp's broken DouyinIE (which requires X-Bogus signature) by:
1. Using Playwright (headless Chromium) to load the video page
2. Extracting CDN video URLs from the rendered HTML
3. Downloading the video directly (CDN URLs are publicly accessible)
"""
import asyncio
import logging
import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class DouyinVideoInfo:
    title: str
    author: str
    duration: int
    thumbnail_url: str
    video_url: str
    description: str = ""


class DouyinExtractor:
    """Custom Douyin video extractor using Playwright."""

    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"

    def __init__(self, cookies_file: Optional[str] = None):
        self._cookies_file = cookies_file
        self._browser = None
        self._context = None

    async def _ensure_browser(self):
        """Lazy-init browser context."""
        from playwright.async_api import async_playwright

        if self._browser:
            return

        p = await async_playwright().__aenter__()
        self._playwright = p
        self._browser = await p.chromium.launch(headless=True)
        self._context = await self._browser.new_context(
            user_agent=self.UA,
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )

        # Load cookies if available
        if self._cookies_file and Path(self._cookies_file).exists():
            await self._load_cookies()

    async def _load_cookies(self):
        """Load Netscape format cookies into the browser context."""
        try:
            with open(self._cookies_file, encoding="utf-8") as f:
                count = 0
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 7:
                        await self._context.add_cookies([{
                            "name": parts[5],
                            "value": parts[6],
                            "domain": parts[0].lstrip("."),
                            "path": parts[2],
                            "secure": parts[3].lower() == "true",
                            "httpOnly": parts[4].lower() == "true",
                            "sameSite": "Lax",
                        }])
                        count += 1
                logger.info("Loaded %d cookies for Douyin", count)
        except Exception as e:
            logger.warning("Failed to load Douyin cookies: %s", e)

    async def extract(self, url: str) -> DouyinVideoInfo:
        """Extract video info from a Douyin video page.

        Returns DouyinVideoInfo with the best available video URL and metadata.
        """
        await self._ensure_browser()
        page = await self._context.new_page()

        try:
            # Navigate and wait for dynamic content
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for video element (indicates JS has rendered)
            try:
                await page.wait_for_selector("video", timeout=20000)
            except Exception:
                logger.warning("Video element did not appear within timeout")

            # Give extra time for all data to load
            await page.wait_for_timeout(8000)

            # Extract video URLs from rendered HTML
            html = await page.content()
            video_urls = self._extract_video_urls(html)

            if not video_urls:
                raise RuntimeError("No video URLs found in Douyin page")

            # Select best quality (AVC1 > HVC1 > standard)
            best_url = self._select_best_url(video_urls)

            # Extract metadata
            title = await self._extract_title(page, html)
            author = await self._extract_author(page, html)
            duration = await self._extract_duration(page)
            thumbnail = await self._extract_thumbnail(page, html)
            description = await self._extract_description(page)

            logger.info(
                "Douyin extract success: title=%s, author=%s, duration=%ds, quality=%s",
                title, author, duration,
                "avc1" if "media-video-avc1" in best_url else "standard",
            )

            return DouyinVideoInfo(
                title=title,
                author=author,
                duration=duration,
                thumbnail_url=thumbnail,
                video_url=best_url,
                description=description,
            )

        finally:
            await page.close()

    def _extract_video_urls(self, html: str) -> list[str]:
        """Extract unique video CDN URLs from rendered page HTML."""
        urls = []

        # Pattern 1: URL-encoded src in JSON data
        src_pattern = r'"src"%3A"https%3A%2F%2F([^"]*douyinvod[^"]*)"'
        for m in re.findall(src_pattern, html):
            decoded = urllib.parse.unquote(m)
            full_url = f"https://{decoded}"
            if full_url not in urls:
                urls.append(full_url)

        # Pattern 2: Direct video/tos URLs
        tos_pattern = r'https?://[^"\'\\\s<>]*video/tos/[^"\'\\\s<>]*'
        for m in re.findall(tos_pattern, html):
            u = urllib.parse.unquote(m)
            if u not in urls:
                urls.append(u)

        return urls

    def _select_best_url(self, urls: list[str]) -> str:
        """Select the best quality video URL.

        Priority: AVC1 (H.264) > HVC1 (H.265) > standard
        """
        # Prefer AVC1 (best compatibility)
        avc1 = [u for u in urls if "media-video-avc1" in u]
        if avc1:
            return avc1[0]

        # Fallback to HVC1
        hvc1 = [u for u in urls if "media-video-hvc1" in u or "media-video" in u]
        if hvc1:
            return hvc1[0]

        # Return any URL
        return urls[0] if urls else ""

    async def _extract_title(self, page, html: str) -> str:
        """Extract video title from page."""
        try:
            title = await page.title()
            if title:
                # Remove site suffix like " - 抖音" first, then check
                cleaned = re.sub(r"\s*[–-]\s*抖音.*$", "", title).strip()
                if cleaned and cleaned != title:
                    return cleaned
                # If the title itself is just "抖音" or similar, try other sources
        except Exception:
            pass

        # Fallback 1: lark:url:video_title meta tag (Douyin-specific)
        lark_title = re.search(r'<meta[^>]+name="lark:url:video_title"[^>]+content="([^"]+)"', html)
        if lark_title:
            return lark_title.group(1)

        # Fallback 2: try og:title meta tag
        og_title = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html)
        if og_title:
            return og_title.group(1)

        # Fallback 3: extract from RENDER_DATA
        try:
            render_match = re.search(r'id="RENDER_DATA"[^>]*>([^<]+)<', html)
            if render_match:
                import json
                decoded = urllib.parse.unquote(render_match.group(1))
                data = json.loads(decoded)
                # Navigate to find title in the deep structure
                # Pattern varies, try common paths
                title = self._find_in_render_data(data, 'title')
                if title:
                    return title
        except Exception:
            pass

        return "Untitled"

    def _find_in_render_data(self, data, key: str) -> str | None:
        """Recursively search for a key in nested dicts/lists from RENDER_DATA."""
        if isinstance(data, dict):
            for k, v in data.items():
                if k == key and isinstance(v, str) and len(v) > 1:
                    return v
                result = self._find_in_render_data(v, key)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_in_render_data(item, key)
                if result:
                    return result
        return None

    async def _extract_author(self, page, html: str) -> str:
        """Extract author name."""
        try:
            author = await page.evaluate("""
                () => {
                    // Try douyin specific author selector
                    const authorLinks = document.querySelectorAll('a[href*="user/"], a[href*="author/"]');
                    for (const a of authorLinks) {
                        const text = a.textContent.trim();
                        if (text && text.length > 0 && text.length < 40) return text;
                    }
                    
                    // Try data-e2e="author" attribute
                    const e2eAuthor = document.querySelector('[data-e2e="author"]');
                    if (e2eAuthor) return e2eAuthor.textContent.trim();
                    
                    // Try common author element patterns with dynamic class names
                    const authorEls = document.querySelectorAll('[class*="author"],[class*="nickname"],[class*="uploader"]');
                    for (const el of authorEls) {
                        const text = el.textContent.trim();
                        if (text && text.length < 50 && !text.includes(' ')) return text;
                    }
                    
                    return '';
                }
            """)
            if author:
                return author.strip()
        except Exception:
            pass

        # Fallback: lark:url:video_brand_name meta tag
        lark_brand = re.search(r'<meta[^>]+name="lark:url:video_brand_name"[^>]+content="([^"]+)"', html)
        if lark_brand:
            return lark_brand.group(1)

        # Fallback: extract author from RENDER_DATA
        try:
            render_match = re.search(r'id="RENDER_DATA"[^>]*>([^<]+)<', html)
            if render_match:
                import json
                decoded = urllib.parse.unquote(render_match.group(1))
                data = json.loads(decoded)
                for key in ['author', 'nickname', 'uploader', 'user']:
                    val = self._find_in_render_data(data, key)
                    if val:
                        return val
        except Exception:
            pass

        return "Unknown"

    async def _extract_duration(self, page) -> int:
        """Extract video duration in seconds."""
        try:
            duration = await page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (video && video.duration && isFinite(video.duration)) {
                        return Math.round(video.duration);
                    }
                    return 0;
                }
            """)
            return duration or 0
        except Exception:
            return 0

    async def _extract_thumbnail(self, page, html: str) -> str:
        """Extract thumbnail URL."""
        try:
            # Try lark:url:video_cover_image_url meta tag (Douyin-specific)
            lark_img = re.search(r'<meta[^>]+name="lark:url:video_cover_image_url"[^>]+content="([^"]+)"', html)
            if lark_img:
                return lark_img.group(1)

            # Try og:image
            og_image = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
            if og_image:
                return og_image.group(1)

            # Try video poster
            poster = await page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    return video ? video.poster : '';
                }
            """)
            if poster:
                return poster
        except Exception:
            pass

        return ""

    async def _extract_description(self, page) -> str:
        """Extract video description."""
        try:
            desc = await page.evaluate("""
                () => {
                    const el = document.querySelector('[class*="desc"],[class*="description"]');
                    return el ? el.textContent.trim() : '';
                }
            """)
            return desc or ""
        except Exception:
            return ""

    async def close(self):
        """Cleanup browser resources."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, "_playwright"):
            try:
                await self._playwright.stop()
            except Exception:
                pass

    def download_video(self, video_url: str, output_path: str) -> bool:
        """Download a video from its CDN URL.

        This is a synchronous method called after extraction.
        """
        import requests

        headers = {
            "User-Agent": self.UA,
            "Referer": "https://www.douyin.com/",
        }

        try:
            # Stream download with progress
            resp = requests.get(video_url, headers=headers, stream=True, timeout=300)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = downloaded * 100 // total
                            if pct % 25 == 0 and downloaded > 0:
                                logger.info("Download progress: %d%% (%d/%d MB)", pct, downloaded // 1048576, total // 1048576)

            logger.info("Video downloaded: %s (%d bytes)", output_path, downloaded)
            return True

        except Exception as e:
            logger.error("Video download failed: %s", e)
            return False


# Singleton with lazy init
_douyin_extractor: Optional[DouyinExtractor] = None


async def get_extractor(cookies_file: Optional[str] = None) -> DouyinExtractor:
    """Get or create the Douyin extractor singleton."""
    global _douyin_extractor
    if _douyin_extractor is None:
        _douyin_extractor = DouyinExtractor(cookies_file=cookies_file)
    return _douyin_extractor
