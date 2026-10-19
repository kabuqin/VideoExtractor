"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Faq } from "@/components/Faq";
import { BoltIcon, ShieldIcon, SparklesIcon } from "@/components/icons";
import { ParseForm } from "@/components/ParseForm";
import { ParseResultCard } from "@/components/ParseResultCard";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { TaskList } from "@/components/TaskList";
import { createTask, listTasks, parseVideo } from "@/lib/api";
import type { ParseResult, Task } from "@/lib/types";

const PLATFORMS = ["B站", "抖音", "TikTok", "小红书", "YouTube"];

const FEATURES = [
  {
    icon: <BoltIcon />,
    title: "自动解析",
    description:
      "粘贴链接即自动识别平台，解析标题、作者、封面与时长，快速获取无水印视频信息。",
  },
  {
    icon: <ShieldIcon />,
    title: "本地处理",
    description:
      "下载、语音转写与文案生成全部在本机完成，视频和文字数据不会上传到任何服务器。",
  },
  {
    icon: <SparklesIcon />,
    title: "智能文案",
    description:
      "自动将视频语音转成文字，再按小红书、抖音等平台风格生成标题、摘要、正文与标签。",
  },
];

const STEPS = [
  {
    title: "复制视频链接",
    description: "在 B站、抖音、TikTok、小红书或 YouTube 中复制分享链接或整段分享文本。",
  },
  {
    title: "粘贴并解析",
    description: "粘贴到输入框即可自动解析，确认视频信息后可一键创建处理任务。",
  },
  {
    title: "下载与生成文案",
    description: "任务在后台自动运行，完成后可下载视频、查看转录文本并编辑平台文案。",
  },
];

export default function HomePage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<ParseResult | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [targetPlatform, setTargetPlatform] = useState("xiaohongshu");
  const [style, setStyle] = useState("knowledge");
  const [tasks, setTasks] = useState<Task[]>([]);

  const refreshTasks = useCallback(async () => {
    try {
      setTasks(await listTasks());
    } catch {
      // 后端未启动时保持首页可用
    }
  }, []);

  useEffect(() => {
    refreshTasks();
  }, [refreshTasks]);

  const runParse = useCallback(async (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed) {
      setParseError("请先粘贴视频链接。");
      return;
    }

    setIsParsing(true);
    setParseError(null);
    setResult(null);

    try {
      const data = await parseVideo(trimmed);
      if (!data.supported) {
        setParseError(data.error ?? "暂不支持该链接。");
        return;
      }
      setResult(data);
    } catch (err) {
      setParseError(err instanceof Error ? err.message : "解析失败，请稍后重试。");
    } finally {
      setIsParsing(false);
    }
  }, []);

  async function handleCreateTask() {
    if (!result) return;

    setIsCreating(true);
    setParseError(null);

    try {
      const created = await createTask({
        url: result.normalized_url ?? result.source_url,
        target_platform: targetPlatform,
        style,
        language: "auto",
        whisper_model: "small",
        whisper_device: "auto",
      });
      router.push(`/tasks/${created.task_id}`);
    } catch (err) {
      setParseError(err instanceof Error ? err.message : "创建任务失败。");
      setIsCreating(false);
    }
  }

  function handleClear() {
    setUrl("");
    setResult(null);
    setParseError(null);
  }

  return (
    <>
      <SiteHeader />

      <main>
        <section className="hero">
          <div className="hero-glow hero-glow-left" aria-hidden="true" />
          <div className="hero-glow hero-glow-right" aria-hidden="true" />

          <div className="hero-inner">
            <span className="hero-badge">
              <BoltIcon />
              本地运行 · 无需登录 · 完全免费
            </span>
            <h1>免费视频解析去水印工具</h1>
            <p className="hero-sub">
              粘贴视频链接，自动解析无水印视频，支持视频下载、语音转写与平台文案生成。所有处理都在本机完成，无需上传任何内容。
            </p>

            <ParseForm
              isParsing={isParsing}
              onChange={setUrl}
              onClear={handleClear}
              onParse={runParse}
              value={url}
            />

            <div className="platform-row">
              <span className="platform-row-label">已支持</span>
              {PLATFORMS.map((name) => (
                <span className="platform-chip" key={name}>
                  {name}
                </span>
              ))}
            </div>

            {parseError ? <div className="alert alert-error">{parseError}</div> : null}

            {isParsing ? (
              <div className="alert alert-loading">
                <span className="spinner" />
                正在自动解析视频信息，首次解析可能需要几秒…
              </div>
            ) : null}

            {result ? (
              <ParseResultCard
                isCreating={isCreating}
                onCreateTask={handleCreateTask}
                onReparse={() => runParse(url)}
                onStyleChange={setStyle}
                onTargetPlatformChange={setTargetPlatform}
                result={result}
                style={style}
                targetPlatform={targetPlatform}
              />
            ) : null}
          </div>
        </section>

        <section className="section" id="features">
          <h2>一站式完成视频下载与文案创作</h2>
          <p className="section-sub">
            从链接解析到平台文案，全流程本地运行，无需上传视频，也无需调用外部 API。
          </p>
          <div className="feature-grid">
            {FEATURES.map((feature) => (
              <article className="feature-card" key={feature.title}>
                <span className="feature-icon">{feature.icon}</span>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </article>
            ))}
          </div>
        </section>

        <div className="band">
          <section className="section" id="how-it-works">
            <h2>如何使用</h2>
            <p className="section-sub">三步完成视频解析与下载，任务会在后台自动处理。</p>
            <div className="steps">
              {STEPS.map((step, index) => (
                <article className="step-card" key={step.title}>
                  <span className="step-num">{String(index + 1).padStart(2, "0")}</span>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </article>
              ))}
            </div>
          </section>
        </div>

        {tasks.length > 0 ? (
          <section className="section" id="recent">
            <h2>最近任务</h2>
            <p className="section-sub">处理记录保存在本机，点击卡片查看进度与结果。</p>
            <TaskList tasks={tasks.slice(0, 6)} />
          </section>
        ) : null}

        <section className="section" id="faq">
          <h2>常见问题</h2>
          <p className="section-sub">关于解析、下载与本地处理的常见疑问。</p>
          <Faq />
        </section>
      </main>

      <SiteFooter />
    </>
  );
}
