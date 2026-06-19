from urllib.parse import urlparse

from app.platforms.base import PlatformInfo


class DouyinAdapter:
    platform = "douyin"

    def matches(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return "douyin.com" in host or host == "v.douyin.com"

    def resolve(self, url: str) -> PlatformInfo:
        path_parts = [part for part in urlparse(url).path.split("/") if part]
        video_id = path_parts[-1] if path_parts else None
        return PlatformInfo(
            platform=self.platform,
            source_url=url,
            normalized_url=url,
            video_id=video_id,
        )

