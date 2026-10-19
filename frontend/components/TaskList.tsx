import Link from "next/link";

import { StatusBadge } from "@/components/StatusBadge";
import { platformLabel } from "@/lib/platforms";
import type { Task } from "@/lib/types";

type Props = {
  tasks: Task[];
};

export function TaskList({ tasks }: Props) {
  if (tasks.length === 0) {
    return <p className="empty-hint">暂无任务，提交一个视频链接开始。</p>;
  }

  return (
    <div className="task-list">
      {tasks.map((task) => (
        <Link className="task-card" href={`/tasks/${task.id}`} key={task.id}>
          <div className="task-card-top">
            <span className="platform-pill">{platformLabel(task.source_platform)}</span>
            <StatusBadge status={task.status} />
          </div>
          <p className="task-url">{task.source_url}</p>
          <div className="progress" aria-label={`progress ${task.progress}%`}>
            <span style={{ width: `${task.progress}%` }} />
          </div>
          <div className="task-card-meta">
            <span>{new Date(task.created_at).toLocaleString()}</span>
            <span>{task.progress}%</span>
          </div>
          {task.error_message ? <p className="task-error">{task.error_message}</p> : null}
        </Link>
      ))}
    </div>
  );
}
