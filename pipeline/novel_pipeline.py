"""
novel_pipeline.py — 玄幻小说→AI短剧 全自动流水线
规则:
1. 每本小说必须从头到尾逐章处理完, 才换下一本
2. 每章拆为2集短剧, 两集必须都成功
3. 单章失败自动重试(最多2次), 仍失败标记SKIP继续下一章
4. 禁止中途中断或跳到下一本
"""
import sys, json, time, re
from pathlib import Path
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import SCRIPTS_DIR, AUDIO_DIR, OUTPUT_DIR
from pipeline.novel_scraper import NovelScraper
from pipeline.novel_to_drama import NovelToDrama
from pipeline.tts_gen import TTSGenerator


class NovelDramaPipeline:
    """玄幻→短剧流水线 | 整本完结原则"""

    MAX_RETRY = 2

    def __init__(self):
        self.scraper = NovelScraper("biquge")
        self.converter = NovelToDrama()
        self.tts = TTSGenerator()
        self.COMPLETED = OUTPUT_DIR / "completed"
        self.FAILED = OUTPUT_DIR / "failed"
        self.PROGRESS = OUTPUT_DIR / "progress"
        for d in [self.COMPLETED, self.FAILED, self.PROGRESS]:
            d.mkdir(parents=True, exist_ok=True)

    def _safe(self, title: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', title)[:50]

    def _is_done(self, title: str) -> bool:
        return (self.COMPLETED / f"{self._safe(title)}.done").exists()

    def _is_fail(self, title: str) -> bool:
        return (self.FAILED / f"{self._safe(title)}.fail").exists()

    def _mark_done(self, title: str):
        p = self.COMPLETED / f"{self._safe(title)}.done"
        p.write_text(json.dumps({"title": title, "time": datetime.now().isoformat()}))

    def _mark_fail(self, title: str, reason: str):
        p = self.FAILED / f"{self._safe(title)}.fail"
        p.write_text(json.dumps({"title": title, "reason": reason}))

    def _save_progress(self, title: str, ch_idx: int, total: int):
        """保存进度: 正在处理第几章"""
        p = self.PROGRESS / f"{self._safe(title)}.json"
        p.write_text(json.dumps({"chapter": ch_idx, "total": total,
                                  "time": datetime.now().isoformat()}))

    def _get_progress(self, title: str) -> int:
        """获取上次处理到的章节号, 0=未开始"""
        p = self.PROGRESS / f"{self._safe(title)}.json"
        if p.exists():
            try:
                return int(json.loads(p.read_text()).get("chapter", 0))
            except:
                pass
        return 0

    def get_ranking(self, n=20) -> List[Dict]:
        return self.scraper.fetch_ranking(n)

    def run_chapter(self, novel_title: str, novel_author: str,
                    novel_intro: str, chapter: Dict, episode_count: int = 2) -> Dict:
        """
        处理单章→两集短剧 (必须两集都成功)
        
        Returns: {"ok": bool, "script": dict|None, "audios": list|None, "error": str|None}
        """
        ch_title = chapter.get("title", "")
        content = chapter.get("content", "")

        if len(content) < 200:
            return {"ok": False, "error": f"Content too short ({len(content)} chars)"}

        chapter["novel_title"] = novel_title
        chapter["novel_author"] = novel_author
        chapter["novel_intro"] = novel_intro

        result = None
        for at in range(self.MAX_RETRY + 1):
            if at > 0: time.sleep(2)
            try:
                result = self.converter.convert(chapter)
                eps = result.get("episodes", [])
                if len(eps) >= episode_count and all(
                    isinstance(e, dict) and "error" not in str(e)
                    for e in eps[:episode_count]
                ):
                    break
                result = None
            except Exception as e:
                if at == self.MAX_RETRY:
                    return {"ok": False, "error": f"Script gen failed: {e}"}

        if not result or len(result.get("episodes", [])) < episode_count:
            return {"ok": False, "error": "Failed to generate all episodes"}

        return {"ok": True, "script": result, "audios": []}


    def run_novel(self, rank: int = 1) -> Dict:
        """全自动处理整本小说: 逐章→每章2集短剧→直到完结"""
        log = [f"Novel Pipeline: ENTIRE BOOK | {datetime.now().strftime('%H:%M:%S')}"]
        novels = self.scraper.fetch_ranking(max(5, rank))
        if rank > len(novels):
            return {"ok": False, "error": "Rank out of range", "log": log}
        n = novels[rank - 1]
        title = n["title"]
        author = n["author"]
        intro = n.get("intro", "")
        log.append(f"Book: {title} - {author}")
        if self._is_done(title):
            log.append("Already completed"); return {"ok": True, "skipped": True, "log": log}
        if self._is_fail(title):
            log.append("Previously failed"); return {"ok": True, "skipped": True, "log": log}

        chapters = self.scraper.fetch_chapter_list(n["url"])
        if not chapters:
            self._mark_fail(title, "No chapters"); return {"ok": False, "error": "No chapters", "log": log}
        total = len(chapters)
        log.append(f"Total chapters: {total}")

        start_from = self._get_progress(title) + 1
        if start_from > 1:
            log.append(f"Resume from ch{start_from}/{total}")

        scripts = []
        stats = {"completed": 0, "skipped": 0, "failed": 0}
        for i in range(start_from - 1, total):
            ch = chapters[i]
            ci = i + 1
            log.append(f"Ch{ci}/{total}: {ch['title']}")
            chapter = None
            for _ in range(self.MAX_RETRY + 1):
                chapter = self.scraper.fetch_chapter(n["url"], ci)
                if chapter and len(chapter.get("content", "")) > 200:
                    break
                chapter = None
                time.sleep(2)
            if not chapter:
                stats["skipped"] += 1; self._save_progress(title, ci, total); continue
            r = self.run_chapter(title, author, intro, chapter)
            if r["ok"]:
                scripts.append({"chapter": ci, "title": ch["title"], "script": r["script"]})
                stats["completed"] += 1
                log.append(f"  OK: {len(r['script']['episodes'])} eps")
            else:
                stats["failed"] += 1
                log.append(f"  FAIL: {r['error']}")
            self._save_progress(title, ci, total)

        if stats["completed"] > 0:
            self._mark_done(title)
            log.append(f"BOOK COMPLETED: {title}")
        else:
            self._mark_fail(title, "No chapters done")
            log.append(f"BOOK FAILED: {title}")
        log.append(f"Stats: {stats['completed']} done/{stats['skipped']} skip/{stats['failed']} fail/{total} total")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sp = SCRIPTS_DIR / f"novel_full_{self._safe(title)}_{ts}.json"
        sp.write_text(json.dumps({"novel": {"title": title, "author": author, "intro": intro, "chapters": total},
            "scripts": scripts, "stats": stats, "time": ts}, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "total_chapters": total, **stats, "scripts": scripts, "log": log}
