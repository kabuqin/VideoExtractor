"use client";

import { FormEvent, useState, ClipboardEvent } from "react";

import { createTask } from "@/lib/api";

/** Extract first video URL from arbitrary text (handles Douyin share text etc.) */
function extractUrl(text: string): string {
  const patterns = [
    /https?:\/\/v\.douyin\.com\/[\w-]+\/?/,
    /https?:\/\/www\.douyin\.com\/video\/[\d]+/,
    /https?:\/\/www\.bilibili\.com\/video\/BV[\w]+/,
    /https?:\/\/b23\.tv\/[\w]+/,
    /https?:\/\/www\.tiktok\.com\/@[\w.]+\/video\/[\d]+/,
    /https?:\/\/www\.xiaohongshu\.com\/explore\/[\w]+/,
    /https?:\/\/www\.youtube\.com\/watch\?v=[\w-]+/,
    /https?:\/\/youtu\.be\/[\w-]+/,
  ];
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return match[0];
  }
  return text;
}

type Props = {
  onCreated: () => void;
};

export function TaskForm({ onCreated }: Props) {
  const [url, setUrl] = useState("");
  const [targetPlatform, setTargetPlatform] = useState("xiaohongshu");
  const [style, setStyle] = useState("knowledge");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await createTask({
        url,
        target_platform: targetPlatform,
        style,
        language: "auto",
        whisper_model: "small",
        whisper_device: "auto",
      });
      setUrl("");
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建任务失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="url">视频链接</label>
        <input
          id="url"
          placeholder="粘贴 B站 / 抖音 / TikTok / 小红书链接（支持直接粘贴分享文本）"
          required
          type="text"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          onPaste={(event: ClipboardEvent<HTMLInputElement>) => {
            const pasted = event.clipboardData.getData("text");
            const extracted = extractUrl(pasted);
            if (extracted !== pasted) {
              event.preventDefault();
              setUrl(extracted);
            }
          }}
        />
      </div>

      <div className="row">
        <div className="field">
          <label htmlFor="target_platform">目标平台</label>
          <select
            id="target_platform"
            value={targetPlatform}
            onChange={(event) => setTargetPlatform(event.target.value)}
          >
            <option value="xiaohongshu">小红书</option>
            <option value="douyin">抖音</option>
            <option value="bilibili">B站</option>
            <option value="tiktok">TikTok</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="style">文案风格</label>
          <select id="style" value={style} onChange={(event) => setStyle(event.target.value)}>
            <option value="knowledge">知识分享</option>
            <option value="marketing">种草带货</option>
            <option value="review">测评口吻</option>
            <option value="story">剧情叙述</option>
          </select>
        </div>
      </div>

      {error ? <div className="error">{error}</div> : null}

      <button className="button" disabled={isSubmitting} type="submit">
        {isSubmitting ? "创建中..." : "创建任务"}
      </button>
    </form>
  );
}
