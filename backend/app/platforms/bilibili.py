from urllib.parse import urlparse

from app.platforms.base import PlatformInfo


class BilibiliAdapter:
    platform = "bilibili"

    def matches(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return "bilibili.com" in host or host == "b23.tv"

    def resolve(self, url: str) -> PlatformInfo:
        path_parts = [part for part in urlparse(url).path.split("/") if part]
        video_id = next((part for part in path_parts if part.upper().startswith("BV")), None)
        return PlatformInfo(
            platform=self.platform,
            source_url=url,
            normalized_url=url,
            video_id=video_id,
        )

