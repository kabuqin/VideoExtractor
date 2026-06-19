"""YouTube platform adapter."""

from urllib.parse import parse_qs, urlparse

from app.platforms.base import PlatformInfo


class YouTubeAdapter:
    platform = "youtube"

    def matches(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return any(domain in host for domain in [
            "youtube.com",
            "youtu.be",
            "youtube-nocookie.com",
        ])

    def resolve(self, url: str) -> PlatformInfo:
        parsed = urlparse(url)
        video_id = self._extract_video_id(parsed)
        return PlatformInfo(
            platform=self.platform,
            source_url=url,
            normalized_url=url,
            video_id=video_id,
        )

    def _extract_video_id(self, parsed) -> str | None:
        # youtube.com/watch?v=VIDEO_ID
        if "watch" in parsed.path:
            params = parse_qs(parsed.query)
            return params.get("v", [None])[0]

        # youtu.be/VIDEO_ID
        if parsed.netloc == "youtu.be":
            return parsed.path.lstrip("/")

        # youtube.com/shorts/VIDEO_ID
        path_parts = [p for p in parsed.path.split("/") if p]
        if path_parts:
            return path_parts[-1]

        return None
