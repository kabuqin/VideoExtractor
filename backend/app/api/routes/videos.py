from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import select

from app.api.deps import DbSession
from app.models.video import Video
from app.schemas.video import VideoRead

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/{task_id}", response_model=VideoRead)
def get_video_by_task(task_id: UUID, session: DbSession) -> Video:
    video = session.exec(select(Video).where(Video.task_id == task_id)).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{task_id}/download")
def download_video_file(task_id: UUID, session: DbSession) -> FileResponse:
    """Download the video file to local machine."""
    video = session.exec(select(Video).where(Video.task_id == task_id)).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if not video.video_path:
        raise HTTPException(status_code=404, detail="Video file path not available")

    file_path = Path(video.video_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    filename = file_path.name
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4",
    )

