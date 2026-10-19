import re

# Supported video URL patterns for auto-extraction from share text.
VIDEO_URL_PATTERNS = [
    re.compile(r"https?://v\.douyin\.com/[\w-]+/?"),
    re.compile(r"https?://www\.douyin\.com/video/[\d]+"),
    re.compile(r"https?://www\.bilibili\.com/video/BV[\w]+"),
    re.compile(r"https?://b23\.tv/[\w]+"),
    re.compile(r"https?://www\.tiktok\.com/@[\w.]+/video/[\d]+"),
    re.compile(r"https?://www\.xiaohongshu\.com/explore/[\w]+"),
    re.compile(r"https?://www\.youtube\.com/watch\?v=[\w-]+"),
    re.compile(r"https?://www\.youtube\.com/shorts/[\w-]+"),
    re.compile(r"https?://youtu\.be/[\w-]+"),
]


def extract_video_url(text: str) -> str:
    """Extract the first supported video URL from arbitrary text (share text etc.)."""
    for pattern in VIDEO_URL_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return text.strip()
