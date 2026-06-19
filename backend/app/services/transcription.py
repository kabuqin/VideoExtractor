"""Audio extraction and speech-to-text transcription service."""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    segments: list[dict]


class TranscriptionService:
    """Transcribe video/audio to text using faster-whisper.

    Supports direct video file input via the built-in `av` decoder,
    so FFmpeg is not required.
    """

    def __init__(self, model_size: str = "base"):
        self._model_size = model_size
        self._model = None

    def _get_model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info("Loading Whisper model: %s", self._model_size)
                self._model = WhisperModel(
                    self._model_size,
                    device="cpu",
                    compute_type="int8",
                )
                logger.info("Whisper model loaded successfully")
            except ImportError as exc:
                raise RuntimeError(
                    "faster-whisper is not installed. Run: pip install faster-whisper"
                ) from exc
            except Exception as exc:
                raise RuntimeError(f"Failed to load Whisper model: {exc}") from exc
        return self._model

    def transcribe(self, file_path: str) -> TranscriptionResult:
        """Transcribe a video or audio file to text using faster-whisper.

        faster-whisper uses the `av` library internally to decode audio,
        so it can directly accept video files (mp4, mkv, etc.) without FFmpeg.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info("Transcribing file: %s", file_path)
        model = self._get_model()

        try:
            segments, info = model.transcribe(
                str(path),
                beam_size=5,
                language=None,  # Auto-detect language
                vad_filter=True,  # Filter out silence
            )

            # Collect all segments
            segment_list = []
            texts = []
            for segment in segments:
                segment_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                })
                texts.append(segment.text.strip())

            full_text = "\n".join(texts)
            detected_lang = info.language if info.language_probability > 0.5 else None

            logger.info(
                "Transcription complete: %d segments, %d chars, language=%s (prob=%.2f)",
                len(segment_list),
                len(full_text),
                info.language,
                info.language_probability,
            )

            return TranscriptionResult(
                text=full_text,
                language=detected_lang,
                segments=segment_list,
            )

        except Exception as exc:
            raise RuntimeError(f"Transcription failed: {exc}") from exc

    def transcribe_video(self, video_path: str, output_dir: str | None = None) -> TranscriptionResult:
        """Transcribe video file directly to text (no FFmpeg needed)."""
        return self.transcribe(video_path)


# Singleton instance
transcription_service = TranscriptionService()
