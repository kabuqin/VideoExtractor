import type { Video } from "@/lib/types";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "-";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

type Props = {
  video: Video;
  taskId: string;
};

export function VideoInfo({ video, taskId }: Props) {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001/api";

  function handleDownload() {
    const url = `${apiBase}/videos/${taskId}/download`;
    window.open(url, "_blank");
  }

  return (
    <div className="video-info">
      {video.thumbnail_url ? (
        <img
          alt={video.title ?? "视频封面"}
          className="video-thumb"
          src={video.thumbnail_url}
        />
      ) : null}
      <div className="video-details">
        <h3>{video.title ?? "未知标题"}</h3>
        <div className="task-meta">
          <span>作者：{video.author ?? "-"}</span>
          <span>时长：{formatDuration(video.duration)}</span>
        </div>
        <div className="task-meta">
          <span>平台：{video.platform ?? "-"}</span>
          <span>ID：{video.video_id ?? "-"}</span>
        </div>
        {video.video_path ? (
          <div className="task-meta file-path" title={video.video_path}>
            <span>文件位置：{video.video_path}</span>
          </div>
        ) : null}
        <button className="btn btn-primary" onClick={handleDownload}>
          ⬇ 下载视频到本地
        </button>
      </div>
    </div>
  );
}
