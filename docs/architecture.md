# Architecture

This project starts as a local single-user application.

## Components

- Frontend: Next.js web UI for task creation, progress tracking, transcript review and export.
- Backend: FastAPI service with SQLite persistence.
- Platform adapters: URL detection and later platform-specific metadata resolution.
- Media pipeline: download video, extract audio, transcribe audio, clean transcript and generate copy.
- Storage: local folders under `storage/` for videos, audios, transcripts, exports and local models.

## Phase 1 Scope

- Task creation and lookup API.
- SQLite task persistence.
- Platform detection for Bilibili, Douyin, TikTok and Xiaohongshu.
- Minimal web interface for creating tasks and viewing status.

## Phase 2 Scope

- `yt-dlp` downloader service.
- Local task video folder allocation.
- Video metadata persistence.
- `POST /api/tasks/{task_id}/start` for the first executable pipeline step.
- `GET /api/videos/{task_id}` for downloaded video metadata.

## Later Pipeline

1. Extract audio with FFmpeg.
2. Transcribe audio with local `faster-whisper`.
3. Segment, punctuate and rewrite transcript text.
4. Generate target-platform copy.
5. Export txt, markdown and docx files.
6. Move long-running execution from synchronous API calls into Celery workers.
