"""
pipeline/novel_scraper.py — 玄幻小说排行榜抓取器
支持多个免费小说源，获取榜单+章节内容
"""
import requests
import re
import time
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 多个免费小说源
SOURCES = {
    "biquge": {
        "name": "笔趣阁",
        "rank_url": "https://www.xbiquge.la/xuanhuan/",
        "base_url": "https://www.xbiquge.la",
        "encoding": "utf-8",
    },
    "69shu": {
        "name": "69书吧",
        "rank_url": "https://www.69shu.pro/rank/",
        "base_url": "https://www.69shu.pro",
        "encoding": "utf-8",
    },
    "biqukan": {
        "name": "笔趣看",
        "rank_url": "https://www.biqukan.cc/top/",
        "base_url": "https://www.biqukan.cc",
        "encoding": "gbk",
    },
}


class NovelScraper:
    """玄幻小说排行榜抓取器"""

    def __init__(self, source: str = "biquge"):
        self.source = source
        self.cfg = SOURCES.get(source, SOURCES["biquge"])

    def fetch_ranking(self, max_count: int = 20) -> List[Dict]:
        """
        获取玄幻排行榜
        
        Returns:
            List[dict]: [{"rank", "title", "author", "url", "intro"}]
        """
        novels = []
        try:
            resp = requests.get(
                self.cfg["rank_url"],
                headers=HEADERS,
                timeout=15
            )
            resp.encoding = self.cfg["encoding"]
            soup = BeautifulSoup(resp.text, "lxml")

            # 多种选择器适配不同站点
            items = (
                soup.select(".rank-list li") or
                soup.select(".novellist li") or
                soup.select("#newscontent .l li") or
                soup.select("ul.list li") or
                soup.select(".item")
            )

            for i, item in enumerate(items[:max_count]):
                link = item.find("a")
                if not link:
                    continue

                title = link.get("title") or link.get_text(strip=True)
                href = link.get("href", "")
                if href and not href.startswith("http"):
                    href = self.cfg["base_url"] + href

                author_el = item.select_one(".author, .s4, span")
                author = author_el.get_text(strip=True) if author_el else "未知"

                intro_el = item.select_one(".intro, .review, p")
                intro = intro_el.get_text(strip=True)[:100] if intro_el else ""

                novels.append({
                    "rank": i + 1,
                    "title": title,
                    "author": author,
                    "url": href,
                    "intro": intro,
                    "source": self.cfg["name"],
                })

            print(f"Fetched {len(novels)} novels from {self.cfg['name']}")
        except Exception as e:
            print(f"Fetch ranking failed ({self.cfg['name']}): {e}")

        return novels

    def fetch_chapter(self, novel_url: str, chapter_no: int = 1) -> Optional[Dict]:
        """
        获取小说章节内容
        
        Args:
            novel_url: 小说主页URL
            chapter_no: 章节序号(1=第一章)
        
        Returns:
            dict: {"title", "chapter_title", "content", "next_url"}
        """
        try:
            # 1. 获取小说目录页
            resp = requests.get(novel_url, headers=HEADERS, timeout=15)
            resp.encoding = self.cfg["encoding"]
            soup = BeautifulSoup(resp.text, "lxml")

            # 2. 找第一章链接
            chapter_links = soup.select("#list dd a, .chapterlist dd a, ul.dirlist li a")
            if not chapter_links:
                chapter_links = soup.select("dd a")[:20]

            if chapter_no > len(chapter_links):
                print(f"Chapter {chapter_no} not found, max {len(chapter_links)}")
                return None

            ch_link = chapter_links[chapter_no - 1]
            ch_url = ch_link.get("href", "")
            ch_title = ch_link.get_text(strip=True)

            if ch_url and not ch_url.startswith("http"):
                ch_url = self.cfg["base_url"] + ch_url

            # 3. 获取章节内容
            resp2 = requests.get(ch_url, headers=HEADERS, timeout=15)
            resp2.encoding = self.cfg["encoding"]
            soup2 = BeautifulSoup(resp2.text, "lxml")

            # 提取正文
            content_el = soup2.select_one("#content, .content, .showtxt, #chaptercontent")
            if content_el:
                # 清理广告和脚本
                for tag in content_el.select("script, .ads, style"):
                    tag.decompose()
                text = content_el.get_text("\n", strip=True)
            else:
                text = soup2.get_text()

            # 清理多余空白
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r'[ \t]+', ' ', text)

            # 限制长度(取前3000字用于短剧改编)
            if len(text) > 3000:
                text = text[:3000] + "..."

            print(f"Chapter: {ch_title} ({len(text)} chars)")

            return {
                "title": ch_title,
                "content": text,
                "source_url": ch_url,
                "chapter_no": chapter_no,
            }

        except Exception as e:
            print(f"Fetch chapter failed: {e}")
            return None

    def get_top_novel_chapter(self, rank: int = 1, chapter_no: int = 1) -> Optional[Dict]:
        """快捷方法：获取排行第N的小说的章节"""
        novels = self.fetch_ranking(max_count=max(rank, 5))
        if rank > len(novels):
            return None
        novel = novels[rank - 1]
        chapter = self.fetch_chapter(novel["url"], chapter_no)
        if chapter:
            chapter["novel_title"] = novel["title"]
            chapter["novel_author"] = novel["author"]
            chapter["novel_intro"] = novel["intro"]
        return chapter
