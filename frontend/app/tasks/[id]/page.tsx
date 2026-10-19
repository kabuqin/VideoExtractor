"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { CopyPanel } from "@/components/CopyPanel";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { StatusBadge } from "@/components/StatusBadge";
import { TranscriptPanel } from "@/components/TranscriptPanel";
import { VideoInfo } from "@/components/VideoInfo";
import {
  getCopy,
  getTask,
  getTranscript,
  getVideo,
  rewriteCopy,
  startTask,
  updateCopy,
  updateTranscript,
} from "@/lib/api";
import { platformLabel } from "@/lib/platforms";
import type { Copy, CopyUpdatePayload, Task, Transcript, Video } from "@/lib/types";

const STYLE_LABELS: Record<string, string> = {
  knowledge: "知识分享",
  marketing: "种草带货",
  review: "测评口吻",
  story: "剧情叙述",
};

export default function TaskDetailPage({ params }: { params: { id: string } }) {
  const [task, setTask] = useState<Task | null>(null);
  const [video, setVideo] = useState<Video | null>(null);
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [copy, setCopy] = useState<Copy | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  // Transcript editing state
  const [isEditingTranscript, setIsEditingTranscript] = useState(false);
  const [editTranscriptText, setEditTranscriptText] = useState("");
  const [isSavingTranscript, setIsSavingTranscript] = useState(false);

  // Copy state
  const [isRewriting, setIsRewriting] = useState(false);
  const [isSavingCopy, setIsSavingCopy] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const taskData = await getTask(params.id);
      setTask(taskData);

      const videoData = await getVideo(params.id);
      setVideo(videoData);

      // Load transcript and copy when pipeline has progressed far enough
      const activeStatuses = [
        "transcribing_audio",
        "generating_copy",
        "completed",
        "video_downloaded",
      ];
      if (taskData.progress >= 50 || activeStatuses.includes(taskData.status)) {
        const [transcriptData, copyData] = await Promise.all([
          getTranscript(params.id),
          getCopy(params.id),
        ]);
        setTranscript(transcriptData);
        setCopy(copyData);
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取任务失败");
    }
  }, [params.id]);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      if (isMounted) await loadData();
    }

    load();
    const timer = window.setInterval(load, 3000);

    return () => {
      isMounted = false;
      window.clearInterval(timer);
    };
  }, [loadData]);

  async function handleStart() {
    setIsStarting(true);
    setError(null);

    try {
      await startTask(params.id);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "启动任务失败");
    } finally {
      setIsStarting(false);
    }
  }

  // Transcript edit handlers
  function handleStartEditTranscript() {
    setEditTranscriptText(transcript?.edited_text ?? transcript?.raw_text ?? "");
    setIsEditingTranscript(true);
  }

  function handleCancelEditTranscript() {
    setIsEditingTranscript(false);
  }

  async function handleSaveTranscript() {
    if (!transcript) return;
    setIsSavingTranscript(true);
    try {
      const updated = await updateTranscript(transcript.task_id, {
        edited_text: editTranscriptText,
      });
      setTranscript(updated);
      setIsEditingTranscript(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存文本失败");
    } finally {
      setIsSavingTranscript(false);
    }
  }

  // Copy handlers
  async function handleRewriteCopy() {
    setIsRewriting(true);
    setError(null);
    try {
      const updated = await rewriteCopy(params.id, {
        use_edited_transcript: !!transcript?.edited_text,
      });
      setCopy(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新生成文案失败");
    } finally {
      setIsRewriting(false);
    }
  }

  async function handleSaveCopy(payload: CopyUpdatePayload) {
    setIsSavingCopy(true);
    try {
      const updated = await updateCopy(params.id, payload);
      setCopy(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存文案失败");
    } finally {
      setIsSavingCopy(false);
    }
  }

  const showStartButton = task && (task.status === "pending" || task.status === "failed");
  const isActive =
    task &&
    !["completed", "failed", "cancelled", "video_downloaded", "pending", "checking_platform"].includes(
      task.status,
    );

  return (
    <>
      <SiteHeader />
      <main className="detail-page">
        <div className="detail-shell">
          <div className="breadcrumb">
            <Link href="/">首页</Link>
            <span className="sep">/</span>
            <span>任务详情</span>
          </div>

          <div className="detail-heading">
            <div>
              <h1>处理详情</h1>
              <p className="detail-subtitle">任务 ID：{params.id}</p>
            </div>
            <Link className="button button-secondary" href="/">
              返回首页
            </Link>
          </div>

          {error ? <div className="error">{error}</div> : null}

          {task ? (
            <div className="detail-stack">
              <section className="panel">
                <div className="status-row">
                  <StatusBadge status={task.status} />
                  <span className="current-step">{task.current_step ?? "-"}</span>
                  <span className="muted-pill" style={{ marginLeft: "auto" }}>
                    {task.progress}%
                  </span>
                </div>

                <div className="progress" aria-label={`progress ${task.progress}%`}>
                  <span style={{ width: `${task.progress}%` }} />
                </div>

                <div className="task-meta" style={{ marginTop: 14 }}>
                  <span>来源：{platformLabel(task.source_platform)}</span>
                  <span>目标：{platformLabel(task.target_platform)}</span>
                  <span>风格：{STYLE_LABELS[task.style] ?? task.style}</span>
                </div>

                <strong className="source-url">{task.source_url}</strong>

                {task.error_message ? <div className="error">{task.error_message}</div> : null}

                {showStartButton ? (
                  <div className="action-bar">
                    <button
                      className="button"
                      disabled={isStarting}
                      onClick={handleStart}
                      type="button"
                    >
                      {isStarting
                        ? "启动中..."
                        : task.status === "failed"
                          ? "重试任务"
                          : "开始处理"}
                    </button>
                  </div>
                ) : null}

                {isActive ? (
                  <p className="polling-hint">任务正在后台自动处理，页面会自动刷新进度…</p>
                ) : null}
              </section>

              {video ? (
                <section className="panel">
                  <h2>视频信息</h2>
                  <VideoInfo video={video} taskId={params.id} />
                </section>
              ) : isActive ? (
                <section className="panel">
                  <h2>视频信息</h2>
                  <p className="task-meta">正在解析并下载视频，请稍候…</p>
                </section>
              ) : null}

              {transcript || copy ? (
                <div className="editor-grid">
                  {transcript ? (
                    <TranscriptPanel
                      editText={editTranscriptText}
                      isEditing={isEditingTranscript}
                      isSaving={isSavingTranscript}
                      onCancelEdit={handleCancelEditTranscript}
                      onSave={handleSaveTranscript}
                      onStartEdit={handleStartEditTranscript}
                      onTextChange={setEditTranscriptText}
                      transcript={transcript}
                    />
                  ) : (
                    <div className="panel">
                      <h2>提取文本</h2>
                      <p className="task-meta">正在提取中…</p>
                    </div>
                  )}

                  {copy ? (
                    <CopyPanel
                      copy={copy}
                      isRewriting={isRewriting}
                      isSaving={isSavingCopy}
                      onRewrite={handleRewriteCopy}
                      onSave={handleSaveCopy}
                    />
                  ) : (
                    <div className="panel">
                      <h2>平台文案</h2>
                      <p className="task-meta">
                        {task.status === "generating_copy" ? "正在生成文案…" : "文案暂未生成。"}
                      </p>
                      {transcript ? (
                        <div className="action-bar">
                          <button
                            className="button"
                            disabled={isRewriting}
                            onClick={handleRewriteCopy}
                            type="button"
                          >
                            {isRewriting ? "生成中..." : "手动生成文案"}
                          </button>
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          ) : (
            <p className="empty-hint">加载中…</p>
          )}
        </div>
        <SiteFooter />
      </main>
    </>
  );
}
