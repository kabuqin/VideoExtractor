"use client";

import { useEffect, useState } from "react";

import { TaskForm } from "@/components/TaskForm";
import { TaskList } from "@/components/TaskList";
import { listTasks } from "@/lib/api";
import type { Task } from "@/lib/types";

export default function HomePage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refreshTasks() {
    try {
      setError(null);
      setTasks(await listTasks());
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取任务列表失败");
    }
  }

  useEffect(() => {
    refreshTasks();
  }, []);

  return (
    <main className="page">
      <div className="shell">
        <header className="topbar">
          <div className="brand">
            <h1>短视频文案生成器</h1>
            <p>本地解析、识别字幕、整理文案，优先支持 B站 / 抖音 / TikTok / 小红书。</p>
          </div>
        </header>

        <section className="grid">
          <div className="panel">
            <h2>新建任务</h2>
            <TaskForm onCreated={refreshTasks} />
          </div>

          <div className="panel">
            <h2>任务记录</h2>
            {error ? <div className="error">{error}</div> : <TaskList tasks={tasks} />}
          </div>
        </section>
      </div>
    </main>
  );
}

