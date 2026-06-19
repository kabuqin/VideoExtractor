import type { Transcript } from "@/lib/types";

type Props = {
  transcript: Transcript;
  isEditing: boolean;
  editText: string;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSave: () => void;
  onTextChange: (text: string) => void;
  isSaving: boolean;
};

export function TranscriptPanel({
  transcript,
  isEditing,
  editText,
  onStartEdit,
  onCancelEdit,
  onSave,
  onTextChange,
  isSaving,
}: Props) {
  const displayText = transcript.edited_text ?? transcript.raw_text;
  const isEdited = !!transcript.edited_text;

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>提取文本</h2>
        {isEdited ? <span className="edited-badge">已手动编辑</span> : null}
      </div>

      {isEditing ? (
        <>
          <textarea
            className="text-editor"
            onChange={(e) => onTextChange(e.target.value)}
            value={editText}
          />
          <div className="action-bar">
            <button
              className="button"
              disabled={isSaving}
              onClick={onSave}
              type="button"
            >
              {isSaving ? "保存中..." : "保存"}
            </button>
            <button
              className="button button-secondary"
              disabled={isSaving}
              onClick={onCancelEdit}
              type="button"
            >
              取消
            </button>
          </div>
        </>
      ) : (
        <>
          {displayText ? (
            <div className="text-display">{displayText}</div>
          ) : (
            <p className="task-meta">暂未提取到文本，请重新运行任务。</p>
          )}

          {transcript.segmented_text ? (
            <>
              <h3 className="sub-label">视频描述</h3>
              <div className="text-display text-display-sm">
                {transcript.segmented_text}
              </div>
            </>
          ) : null}

          <div className="action-bar">
            <button className="button button-secondary" onClick={onStartEdit} type="button">
              编辑文本
            </button>
          </div>
        </>
      )}
    </div>
  );
}
