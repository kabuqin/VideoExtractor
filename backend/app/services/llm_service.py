import json
import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratedCopy:
    title: str
    summary: str
    body: str
    hashtags: list[str]


# Platform-specific system prompts
_PLATFORM_PROMPTS = {
    "xiaohongshu": (
        "你是一位小红书文案创作专家。请根据提供的视频内容，创作符合小红书风格的文案。\n"
        "要求：\n"
        "- 标题吸引眼球，可适当使用 emoji\n"
        "- 正文分段短小，每段 2-3 句\n"
        "- 语气亲切自然，像朋友分享\n"
        "- 标签使用 # 号开头，5-8 个相关标签\n"
    ),
    "douyin": (
        "你是一位抖音文案创作专家。请根据提供的视频内容，创作符合抖音风格的文案。\n"
        "要求：\n"
        "- 开头要有钩子句，吸引用户停留\n"
        "- 正文简洁有力，适合短视频配文\n"
        "- 可使用热门话题标签，5-8 个\n"
    ),
    "bilibili": (
        "你是一位 B 站 UP 主文案创作专家。请根据提供的视频内容，创作符合 B 站风格的文案。\n"
        "要求：\n"
        "- 标题有信息量，避免过度标题党\n"
        "- 正文可详细展开，有深度\n"
        "- 语气轻松有趣\n"
        "- 标签 5-8 个，涵盖相关领域\n"
    ),
    "tiktok": (
        "You are a TikTok copywriting expert. Create engaging TikTok-style copy based on the provided video content.\n"
        "Requirements:\n"
        "- Start with a hook to grab attention\n"
        "- Keep it concise and punchy\n"
        "- Use trending hashtags, 5-8 relevant tags\n"
    ),
}

_STYLE_PROMPTS = {
    "knowledge": "风格定位：知识分享型，注重干货输出和专业性，让观众有获得感。",
    "marketing": "风格定位：种草带货型，突出产品亮点和使用体验，激发购买欲望。",
    "review": "风格定位：测评口吻型，客观分析优缺点，给出中肯建议。",
    "story": "风格定位：剧情叙述型，用故事线串联内容，增强代入感。",
}


class LLMService:
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        timeout: int = 0,
    ):
        self.api_key = api_key or settings.llm_api_key
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = timeout or settings.llm_timeout_seconds

    def generate_copy(
        self,
        transcript_text: str | None,
        description: str | None,
        target_platform: str,
        style: str,
        video_title: str | None = None,
    ) -> GeneratedCopy:
        """Call LLM API to generate platform-optimized copy."""
        if not self.api_key:
            raise LLMServiceError(
                "LLM API Key 未配置。请在 backend/.env 中设置 LLM_API_KEY。"
            )

        system_prompt = self._build_system_prompt(target_platform, style)
        user_prompt = self._build_user_prompt(transcript_text, description, video_title)

        content = self._call_llm(system_prompt, user_prompt)
        return self._parse_response(content)

    def _build_system_prompt(self, target_platform: str, style: str) -> str:
        platform_part = _PLATFORM_PROMPTS.get(
            target_platform, _PLATFORM_PROMPTS["xiaohongshu"]
        )
        style_part = _STYLE_PROMPTS.get(style, _STYLE_PROMPTS["knowledge"])
        return (
            f"{platform_part}\n{style_part}\n\n"
            "请务必以 JSON 格式输出，格式如下：\n"
            '{"title": "标题", "summary": "一句话摘要", "body": "正文内容", "hashtags": ["标签1", "标签2"]}\n'
            "只输出 JSON，不要有其他文字。"
        )

    def _build_user_prompt(
        self,
        transcript_text: str | None,
        description: str | None,
        video_title: str | None,
    ) -> str:
        parts: list[str] = []
        if video_title:
            parts.append(f"视频标题：{video_title}")
        if description:
            parts.append(f"视频描述：\n{description}")
        if transcript_text:
            parts.append(f"字幕/语音文本：\n{transcript_text}")

        if not parts:
            raise LLMServiceError("没有可用的文本内容来生成文案。")

        parts.append("\n请根据以上内容创作文案。")
        return "\n\n".join(parts)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make synchronous HTTP request to OpenAI-compatible API."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()

                choices = data.get("choices")
                if not choices:
                    raise LLMServiceError("LLM API 返回空结果。")

                message = choices[0].get("message", {})
                content = message.get("content", "")
                if not content:
                    raise LLMServiceError("LLM API 返回空内容。")

                return content

            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning("LLM API timeout (attempt %d)", attempt + 1)
            except httpx.HTTPStatusError as exc:
                raise LLMServiceError(
                    f"LLM API 请求失败 (HTTP {exc.response.status_code}): "
                    f"{exc.response.text[:200]}"
                ) from exc
            except LLMServiceError:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning("LLM API error (attempt %d): %s", attempt + 1, exc)

        raise LLMServiceError(f"LLM API 调用失败（已重试 2 次）: {last_error}")

    def _parse_response(self, content: str) -> GeneratedCopy:
        """Parse the LLM JSON response into a GeneratedCopy."""
        # Try direct JSON parse
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code block
            match = __import__("re").search(r"```(?:json)?\s*\n?(.*?)\n?```", content, __import__("re").DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except json.JSONDecodeError as exc:
                    raise LLMServiceError(f"无法解析 LLM 返回的 JSON: {exc}") from exc
            else:
                raise LLMServiceError("LLM 返回的内容不是有效的 JSON 格式。")

        return GeneratedCopy(
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            body=data.get("body", ""),
            hashtags=data.get("hashtags", []),
        )


llm_service = LLMService()
