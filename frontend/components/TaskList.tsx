"use client";

import Link from "next/link";

import type { Task } from "@/lib/types";

type Props = {
  tasks: Task[];
};

export function TaskList({ tasks }: Props) {
  if (tasks.length === 0) {
    return <p className="task-meta">暂无任务，提交一个视频链接开始。</p>;
  }

  return (
    <div className="task-list">
      {tasks.map((task) => (
        <Link className="task-item" href={`/tasks/${task.id}`} key={task.id}>
          <div className="task-meta">
            <span>{task.source_platform ?? "unknown"}</span>
            <span>{new Date(task.created_at).toLocaleString()}</span>
          </div>
          <strong>{task.source_url}</strong>
          <span className="status">{task.status}</span>
          <div className="progress" aria-label={`progress ${task.progress}%`}>
            <span style={{ width: `${task.progress}%` }} />
          </div>
          {task.error_message ? <span className="error">{task.error_message}</span> : null}
        </Link>
      ))}
    </div>
  );
}

