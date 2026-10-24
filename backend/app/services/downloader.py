import asyncio
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import DownloadError, SubtitleExtractionError
from app.storage.path_manager import path_manager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DownloadedVideo:
    title: str | None
    author: str | None
    duration: int | None
    thumbnail_url: str | None
    video_path: str | None
    description: str | None = None
    subtitle_paths: list[str] = field(default_factory=list)
    subtitle_lang: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class YtDlpDownloader:
    def fetch_metadata(self, url: str) -> dict[str, Any]:
        ydl = self._build_ydl({"skip_download": True})
        return self._extract_info(ydl, url)

    def probe_metadata(self, url: str) -> DownloadedVideo:
        """Resolve video metadata without downloading the media file."""
        options = {
            "skip_download": True,
            "noplaylist": True,
            "socket_timeout": 20,
        }

        cookies_file = settings.youtube_cookies_file
        if cookies_file and Path(cookies_file).exists():
            options["cookies"] = cookies_file

        try:
            _, metadata = self._try_extract_with_browser_cookies(url, options)
        except DownloadError:
            if self._is_douyin_url(url):
                try:
                    info = self._extract_douyin_info(url)
                except Exception as exc:
                    logger.warning("Douyin metadata probe failed: %s", exc)
                else:
                    return DownloadedVideo(
                        title=info.title,
                        author=info.author,
                        duration=info.duration,
                        thumbnail_url=info.thumbnail_url,
                        video_path=None,
                        description=info.description,
                        metadata={"extractor": "DouyinExtractor"},
                    )
            raise

        return DownloadedVideo(
            title=metadata.get("title"),
            author=metadata.get("uploader") or metadata.get("channel") or metadata.get("creator"),
            duration=self._safe_int(metadata.get("duration")),
            thumbnail_url=metadata.get("thumbnail"),
            video_path=None,
            description=metadata.get("description"),
            metadata=self._compact_metadata(metadata),
        )

    def _try_extract_with_browser_cookies(self, url: str, options: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Try extracting with browser cookies, falling back through multiple browsers.

        Browser order: configured browser → chrome → edge → firefox.
        If all fail, proceeds without cookies (logs warning).
        """
        configured = settings.browser_cookies
        if not configured:
            ydl = self._build_ydl(options)
            return ydl, self._extract_info(ydl, url)

        # Build browser try order: configured first, then fallbacks
        fallbacks = ["chrome", "edge", "firefox"]
        browser_order = [configured]
        for fb in fallbacks:
            if fb not in browser_order:
                browser_order.append(fb)

        for i, browser in enumerate(browser_order):
            try:
                opts = {**options, "cookiesfrombrowser": (browser,)}
                ydl = self._build_ydl(opts)
                return ydl, self._extract_info(ydl, url)
            except Exception as e:
                if i < len(browser_order) - 1:
                    next_browser = browser_order[i + 1]
                    logger.warning(
                        "Browser cookies from '%s' failed, trying '%s': %s",
                        browser, next_browser, e,
                    )
                else:
                    logger.warning(
                        "All browsers failed, trying manual cookies file: %s", e,
                    )

        # Fallback: try manual cookies file
        cookies_file = settings.cookies_file
        if cookies_file and Path(cookies_file).exists():
            logger.info("Using manual cookies file: %s", cookies_file)
            opts = {**options, "cookies": cookies_file}
            ydl = self._build_ydl(opts)
            return ydl, self._extract_info(ydl, url)
        elif cookies_file:
            logger.warning("Manual cookies file not found: %s", cookies_file)

        # Final fallback: no cookies
        logger.warning("Proceeding without cookies")
        ydl = self._build_ydl(options)
        return ydl, self._extract_info(ydl, url)

    @staticmethod
    def _is_douyin_url(url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return "douyin.com" in host or host == "v.douyin.com"

    def _extract_douyin_info(self, url: str):
        """Run the Playwright-based Douyin extractor (metadata + CDN URL)."""
        from app.platforms.douyin_extractor import DouyinExtractor

        cookies_file = settings.cookies_file
        if cookies_file and not Path(cookies_file).exists():
            cookies_file = None

        extractor = DouyinExtractor(cookies_file=cookies_file)

        # Use the SAME event loop for extract and close (Playwright WebSocket is loop-bound)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(extractor.extract(url))
        finally:
            try:
                loop.run_until_complete(extractor.close())
            finally:
                loop.close()

    def _try_douyin_fallback(self, url: str, task_id: UUID) -> DownloadedVideo | None:
        """Try custom Douyin extractor as fallback when yt-dlp fails."""
        if not self._is_douyin_url(url):
            return None

        try:
            logger.info("Trying custom Douyin extractor (Playwright)...")
            info = self._extract_douyin_info(url)

            logger.info("Douyin extractor got video: %s by %s", info.title, info.author)

            # Generate output path
            output_dir = settings.storage_root / "videos" / str(task_id)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "video.mp4"

            # Download the video from CDN URL
            from app.platforms.douyin_extractor import DouyinExtractor

            success = DouyinExtractor().download_video(info.video_url, str(output_path))

            if not success or not output_path.exists():
                logger.error("Douyin video download failed")
                return None

            file_size = output_path.stat().st_size
            logger.info("Douyin video saved: %s (%d bytes)", output_path, file_size)

            return DownloadedVideo(
                title=info.title,
                author=info.author,
                duration=info.duration,
                thumbnail_url=info.thumbnail_url,
                video_path=str(output_path),
                description=info.description,
                subtitle_paths=[],
                metadata={
                    "extractor": "DouyinExtractor",
                    "video_url": info.video_url,
                },
            )

        except ImportError as e:
            logger.warning("Playwright not available, cannot use Douyin fallback: %s", e)
            return None
        except Exception as e:
            logger.warning("Custom Douyin extractor failed: %s", e)
            return None

    def download(self, url: str, task_id: UUID) -> DownloadedVideo:
        output_template = path_manager.video_output_template(task_id)
        options = {
            "outtmpl": output_template,
            "format": "bv*+ba/best",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "retries": 3,
            "fragment_retries": 5,
            "socket_timeout": 30,
        }

        # Add YouTube cookies if configured
        cookies_file = settings.youtube_cookies_file
        if cookies_file and Path(cookies_file).exists():
            options["cookies"] = cookies_file
        elif cookies_file:
            raise DownloadError(f"YouTube cookies file not found: {cookies_file}")

        ffmpeg_location = self._ffmpeg_location()
        if ffmpeg_location:
            options["ffmpeg_location"] = ffmpeg_location

        # Try browser cookies with automatic fallback across browsers
        try:
            ydl, metadata = self._download_with_retry(url, options)
        except DownloadError as e:
            # If yt-dlp fails for Douyin, try custom fallback
            if self._is_douyin_url(url):
                logger.warning("yt-dlp failed for Douyin, trying Playwright fallback: %s", e)
                result = self._try_douyin_fallback(url, task_id)
                if result:
                    return result
                # Fallback failed too, re-raise original error
                raise
            raise

        video_path = self._resolve_downloaded_path(ydl, metadata)

        self._try_download_subtitles(url, options)

        # Collect subtitle files and extract description
        subtitle_paths, subtitle_lang = self._collect_subtitle_paths(video_path)
        description = metadata.get("description")

        return DownloadedVideo(
            title=metadata.get("title"),
            author=metadata.get("uploader") or metadata.get("channel") or metadata.get("creator"),
            duration=self._safe_int(metadata.get("duration")),
            thumbnail_url=metadata.get("thumbnail"),
            video_path=str(video_path) if video_path else None,
            description=description,
            subtitle_paths=subtitle_paths,
            subtitle_lang=subtitle_lang,
            metadata=self._compact_metadata(metadata),
        )

    def _try_download_subtitles(self, url: str, options: dict[str, Any]) -> None:
        """Fetch subtitles separately so failures fall back to transcription."""
        subtitle_options = {
            **options,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["zh-Hans", "zh", "zh-CN", "en"],
            "subtitlesformat": "vtt/srt/best",
        }
        try:
            self._try_extract_with_browser_cookies(url, subtitle_options)
        except Exception as exc:
            logger.warning("Subtitle download failed, continuing without subtitles: %s", exc)

    def _download_with_retry(self, url: str, options: dict[str, Any]):
        try:
            return self._try_extract_with_browser_cookies(url, options)
        except DownloadError as exc:
            if "ffmpeg" not in str(exc).lower():
                raise
            # Merging separate video/audio streams requires ffmpeg; degrade to a
            # single-file format so the pipeline still works without it.
            logger.warning("FFmpeg not available, retrying with single-file format")
            fallback_options = {**options, "format": "best[ext=mp4]/best"}
            fallback_options.pop("merge_output_format", None)
            try:
                return self._try_extract_with_browser_cookies(url, fallback_options)
            except DownloadError:
                raise exc

    @staticmethod
    def _ffmpeg_location() -> str | None:
        """Return the ffmpeg binary bundled with imageio-ffmpeg, if installed."""
        try:
            import imageio_ffmpeg
        except ImportError:
            return None

        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception as exc:
            logger.warning("Could not resolve bundled ffmpeg: %s", exc)
            return None

    def _build_ydl(self, options: dict[str, Any]):
        try:
            from yt_dlp import YoutubeDL
        except ImportError as exc:
            raise DownloadError("yt-dlp is not installed. Run `pip install -e .` in backend first.") from exc

        defaults = {
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
        }
        defaults.update(options)
        return YoutubeDL(defaults)

    def _extract_info(self, ydl, url: str) -> dict[str, Any]:
        try:
            info = ydl.extract_info(url, download=not ydl.params.get("skip_download", False))
        except Exception as exc:
            raise DownloadError(f"Video download failed: {exc}") from exc

        if not info:
            raise DownloadError("Video downloader returned no metadata.")

        if "entries" in info:
            entries = [entry for entry in info.get("entries") or [] if entry]
            if not entries:
                raise DownloadError("Playlist or collection contains no downloadable video.")
            info = entries[0]

        return info

    def _resolve_downloaded_path(self, ydl, metadata: dict[str, Any]) -> Path | None:
        requested_downloads = metadata.get("requested_downloads") or []
        for item in requested_downloads:
            filepath = item.get("filepath")
            if filepath and Path(filepath).exists():
                return Path(filepath)

        try:
            prepared = Path(ydl.prepare_filename(metadata))
        except Exception:
            return None

        candidates = [prepared, prepared.with_suffix(".mp4")]
        return next((candidate for candidate in candidates if candidate.exists()), candidates[-1])

    def _collect_subtitle_paths(self, video_path: Path | None) -> tuple[list[str], str | None]:
        """Scan for subtitle files near the downloaded video."""
        if not video_path or not video_path.exists():
            return [], None

        video_dir = video_path.parent
        video_stem = video_path.stem
        subtitle_exts = {".vtt", ".srt", ".ass", ".json3"}
        preferred_langs = ["zh-Hans", "zh", "zh-CN", "en"]

        found: list[tuple[str, Path]] = []  # (lang, path)
        for f in video_dir.iterdir():
            if not f.is_file():
                continue
            # Subtitle files typically share the video's base name
            if not f.stem.startswith(video_stem[:20]):
                continue
            if f.suffix.lower() not in subtitle_exts:
                continue
            # Try to extract language code from filename
            # e.g., "video.zh-Hans.vtt" -> "zh-Hans"
            parts = f.stem.split(".")
            lang = parts[-1] if len(parts) > 1 else "unknown"
            found.append((lang, f))

        if not found:
            return [], None

        # Prefer languages in our preferred list
        for pref_lang in preferred_langs:
            for lang, path in found:
                if pref_lang.lower() in lang.lower():
                    return [str(path)], lang

        # Fallback: return the first found
        return [str(found[0][1])], found[0][0]

    @staticmethod
    def extract_subtitles_text(subtitle_path: str) -> str:
        """Parse a subtitle file (VTT/SRT/ASS) into plain text."""
        path = Path(subtitle_path)
        if not path.exists():
            raise SubtitleExtractionError(f"Subtitle file not found: {subtitle_path}")

        content = path.read_text(encoding="utf-8", errors="replace")
        ext = path.suffix.lower()

        if ext == ".vtt":
            return YtDlpDownloader._parse_vtt(content)
        elif ext == ".srt":
            return YtDlpDownloader._parse_srt(content)
        elif ext == ".ass":
            return YtDlpDownloader._parse_ass(content)
        else:
            raise SubtitleExtractionError(f"Unsupported subtitle format: {ext}")

    @staticmethod
    def _parse_vtt(content: str) -> str:
        """Parse WebVTT subtitle content to plain text."""
        lines: list[str] = []
        for line in content.splitlines():
            line = line.strip()
            # Skip header, timecodes, empty lines, NOTE blocks
            if line.startswith("WEBVTT") or line.startswith("NOTE"):
                continue
            if re.match(r"^\d{2}:\d{2}", line) and "-->" in line:
                continue
            if re.match(r"^\d+$", line):
                continue
            if not line:
                continue
            # Remove HTML-like tags
            clean = re.sub(r"<[^>]+>", "", line)
            if clean:
                lines.append(clean)
        return YtDlpDownloader._deduplicate_lines(lines)

    @staticmethod
    def _parse_srt(content: str) -> str:
        """Parse SRT subtitle content to plain text."""
        lines: list[str] = []
        for line in content.splitlines():
            line = line.strip()
            # Skip sequence numbers, timecodes, empty lines
            if re.match(r"^\d+$", line):
                continue
            if "-->" in line:
                continue
            if not line:
                continue
            # Remove HTML-like tags
            clean = re.sub(r"<[^>]+>", "", line)
            if clean:
                lines.append(clean)
        return YtDlpDownloader._deduplicate_lines(lines)

    @staticmethod
    def _parse_ass(content: str) -> str:
        """Parse ASS/SSA subtitle content to plain text."""
        lines: list[str] = []
        in_events = False
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("[Events]"):
                in_events = True
                continue
            if line.startswith("[") and in_events:
                break
            if not in_events:
                continue
            if line.startswith("Dialogue:"):
                # Format: Dialogue: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
                parts = line.split(",", 9)
                if len(parts) >= 10:
                    text = parts[9].strip()
                    # Remove ASS override tags like {\b1}, {\c&H...&}
                    text = re.sub(r"\{[^}]*\}", "", text)
                    # Replace \N with newline
                    text = text.replace("\\N", "\n").strip()
                    if text:
                        lines.append(text)
        return YtDlpDownloader._deduplicate_lines(lines)

    @staticmethod
    def _deduplicate_lines(lines: list[str]) -> str:
        """Remove consecutive duplicate lines (common in auto-generated subtitles)."""
        if not lines:
            return ""
        result = [lines[0]]
        for line in lines[1:]:
            if line != result[-1]:
                result.append(line)
        return "\n".join(result)

    def _compact_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        keys = [
            "id",
            "title",
            "webpage_url",
            "original_url",
            "extractor",
            "extractor_key",
            "uploader",
            "channel",
            "creator",
            "duration",
            "thumbnail",
            "ext",
            "description",
            "tags",
            "categories",
        ]
        return {key: metadata.get(key) for key in keys if key in metadata}

    def _safe_int(self, value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None


downloader = YtDlpDownloader()

