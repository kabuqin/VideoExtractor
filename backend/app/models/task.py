from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    CHECKING_PLATFORM = "checking_platform"
    RESOLVING_URL = "resolving_url"
    DOWNLOADING_VIDEO = "downloading_video"
    VIDEO_DOWNLOADED = "video_downloaded"
    EXTRACTING_AUDIO = "extracting_audio"
    LOADING_WHISPER_MODEL = "loading_whisper_model"
    TRANSCRIBING_AUDIO = "transcribing_audio"
    SEGMENTING_TEXT = "segmenting_text"
    RESTORING_PUNCTUATION = "restoring_punctuation"
    REWRITING_TEXT = "rewriting_text"
    GENERATING_COPY = "generating_copy"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_url: str
    normalized_url: str | None = None
    source_platform: str | None = None
    target_platform: str = "xiaohongshu"
    style: str = "knowledge"
    language: str = "auto"
    whisper_model: str = "small"
    whisper_device: str = "auto"
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True)
    progress: int = 0
    current_step: str | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
