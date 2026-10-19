"use client";

import { BoltIcon, SearchIcon } from "@/components/icons";
import { platformLabel } from "@/lib/platforms";
import type { ParseResult } from "@/lib/types";

function formatDuration(seconds: number | null): string | null {
  if (!seconds || seconds <= 0) return null;
  const minutes = Math.floor(seconds / 60);
  const rest = Math.floor(seconds % 60);
  return `${minutes}:${rest.toString().padStart(2, "0")}`;
}

type Props = {
  result: ParseResult;
  targetPlatform: string;
  style: string;
  isCreating: boolean;
  onTargetPlatformChange: (value: string) => void;
  onStyleChange: (value: string) => void;
  onCreateTask: () => void;
  onReparse: () => void;
};

export function ParseResultCard({
  result,
  targetPlatform,
  style,
  isCreating,
  onTargetPlatformChange,
  onStyleChange,
  onCreateTask,
  onReparse,
}: Props) {
  const duration = formatDuration(result.duration);
  const name = platformLabel(result.platform);

  return (
    <section className="result-card">
      <div className="result-main">
        <div className="result-thumb-wrap">
          {result.thumbnail_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              alt={result.title ?? "视频封面"}
              className="result-thumb"
              referrerPolicy="no-referrer"
              src={result.thumbnail_url}
            />
          ) : (
            <div className="result-thumb result-thumb-empty">▶</div>
          )}
          {duration ? <span className="duration-badge">{duration}</span> : null}
        </div>

        <div className="result-body">
          <div className="result-tags">
            <span className="platform-pill">{name}</span>
            <span className="muted-pill">已解析</span>
          </div>
          <h3>{result.title || "视频解析完成"}</h3>
          <p className="result-author">@{result.author || "未知作者"}</p>
          {result.description ? <p className="result-desc">{result.description}</p> : null}
          {result.error ? (
            <div className="alert alert-warn">
              {result.error}
              <br />
              仍可继续创建任务，后台会再次尝试解析与下载。
            </div>
          ) : null}
        </div>
      </div>

      <div className="result-divider" />

      <div className="result-footer">
        <div className="result-options">
          <label className="mini-field">
            <span>文案平台</span>
            <select
              onChange={(event) => onTargetPlatformChange(event.target.value)}
              value={targetPlatform}
            >
              <option value="xiaohongshu">小红书</option>
              <option value="douyin">抖音</option>
              <option value="bilibili">B站</option>
              <option value="tiktok">TikTok</option>
              <option value="youtube">YouTube</option>
            </select>
          </label>
          <label className="mini-field">
            <span>文案风格</span>
            <select onChange={(event) => onStyleChange(event.target.value)} value={style}>
              <option value="knowledge">知识分享</option>
              <option value="marketing">种草带货</option>
              <option value="review">测评口吻</option>
              <option value="story">剧情叙述</option>
            </select>
          </label>
        </div>

        <div className="result-buttons">
          <button className="button" disabled={isCreating} onClick={onCreateTask} type="button">
            {isCreating ? <span className="spinner spinner-light" /> : <BoltIcon />}
            {isCreating ? "创建任务中…" : "开始下载并提取文案"}
          </button>
          <button
            className="button button-secondary"
            disabled={isCreating}
            onClick={onReparse}
            type="button"
          >
            <SearchIcon />
            重新解析
          </button>
        </div>
      </div>
    </section>
  );
}
