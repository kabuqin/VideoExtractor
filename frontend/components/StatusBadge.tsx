import type { TaskStatus } from "@/lib/types";

const STATUS_LABELS: Record<TaskStatus, string> = {
  pending: "等待中",
  checking_platform: "识别平台",
  resolving_url: "解析地址",
  downloading_video: "下载视频中",
  video_downloaded: "视频已下载",
  extracting_audio: "提取字幕中",
  loading_whisper_model: "加载模型中",
  transcribing_audio: "保存转录中",
  segmenting_text: "分段文本中",
  restoring_punctuation: "恢复标点中",
  rewriting_text: "改写文本中",
  generating_copy: "生成文案中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
};

type Props = {
  status: TaskStatus;
};

export function StatusBadge({ status }: Props) {
  const label = STATUS_LABELS[status] ?? status;
  const isFailed = status === "failed";
  const isCompleted = status === "completed";

  return (
    <span
      className="status"
      style={{
        background: isFailed ? "#fef3f2" : isCompleted ? "#ecfdf5" : undefined,
        color: isFailed ? "#b42318" : isCompleted ? "#065f46" : undefined,
      }}
    >
      {label}
    </span>
  );
}
