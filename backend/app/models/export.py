from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Export(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(index=True)
    format: str
    file_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

