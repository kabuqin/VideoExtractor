from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import DbSession
from app.models.transcript import Transcript

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


class TranscriptRead(BaseModel):
    id: UUID
    task_id: UUID
    raw_text: str | None
    segmented_text: str | None
    punctuated_text: str | None
    rewritten_text: str | None
    edited_text: str | None
    created_at: datetime
    updated_at: datetime


class TranscriptUpdate(BaseModel):
    edited_text: str


@router.get("/{task_id}", response_model=TranscriptRead)
def get_transcript(task_id: UUID, session: DbSession) -> Transcript:
    transcript = session.exec(
        select(Transcript).where(Transcript.task_id == task_id)
    ).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript


@router.put("/{task_id}", response_model=TranscriptRead)
def update_transcript(
    task_id: UUID, payload: TranscriptUpdate, session: DbSession
) -> Transcript:
    transcript = session.exec(
        select(Transcript).where(Transcript.task_id == task_id)
    ).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    transcript.edited_text = payload.edited_text
    transcript.updated_at = datetime.utcnow()
    session.add(transcript)
    session.commit()
    session.refresh(transcript)
    return transcript
