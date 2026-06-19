from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import select

from app.api.deps import DbSession
from app.core.exceptions import UnsupportedPlatformError
from app.models.task import Task, TaskStatus
from app.platforms.resolver import platform_resolver
from app.schemas.task import TaskCreate, TaskCreated, TaskRead
from app.tasks.video_pipeline import run_pipeline

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskCreated, status_code=201)
def create_task(payload: TaskCreate, session: DbSession) -> TaskCreated:
    source_url = str(payload.url)
    try:
        platform_info = platform_resolver.resolve(source_url)
        status = TaskStatus.CHECKING_PLATFORM
        progress = 5
        current_step = "Platform recognized"
        error_message = None
    except UnsupportedPlatformError as exc:
        platform_info = None
        status = TaskStatus.FAILED
        progress = 0
        current_step = "Unsupported platform"
        error_message = exc.message

    task = Task(
        source_url=source_url,
        normalized_url=platform_info.normalized_url if platform_info else None,
        source_platform=platform_info.platform if platform_info else None,
        target_platform=payload.target_platform,
        style=payload.style,
        language=payload.language,
        whisper_model=payload.whisper_model,
        whisper_device=payload.whisper_device,
        status=status,
        progress=progress,
        current_step=current_step,
        error_message=error_message,
        updated_at=datetime.utcnow(),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return TaskCreated(task_id=task.id, status=task.status)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: UUID, session: DbSession) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/start", response_model=TaskRead)
def start_task(
    task_id: UUID, session: DbSession, background_tasks: BackgroundTasks
) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Allow re-running for failed or partially completed tasks
    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Task already completed")
    # Reset error state so pipeline can re-run
    task.error_message = None
    task.status = TaskStatus.CHECKING_PLATFORM
    task.progress = 5
    task.current_step = "重新启动处理"
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    background_tasks.add_task(run_pipeline, task_id)
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(session: DbSession) -> list[Task]:
    statement = select(Task).order_by(Task.created_at.desc())
    return list(session.exec(statement).all())
