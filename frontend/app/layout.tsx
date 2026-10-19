import "./globals.css";

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "VideoExtractor · 免费视频解析去水印工具",
  description:
    "粘贴视频链接，自动解析并下载 B站、抖音、TikTok、小红书、YouTube 视频，本地语音转写并生成平台文案。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
