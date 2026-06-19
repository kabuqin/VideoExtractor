from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class Transcript(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(index=True)
    raw_segments: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    raw_text: str | None = None
    segmented_text: str | None = None
    punctuated_text: str | None = None
    rewritten_text: str | None = None
    edited_text: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

