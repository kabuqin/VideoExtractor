export const PLATFORM_LABELS: Record<string, string> = {
  bilibili: "B站",
  douyin: "抖音",
  tiktok: "TikTok",
  xiaohongshu: "小红书",
  youtube: "YouTube",
};

export function platformLabel(platform: string | null | undefined): string {
  if (!platform) return "未知平台";
  return PLATFORM_LABELS[platform] ?? platform;
}
