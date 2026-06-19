import "./globals.css";

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "短视频文案生成器",
  description: "本地单用户短视频字幕识别与文案生成工具",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

