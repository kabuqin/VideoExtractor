import Link from "next/link";

import { PlayIcon } from "@/components/icons";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Link className="logo" href="/">
          <span className="logo-mark">
            <PlayIcon />
          </span>
          <span className="logo-text">
            Video<span>Extractor</span>
          </span>
        </Link>

        <nav className="site-nav">
          <a href="/#features">功能</a>
          <a href="/#how-it-works">如何使用</a>
          <a href="/#faq">常见问题</a>
          <a
            className="nav-external"
            href="https://github.com/kabuqin/VideoExtractor"
            rel="noreferrer"
            target="_blank"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
