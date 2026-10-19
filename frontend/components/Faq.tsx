const FAQS = [
  {
    question: "这个工具是免费的吗？",
    answer:
      "是的，完全免费。项目在本地运行，没有次数限制，也不需要注册账号。语音转写与文案生成同样不使用付费 API。",
  },
  {
    question: "支持哪些平台？",
    answer:
      "目前支持 B站、抖音、TikTok、小红书和 YouTube。直接粘贴分享链接，或粘贴带链接的分享文本，系统会自动提取并解析。",
  },
  {
    question: "解析失败怎么办？",
    answer:
      "部分平台对未登录访问有限制。你可以在 backend/.env 中配置 COOKIES_FILE 或 BROWSER_COOKIES（从已登录的浏览器读取 cookies），再重新解析。",
  },
  {
    question: "视频会被上传到服务器吗？",
    answer:
      "不会。视频下载、语音转文字和文案生成全部在本机完成，视频与文字数据都不会离开你的设备。",
  },
  {
    question: "处理一个视频需要多久？",
    answer:
      "下载通常只需要几秒到几十秒；语音转写时长取决于视频长度，首次运行还会自动下载 Whisper 模型（约 150MB）。",
  },
];

export function Faq() {
  return (
    <div className="faq-list">
      {FAQS.map((item) => (
        <details className="faq-item" key={item.question}>
          <summary>
            {item.question}
            <span aria-hidden="true" className="faq-icon">
              +
            </span>
          </summary>
          <p>{item.answer}</p>
        </details>
      ))}
    </div>
  );
}
