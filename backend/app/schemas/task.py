from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    url: str
    target_platform: str = "xiaohongshu"
    style: str = "knowledge"
    language: str = "auto"
    whisper_model: str = "small"
    whisper_device: str = "auto"


class TaskRead(BaseModel):
    id: UUID
    source_url: str
    normalized_url: str | None
    source_platform: str | None
    target_platform: str
    style: str
    language: str
    whisper_model: str
    whisper_device: str
    status: TaskStatus
    progress: int
    current_step: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class TaskCreated(BaseModel):
    task_id: UUID
    status: TaskStatus

