const VIDEO_URL_PATTERNS = [
  /https?:\/\/v\.douyin\.com\/[\w-]+\/?/,
  /https?:\/\/www\.douyin\.com\/video\/[\d]+/,
  /https?:\/\/www\.bilibili\.com\/video\/BV[\w]+/,
  /https?:\/\/b23\.tv\/[\w]+/,
  /https?:\/\/www\.tiktok\.com\/@[\w.]+\/video\/[\d]+/,
  /https?:\/\/www\.xiaohongshu\.com\/explore\/[\w]+/,
  /https?:\/\/www\.youtube\.com\/watch\?v=[\w-]+/,
  /https?:\/\/www\.youtube\.com\/shorts\/[\w-]+/,
  /https?:\/\/youtu\.be\/[\w-]+/,
];

export function extractVideoUrl(text: string): string {
  const trimmed = text.trim();
  for (const pattern of VIDEO_URL_PATTERNS) {
    const match = trimmed.match(pattern);
    if (match) return match[0];
  }
  const bare = trimmed.match(/https?:\/\/\S+/);
  return bare ? bare[0].replace(/[),，。;；]+$/, "") : trimmed;
}

export function isSupportedVideoUrl(url: string): boolean {
  return VIDEO_URL_PATTERNS.some((pattern) => pattern.test(url));
}
