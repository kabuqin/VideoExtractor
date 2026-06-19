from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import DbSession
from app.core.exceptions import LLMServiceError
from app.models.copy import Copy
from app.models.task import Task
from app.models.transcript import Transcript
from app.models.video import Video
from app.services.copy_generator import copy_generator

router = APIRouter(prefix="/copies", tags=["copies"])


class CopyRead(BaseModel):
    id: UUID
    task_id: UUID
    title: str | None
    summary: str | None
    body: str | None
    hashtags: list[str]
    platform: str
    style: str
    prompt_version: str
    created_at: datetime


class CopyUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    body: str | None = None
    hashtags: list[str] | None = None


class RewriteRequest(BaseModel):
    target_platform: str | None = None
    style: str | None = None
    use_edited_transcript: bool = False


@router.get("/{task_id}", response_model=CopyRead)
def get_copy(task_id: UUID, session: DbSession) -> Copy:
    copy = session.exec(select(Copy).where(Copy.task_id == task_id)).first()
    if not copy:
        raise HTTPException(status_code=404, detail="Copy not found")
    return copy


@router.put("/{task_id}", response_model=CopyRead)
def update_copy(task_id: UUID, payload: CopyUpdate, session: DbSession) -> Copy:
    copy = session.exec(select(Copy).where(Copy.task_id == task_id)).first()
    if not copy:
        raise HTTPException(status_code=404, detail="Copy not found")

    if payload.title is not None:
        copy.title = payload.title
    if payload.summary is not None:
        copy.summary = payload.summary
    if payload.body is not None:
        copy.body = payload.body
    if payload.hashtags is not None:
        copy.hashtags = payload.hashtags

    session.add(copy)
    session.commit()
    session.refresh(copy)
    return copy


@router.post("/{task_id}/rewrite", response_model=CopyRead)
def rewrite_copy(task_id: UUID, payload: RewriteRequest, session: DbSession) -> Copy:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get transcript
    transcript = session.exec(
        select(Transcript).where(Transcript.task_id == task_id)
    ).first()

    # Get video for title
    video = session.exec(select(Video).where(Video.task_id == task_id)).first()

    # Determine text input
    subtitle_text = None
    description_text = None
    if transcript:
        if payload.use_edited_transcript and transcript.edited_text:
            subtitle_text = transcript.edited_text
        else:
            subtitle_text = transcript.raw_text
        description_text = transcript.segmented_text

    target_platform = payload.target_platform or task.target_platform
    style = payload.style or task.style

    try:
        generated = copy_generator.generate_copy(
            transcript_text=subtitle_text,
            description=description_text,
            target_platform=target_platform,
            style=style,
            video_title=video.title if video else None,
        )
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc

    # Update or create copy
    copy = session.exec(select(Copy).where(Copy.task_id == task_id)).first()
    if not copy:
        copy = Copy(task_id=task_id)
    copy.title = generated.title
    copy.summary = generated.summary
    copy.body = generated.body
    copy.hashtags = generated.hashtags
    copy.platform = target_platform
    copy.style = style
    session.add(copy)
    session.commit()
    session.refresh(copy)
    return copy
