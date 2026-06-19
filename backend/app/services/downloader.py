import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import DownloadError, SubtitleExtractionError
from app.storage.path_manager import path_manager


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
            # Subtitle download options
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["zh-Hans", "zh", "zh-CN", "en"],
            "subtitlesformat": "vtt/srt/best",
        }

        # Add YouTube cookies if configured
        cookies_file = settings.youtube_cookies_file
        if cookies_file and Path(cookies_file).exists():
            options["cookies"] = cookies_file
        elif cookies_file:
            from app.core.exceptions import DownloadError
            raise DownloadError(f"YouTube cookies file not found: {cookies_file}")

        ydl = self._build_ydl(options)
        metadata = self._extract_info(ydl, url)
        video_path = self._resolve_downloaded_path(ydl, metadata)

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

