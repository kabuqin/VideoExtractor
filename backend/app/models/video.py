from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class Video(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(index=True)
    platform: str | None = None
    video_id: str | None = None
    source_url: str | None = None
    title: str | None = None
    author: str | None = None
    duration: int | None = None
    thumbnail_url: str | None = None
    video_path: str | None = None
    audio_path: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
