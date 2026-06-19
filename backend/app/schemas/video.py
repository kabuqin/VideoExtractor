from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class VideoRead(BaseModel):
    id: UUID
    task_id: UUID
    platform: str | None
    video_id: str | None
    source_url: str | None
    title: str | None
    author: str | None
    duration: int | None
    thumbnail_url: str | None
    video_path: str | None
    audio_path: str | None
    metadata_json: dict[str, Any]
    created_at: datetime

