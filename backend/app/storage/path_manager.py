from pathlib import Path
from uuid import UUID

from app.core.config import settings


class PathManager:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def ensure_storage_dirs(self) -> None:
        for folder in ["videos", "audios", "transcripts", "exports", "models"]:
            (self.storage_root / folder).mkdir(parents=True, exist_ok=True)

    def video_output_template(self, task_id: UUID) -> str:
        self.ensure_storage_dirs()
        task_dir = self.storage_root / "videos" / str(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        return str(task_dir / "%(title).120s-%(id)s.%(ext)s")


path_manager = PathManager(settings.storage_root)

