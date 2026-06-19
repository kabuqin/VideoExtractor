from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class Copy(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(index=True)
    title: str | None = None
    summary: str | None = None
    body: str | None = None
    hashtags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    platform: str = "xiaohongshu"
    style: str = "knowledge"
    prompt_version: str = "v1"
    created_at: datetime = Field(default_factory=datetime.utcnow)

