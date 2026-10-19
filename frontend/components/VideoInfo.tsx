import { DownloadIcon, PlayIcon } from "@/components/icons";
import { platformLabel } from "@/lib/platforms";
import type { Video } from "@/lib/types";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "-";
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${minutes}:${rest.toString().padStart(2, "0")}`;
}

type Props = {
  video: Video;
  taskId: string;
};

export function VideoInfo({ video, taskId }: Props) {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001/api";
  const downloadUrl = `${apiBase}/videos/${taskId}/download`;

  return (
    <div className="video-info">
      <div className="video-thumb-wrap">
        {video.thumbnail_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            alt={video.title ?? "视频封面"}
            className="video-thumb"
            referrerPolicy="no-referrer"
            src={video.thumbnail_url}
          />
        ) : (
          <div className="video-thumb video-thumb-empty">
            <PlayIcon />
          </div>
        )}
      </div>

      <div className="video-details">
        <div className="result-tags">
          <span className="platform-pill">{platformLabel(video.platform)}</span>
          <span className="muted-pill">时长 {formatDuration(video.duration)}</span>
        </div>
        <h3>{video.title ?? "未知标题"}</h3>
        <p className="video-author">@{video.author ?? "-"}</p>
        {video.video_id ? <p className="video-id">视频 ID：{video.video_id}</p> : null}
        {video.video_path ? (
          <p className="file-path" title={video.video_path}>
            文件位置：{video.video_path}
          </p>
        ) : null}
        <div className="action-bar">
          <a className="button button-inline" href={downloadUrl}>
            <DownloadIcon />
            下载视频到本地
          </a>
        </div>
      </div>
    </div>
  );
}
