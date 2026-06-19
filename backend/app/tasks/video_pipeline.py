import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlmodel import Session, select

from app.core.exceptions import AppError, LLMServiceError
from app.db.session import engine
from app.models.copy import Copy
from app.models.task import Task, TaskStatus
from app.models.transcript import Transcript
from app.models.video import Video
from app.services.copy_generator import copy_generator
from app.services.downloader import DownloadedVideo, downloader
from app.services.transcription import transcription_service

logger = logging.getLogger(__name__)


def run_pipeline(task_id: UUID) -> Task:
    """Run the full pipeline: download → extract audio → transcribe → save transcript → generate copy."""
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        try:
            # Check if video is already downloaded (for re-run scenarios)
            existing_video = session.exec(select(Video).where(Video.task_id == task.id)).first()
            skip_download = (
                existing_video
                and existing_video.video_path
                and Path(existing_video.video_path).exists()
            )

            if skip_download:
                logger.info("Video already downloaded, skipping download: %s", existing_video.video_path)
                video = existing_video
                _update_task(session, task, TaskStatus.VIDEO_DOWNLOADED, 40, "视频已存在，跳过下载")

                # Build a minimal DownloadedVideo for downstream use
                downloaded = DownloadedVideo(
                    title=video.title,
                    author=video.author,
                    duration=video.duration,
                    thumbnail_url=video.thumbnail_url,
                    video_path=video.video_path,
                    description=(video.metadata_json or {}).get("description"),
                    metadata=video.metadata_json or {},
                )
            else:
                # Step 1: Resolve metadata and download video
                _update_task(session, task, TaskStatus.RESOLVING_URL, 10, "解析视频元数据")
                downloaded = downloader.download(task.normalized_url or task.source_url, task.id)

                _update_task(session, task, TaskStatus.DOWNLOADING_VIDEO, 30, "下载视频")

                # Step 2: Save video record
                video = existing_video or Video(task_id=task.id)
                video.platform = task.source_platform
                video.source_url = task.normalized_url or task.source_url
                video.video_id = downloaded.metadata.get("id")
                video.title = downloaded.title
                video.author = downloaded.author
                video.duration = downloaded.duration
                video.thumbnail_url = downloaded.thumbnail_url
                video.video_path = downloaded.video_path
                video.metadata_json = downloaded.metadata
                session.add(video)

                _update_task(
                    session, task, TaskStatus.VIDEO_DOWNLOADED, 40, "视频下载完成"
                )

            # Step 3: Transcribe video audio to text
            _update_task(
                session, task, TaskStatus.EXTRACTING_AUDIO, 50, "提取音频并转文字"
            )
            description_text = downloaded.description or ""
            transcribed_text = ""

            if downloaded.video_path:
                try:
                    _update_task(
                        session, task, TaskStatus.TRANSCRIBING_AUDIO, 55, "语音转文字（首次加载模型较慢）"
                    )
                    result = transcription_service.transcribe_video(downloaded.video_path)
                    transcribed_text = result.text
                    logger.info("Transcription complete: %d chars", len(transcribed_text))
                except Exception as exc:
                    logger.warning("Audio transcription failed: %s", exc)
                    transcribed_text = _extract_subtitle_text(downloaded.subtitle_paths)
                    if not transcribed_text:
                        logger.error("Both transcription and subtitle extraction failed")
            else:
                transcribed_text = _extract_subtitle_text(downloaded.subtitle_paths)

            # Step 4: Save Transcript
            _update_task(
                session, task, TaskStatus.TRANSCRIBING_AUDIO, 65, "保存转录文本"
            )
            existing_transcript = session.exec(
                select(Transcript).where(Transcript.task_id == task.id)
            ).first()
            transcript = existing_transcript or Transcript(task_id=task.id)
            transcript.raw_text = transcribed_text or None
            transcript.segmented_text = description_text or None
            transcript.updated_at = datetime.utcnow()
            session.add(transcript)
            session.commit()

            # Step 5: Generate copy
            _update_task(
                session, task, TaskStatus.GENERATING_COPY, 75, "生成文案"
            )

            try:
                generated = copy_generator.generate_copy(
                    transcript_text=transcribed_text,
                    description=description_text,
                    target_platform=task.target_platform,
                    style=task.style,
                    video_title=downloaded.title,
                )

                # Step 6: Save Copy and mark completed
                existing_copy = session.exec(
                    select(Copy).where(Copy.task_id == task.id)
                ).first()
                copy = existing_copy or Copy(task_id=task.id)
                copy.title = generated.title
                copy.summary = generated.summary
                copy.body = generated.body
                copy.hashtags = generated.hashtags
                copy.platform = task.target_platform
                copy.style = task.style
                session.add(copy)

                task.completed_at = datetime.utcnow()
                _update_task(
                    session, task, TaskStatus.COMPLETED, 100, "处理完成"
                )
            except LLMServiceError as exc:
                logger.warning("Copy generation failed: %s", exc.message)
                _update_task(
                    session,
                    task,
                    TaskStatus.VIDEO_DOWNLOADED,
                    65,
                    f"转录已保存，但文案生成失败：{exc.message}",
                )

            session.refresh(task)
            return task

        except AppError as exc:
            _fail_task(session, task, exc.message)
            session.refresh(task)
            return task
        except Exception as exc:
            _fail_task(session, task, f"管线错误：{exc}")
            session.refresh(task)
            return task


def _extract_subtitle_text(subtitle_paths: list[str]) -> str:
    """Extract plain text from subtitle files (fallback method)."""
    if not subtitle_paths:
        return ""

    for path in subtitle_paths:
        try:
            text = downloader.extract_subtitles_text(path)
            if text.strip():
                return text
        except Exception as exc:
            logger.warning("Failed to parse subtitle %s: %s", path, exc)
            continue

    return ""


def _update_task(
    session: Session,
    task: Task,
    status: TaskStatus,
    progress: int,
    current_step: str,
) -> None:
    task.status = status
    task.progress = progress
    task.current_step = current_step
    task.error_message = None
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()


def _fail_task(session: Session, task: Task, message: str) -> None:
    task.status = TaskStatus.FAILED
    task.current_step = "管线失败"
    task.error_message = message
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
