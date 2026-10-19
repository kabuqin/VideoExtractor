"use client";

import { ClipboardEvent, FormEvent, useState } from "react";

import { ClipboardIcon, SearchIcon, TrashIcon } from "@/components/icons";
import { extractVideoUrl, isSupportedVideoUrl } from "@/lib/url";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onParse: (url: string) => void;
  onClear: () => void;
  isParsing: boolean;
};

export function ParseForm({ value, onChange, onParse, onClear, isParsing }: Props) {
  const [hint, setHint] = useState<string | null>(null);

  function handlePaste(event: ClipboardEvent<HTMLTextAreaElement>) {
    const pasted = event.clipboardData.getData("text");
    const extracted = extractVideoUrl(pasted);
    if (!isSupportedVideoUrl(extracted)) return;

    event.preventDefault();
    setHint(null);
    onChange(extracted);
    onParse(extracted);
  }

  async function handlePasteButton() {
    setHint(null);
    try {
      const text = await navigator.clipboard.readText();
      const extracted = extractVideoUrl(text);
      if (!extracted) {
        setHint("剪贴板是空的，请先复制视频链接。");
        return;
      }
      onChange(extracted);
      if (isSupportedVideoUrl(extracted)) {
        onParse(extracted);
      } else {
        setHint("剪贴板中没有识别到支持的视频链接。");
      }
    } catch {
      setHint("浏览器未授权读取剪贴板，请直接在输入框中粘贴。");
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setHint(null);
    onParse(value);
  }

  return (
    <form className="parse-card" onSubmit={handleSubmit}>
      <div className="parse-input-wrap">
        <textarea
          aria-label="视频链接"
          className="parse-input"
          onChange={(event) => {
            setHint(null);
            onChange(event.target.value);
          }}
          onPaste={handlePaste}
          placeholder="粘贴视频链接，或直接粘贴平台分享文本…"
          rows={3}
          value={value}
        />
        {hint ? <p className="parse-hint">{hint}</p> : null}
      </div>

      <div className="parse-actions">
        <button className="button" disabled={isParsing} type="submit">
          {isParsing ? <span className="spinner spinner-light" /> : <SearchIcon />}
          {isParsing ? "解析中…" : "解析视频"}
        </button>
        <button
          className="button button-secondary"
          disabled={isParsing}
          onClick={handlePasteButton}
          type="button"
        >
          <ClipboardIcon />
          粘贴
        </button>
        <button
          className="button button-secondary"
          disabled={isParsing}
          onClick={() => {
            setHint(null);
            onClear();
          }}
          type="button"
        >
          <TrashIcon />
          清除
        </button>
      </div>
    </form>
  );
}
