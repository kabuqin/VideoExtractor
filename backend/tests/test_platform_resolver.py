import pytest

from app.core.exceptions import UnsupportedPlatformError
from app.platforms.resolver import PlatformResolver


@pytest.mark.parametrize(
    ("url", "platform"),
    [
        ("https://www.bilibili.com/video/BV1xx411c7mD", "bilibili"),
        ("https://v.douyin.com/example/", "douyin"),
        ("https://www.tiktok.com/@user/video/123456", "tiktok"),
        ("https://www.xiaohongshu.com/explore/abc123", "xiaohongshu"),
    ],
)
def test_resolver_detects_supported_platforms(url: str, platform: str) -> None:
    info = PlatformResolver().resolve(url)

    assert info.platform == platform
    assert info.normalized_url == url


def test_resolver_rejects_unsupported_platform() -> None:
    with pytest.raises(UnsupportedPlatformError):
        PlatformResolver().resolve("https://example.com/video/1")

