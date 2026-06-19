from app.core.exceptions import UnsupportedPlatformError
from app.platforms.base import PlatformInfo
from app.platforms.bilibili import BilibiliAdapter
from app.platforms.douyin import DouyinAdapter
from app.platforms.tiktok import TikTokAdapter
from app.platforms.xiaohongshu import XiaohongshuAdapter


class PlatformResolver:
    def __init__(self) -> None:
        self.adapters = [
            BilibiliAdapter(),
            DouyinAdapter(),
            TikTokAdapter(),
            XiaohongshuAdapter(),
        ]

    def resolve(self, url: str) -> PlatformInfo:
        for adapter in self.adapters:
            if adapter.matches(url):
                return adapter.resolve(url)
        raise UnsupportedPlatformError("Only Bilibili, Douyin, TikTok and Xiaohongshu links are supported.")


platform_resolver = PlatformResolver()

