# 短视频文案生成器

本地单用户短视频文案生成工具。输入视频链接，自动下载视频、语音转文字、生成平台文案，全流程本地运行，无需外部 API。

## 功能特性

- **多平台支持**：B站 / 抖音 / TikTok / 小红书链接自动识别
- **视频下载**：使用 yt-dlp 下载公开视频，保存元数据（标题、作者、时长、封面）
- **语音转文字**：使用 faster-whisper 本地模型将视频音频转为文字（无需 FFmpeg）
- **文案生成**：基于模板规则自动生成平台风格文案（标题、摘要、正文、标签），无需 AI API
- **文案编辑**：支持手动编辑提取文本和生成的文案
- **视频下载**：一键将已下载视频保存到本地
- **任务重跑**：视频已下载时自动跳过下载，直接重新转录或生成文案

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | SQLite + SQLModel |
| 视频下载 | yt-dlp |
| 语音识别 | faster-whisper（本地模型，CPU int8 量化） |
| 文案生成 | 模板规则引擎（本地，无需 API） |
| 前端 | Next.js 14 + React + TypeScript |

## 快速开始

### 1. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -e .
uvicorn app.main:app --reload --port 8001
```

后端地址：http://localhost:8001  
健康检查：http://localhost:8001/health  
API 文档：http://localhost:8001/docs

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：http://localhost:3000

### 3. 使用流程

1. 在首页输入视频链接（如 `https://v.douyin.com/xxx/`）
2. 点击"开始处理"，系统自动执行：
   - 解析视频元数据
   - 下载视频文件
   - 提取音频并语音转文字
   - 生成平台风格文案
3. 在任务详情页查看：
   - 视频信息（封面、标题、作者、时长、文件位置）
   - 提取文本（语音转文字结果，可编辑）
   - AI 文案（标题、摘要、正文、标签，可编辑/重新生成）
4. 点击"下载视频到本地"保存视频文件

## 项目结构

```text
backend/
  app/
    api/routes/      FastAPI 路由（tasks, videos, transcripts, copies）
    core/            配置和异常定义
    db/              数据库连接
    models/          SQLModel 数据模型（Task, Video, Transcript, Copy）
    platforms/       平台识别适配器（B站/抖音/TikTok/小红书）
    schemas/         API 请求/响应 Schema
    services/        业务服务
      downloader.py        视频下载（yt-dlp）
      transcription.py     语音转文字（faster-whisper）
      copy_generator.py    文案生成（模板规则）
    tasks/           异步管线（video_pipeline）
frontend/
  app/               Next.js 页面
  components/        UI 组件（VideoInfo, TranscriptPanel, CopyPanel 等）
  lib/               API Client 和 TypeScript 类型
storage/
  videos/            下载的视频文件
  transcripts/       转录文本
  exports/           导出文件
```

## 管线流程

```
创建任务 → 解析平台 → 下载视频 → 语音转文字 → 保存转录 → 生成文案 → 完成
   5%        10%        30%        55%         65%        75%     100%
```

- 视频已下载时自动跳过下载步骤
- 转录或文案生成失败不会阻断整个流程
- 支持对已完成任务重新运行（如更换文案风格/平台）

## 配置说明

### 环境变量（可选）

创建 `backend/.env` 文件：

```env
# 如需使用 AI 大模型替代模板生成（可选）
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

### 平台支持

| 平台 | URL 格式 |
|------|----------|
| 抖音 | `https://v.douyin.com/xxx/` |
| B站 | `https://b23.tv/xxx` 或 `https://www.bilibili.com/video/BVxxx` |
| TikTok | `https://www.tiktok.com/@user/video/xxx` |
| 小红书 | `https://www.xiaohongshu.com/explore/xxx` |

## 限制说明

- 不支持私密/付费/地区限制/需登录的视频内容
- 首次运行会自动下载 Whisper 模型（约 150MB），之后使用本地缓存
- 语音转文字使用 CPU 模式，较长视频处理可能需要几分钟
- 当前使用 FastAPI BackgroundTasks 后台执行，适合单用户使用
# 短视频文案生成器

本项目是一个本地单用户短视频文案生成工具。第一阶段已经搭好 FastAPI 后端、SQLite 任务表、平台识别适配层，以及 Next.js Web 工作台。

## 当前能力

- 创建任务：输入 B站 / 抖音 / TikTok / 小红书链接
- 自动识别来源平台
- 保存任务到本地 SQLite
- 查看任务列表和任务详情
- 在任务详情页触发 `yt-dlp` 视频下载
- 保存视频标题、作者、时长、封面、本地路径和关键元数据
- 下载完成后任务状态会停在 `video_downloaded`，等待下一阶段音频提取
- 预留本地 `faster-whisper`、FFmpeg、下载和导出模块边界

## 后端启动

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

后端默认地址：

```text
http://localhost:8000
```

健康检查：

```text
http://localhost:8000/health
```

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：

```text
http://localhost:3000
```

## 项目结构

```text
backend/
  app/
    api/          FastAPI 路由
    core/         配置和异常
    db/           数据库连接
    models/       SQLModel 数据模型
    platforms/    平台识别适配器
    schemas/      API schema
    services/     后续媒体和文本服务
    tasks/        后续异步流水线
frontend/
  app/            Next.js 页面
  components/     UI 组件
  lib/            API client 和类型
storage/
  videos/
  audios/
  transcripts/
  exports/
  models/
```

## 下一阶段

阶段三建议实现：

1. 接入 FFmpeg，提取 Whisper 友好音频。
2. 接入 `faster-whisper` 本地模型识别字幕。
3. 把当前同步触发的下载流程迁移到 Celery 后台任务。

## 下载说明

任务详情页的“开始下载视频”会调用：

```text
POST /api/tasks/{task_id}/start
```

当前阶段使用 `yt-dlp` 能力下载公开视频。对于私密、付费、地区限制、平台限制或需要登录授权的内容，系统会将任务标记为失败并保存错误信息。
