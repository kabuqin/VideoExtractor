import logging

from fastapi import APIRouter

from app.core.exceptions import UnsupportedPlatformError
from app.core.urls import extract_video_url
from app.platforms.resolver import platform_resolver
from app.schemas.parse import ParseRequest, ParseResult
from app.services.downloader import downloader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parse", tags=["parse"])


@router.post("", response_model=ParseResult)
def parse_video(payload: ParseRequest) -> ParseResult:
    """Resolve platform and video metadata without downloading the file."""
    source_url = extract_video_url(payload.url)

    try:
        platform_info = platform_resolver.resolve(source_url)
    except UnsupportedPlatformError:
        return ParseResult(
            supported=False,
            source_url=source_url,
            error="暂不支持该平台，目前支持 B站、抖音、TikTok、小红书和 YouTube。",
        )

    result = ParseResult(
        supported=True,
        source_url=source_url,
        platform=platform_info.platform,
        normalized_url=platform_info.normalized_url,
    )

    try:
        probed = downloader.probe_metadata(platform_info.normalized_url or source_url)
        result.title = probed.title
        result.author = probed.author
        result.duration = probed.duration
        result.thumbnail_url = probed.thumbnail_url
        description = (probed.description or "").strip()
        result.description = None if description in {"", "-", "N/A", "无"} else description
    except Exception as exc:
        logger.warning("Metadata probe failed for %s: %s", source_url, exc)
        result.error = f"未能获取完整视频信息：{exc}"

    return result
