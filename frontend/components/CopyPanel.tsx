import { useState } from "react";

import type { Copy, CopyUpdatePayload } from "@/lib/types";

const PLATFORM_LABELS: Record<string, string> = {
  xiaohongshu: "小红书",
  douyin: "抖音",
  bilibili: "B站",
  tiktok: "TikTok",
};

type Props = {
  copy: Copy;
  onRewrite: () => void;
  onSave: (payload: CopyUpdatePayload) => void;
  isRewriting: boolean;
  isSaving: boolean;
};

export function CopyPanel({ copy, onRewrite, onSave, isRewriting, isSaving }: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(copy.title ?? "");
  const [editSummary, setEditSummary] = useState(copy.summary ?? "");
  const [editBody, setEditBody] = useState(copy.body ?? "");
  const [editHashtags, setEditHashtags] = useState(copy.hashtags.join(", "));

  function handleStartEdit() {
    setEditTitle(copy.title ?? "");
    setEditSummary(copy.summary ?? "");
    setEditBody(copy.body ?? "");
    setEditHashtags(copy.hashtags.join(", "));
    setIsEditing(true);
  }

  function handleCancelEdit() {
    setIsEditing(false);
  }

  function handleSave() {
    onSave({
      title: editTitle,
      summary: editSummary,
      body: editBody,
      hashtags: editHashtags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    });
    setIsEditing(false);
  }

  const platformLabel = PLATFORM_LABELS[copy.platform] ?? copy.platform;

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>AI 文案</h2>
        <span className="platform-tag">{platformLabel}</span>
      </div>

      {isEditing ? (
        <div className="form">
          <div className="field">
            <label>标题</label>
            <input
              onChange={(e) => setEditTitle(e.target.value)}
              type="text"
              value={editTitle}
            />
          </div>
          <div className="field">
            <label>摘要</label>
            <input
              onChange={(e) => setEditSummary(e.target.value)}
              type="text"
              value={editSummary}
            />
          </div>
          <div className="field">
            <label>正文</label>
            <textarea
              className="text-editor"
              onChange={(e) => setEditBody(e.target.value)}
              value={editBody}
            />
          </div>
          <div className="field">
            <label>标签（逗号分隔）</label>
            <input
              onChange={(e) => setEditHashtags(e.target.value)}
              placeholder="标签1, 标签2, 标签3"
              type="text"
              value={editHashtags}
            />
          </div>
          <div className="action-bar">
            <button className="button" disabled={isSaving} onClick={handleSave} type="button">
              {isSaving ? "保存中..." : "保存"}
            </button>
            <button
              className="button button-secondary"
              disabled={isSaving}
              onClick={handleCancelEdit}
              type="button"
            >
              取消
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="copy-section">
            <h3 className="sub-label">标题</h3>
            <p className="copy-text">{copy.title ?? "-"}</p>
          </div>

          <div className="copy-section">
            <h3 className="sub-label">摘要</h3>
            <p className="copy-text">{copy.summary ?? "-"}</p>
          </div>

          <div className="copy-section">
            <h3 className="sub-label">正文</h3>
            <div className="text-display">{copy.body ?? "-"}</div>
          </div>

          {copy.hashtags.length > 0 ? (
            <div className="copy-section">
              <h3 className="sub-label">标签</h3>
              <div className="hashtag-list">
                {copy.hashtags.map((tag, i) => (
                  <span className="hashtag" key={i}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          <div className="action-bar">
            <button
              className="button"
              disabled={isRewriting}
              onClick={onRewrite}
              type="button"
            >
              {isRewriting ? "生成中..." : "重新生成"}
            </button>
            <button
              className="button button-secondary"
              onClick={handleStartEdit}
              type="button"
            >
              编辑文案
            </button>
          </div>
        </>
      )}
    </div>
  );
}
