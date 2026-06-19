import logging
import re
from dataclasses import dataclass

from app.core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratedCopy:
    title: str
    summary: str
    body: str
    hashtags: list[str]


# ─── Platform-specific formatting ─────────────────────────────────────────────

_PLATFORM_FORMAT = {
    "xiaohongshu": {
        "emoji_title": True,
        "body_style": "paragraph",
        "hash_prefix": "#",
    },
    "douyin": {
        "emoji_title": False,
        "body_style": "punchy",
        "hash_prefix": "#",
    },
    "bilibili": {
        "emoji_title": False,
        "body_style": "detailed",
        "hash_prefix": "#",
    },
    "tiktok": {
        "emoji_title": True,
        "body_style": "punchy",
        "hash_prefix": "#",
    },
    "youtube": {
        "emoji_title": False,
        "body_style": "detailed",
        "hash_prefix": "#",
    },
}

_STYLE_KEYWORDS = {
    "knowledge": ["干货", "分享", "知识", "科普", "教程"],
    "marketing": ["种草", "推荐", "好物", "安利", "必入"],
    "review": ["测评", "实测", "体验", "对比", "真实感受"],
    "story": ["故事", "记录", "日常", "分享", "生活"],
}

_TITLE_EMOJIS = {
    "knowledge": "📚",
    "marketing": "🔥",
    "review": "🔍",
    "story": "✨",
}


# ─── Template-based copy generator ────────────────────────────────────────────

class CopyGenerator:
    """Generate platform-optimized copy from transcript text using templates.

    No external API required — runs entirely locally.
    """

    def generate_copy(
        self,
        transcript_text: str | None,
        description: str | None,
        target_platform: str,
        style: str,
        video_title: str | None = None,
    ) -> GeneratedCopy:
        """Generate copy from transcript + description using template rules."""
        # Collect all available text
        all_text = self._collect_text(transcript_text, description, video_title)
        if not all_text.strip():
            raise LLMServiceError("没有可用的文本内容来生成文案。")

        lines = [l.strip() for l in all_text.split("\n") if l.strip()]

        # Generate each component
        title = self._generate_title(video_title, lines, style, target_platform)
        summary = self._generate_summary(lines, description)
        body = self._generate_body(lines, description, target_platform, style)
        hashtags = self._generate_hashtags(description, lines, style, target_platform)

        return GeneratedCopy(
            title=title,
            summary=summary,
            body=body,
            hashtags=hashtags,
        )

    def _collect_text(
        self,
        transcript_text: str | None,
        description: str | None,
        video_title: str | None,
    ) -> str:
        parts = []
        if video_title:
            parts.append(video_title)
        if transcript_text:
            parts.append(transcript_text)
        if description:
            parts.append(description)
        return "\n".join(parts)

    def _generate_title(
        self,
        video_title: str | None,
        lines: list[str],
        style: str,
        platform: str,
    ) -> str:
        """Generate title from video title or first meaningful line."""
        # Prefer the original video title
        if video_title and len(video_title) > 3:
            # Clean up hashtags from title
            title = re.sub(r"#\S+", "", video_title).strip()
            if not title:
                title = video_title.strip()
        else:
            # Use first non-empty line as title
            title = lines[0] if lines else "视频内容分享"

        # Truncate if too long
        if len(title) > 40:
            title = title[:37] + "..."

        # Add platform emoji
        fmt = _PLATFORM_FORMAT.get(platform, _PLATFORM_FORMAT["xiaohongshu"])
        if fmt.get("emoji_title"):
            emoji = _TITLE_EMOJIS.get(style, "✨")
            title = f"{emoji} {title}"

        return title

    def _generate_summary(self, lines: list[str], description: str | None) -> str:
        """Generate a one-line summary."""
        # Use description if it's a good summary (short and clean)
        if description and len(description) < 80:
            clean = re.sub(r"#\S+", "", description).strip()
            if clean:
                return clean

        # Otherwise, join first 2 meaningful lines
        meaningful = [l for l in lines if len(l) > 5][:2]
        if meaningful:
            summary = "，".join(meaningful)
            if len(summary) > 80:
                summary = summary[:77] + "..."
            return summary

        return lines[0] if lines else ""

    def _generate_body(
        self,
        lines: list[str],
        description: str | None,
        platform: str,
        style: str,
    ) -> str:
        """Generate body text formatted for the target platform."""
        fmt = _PLATFORM_FORMAT.get(platform, _PLATFORM_FORMAT["xiaohongshu"])
        body_style = fmt.get("body_style", "paragraph")

        # Filter out hashtag lines from transcript
        content_lines = [l for l in lines if not l.startswith("#") and len(l) > 1]

        if body_style == "paragraph":
            # Xiaohongshu style: short paragraphs with line breaks
            paragraphs = []
            chunk = []
            for line in content_lines:
                chunk.append(line)
                if len(chunk) >= 3:
                    paragraphs.append(" ".join(chunk))
                    chunk = []
            if chunk:
                paragraphs.append(" ".join(chunk))

            body = "\n\n".join(paragraphs)

            # Add style intro
            style_kw = _STYLE_KEYWORDS.get(style, _STYLE_KEYWORDS["knowledge"])
            intro = f"今天给大家{style_kw[0]}一个超棒的内容～"
            body = f"{intro}\n\n{body}"

        elif body_style == "punchy":
            # Douyin/TikTok style: short punchy lines
            body = "\n".join(content_lines[:8])

        elif body_style == "detailed":
            # Bilibili style: more detailed, with structure
            if len(content_lines) > 4:
                mid = len(content_lines) // 2
                part1 = " ".join(content_lines[:mid])
                part2 = " ".join(content_lines[mid:])
                body = f"{part1}\n\n{part2}"
            else:
                body = " ".join(content_lines)
        else:
            body = "\n".join(content_lines)

        # Append description as extra context if different from transcript
        if description and description.strip() not in body:
            clean_desc = re.sub(r"#\S+", "", description).strip()
            if clean_desc and len(clean_desc) > 5:
                body = f"{body}\n\n💡 {clean_desc}"

        return body

    def _generate_hashtags(
        self,
        description: str | None,
        lines: list[str],
        style: str,
        platform: str,
    ) -> list[str]:
        """Extract and generate hashtags."""
        tags: list[str] = []

        # Extract existing hashtags from description
        if description:
            existing = re.findall(r"#(\S+?)(?:\s|$|#)", description)
            tags.extend(existing)

        # Also check transcript lines for hashtags
        for line in lines:
            found = re.findall(r"#(\S+?)(?:\s|$|#)", line)
            tags.extend(found)

        # Add style-related tags
        style_kw = _STYLE_KEYWORDS.get(style, _STYLE_KEYWORDS["knowledge"])
        tags.extend(style_kw[:2])

        # Add platform-specific generic tags
        platform_tags = {
            "xiaohongshu": ["小红书", "好物分享"],
            "douyin": ["抖音", "热门"],
            "bilibili": ["B站", "干货分享"],
            "tiktok": ["fyp", "viral"],
            "youtube": ["YouTube", "Shorts"],
        }
        tags.extend(platform_tags.get(platform, [])[:1])

        # Deduplicate and limit to 8
        seen = set()
        unique_tags = []
        for tag in tags:
            tag = tag.strip().strip("#")
            if tag and tag not in seen and len(tag) <= 20:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags[:8]


# Singleton instance
copy_generator = CopyGenerator()
