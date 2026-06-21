"""
pipeline/novel_to_drama.py — 小说章节→AI短剧剧本转换器
将一章小说拆分为两集短剧剧本，投送到剧本生成器
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import SCRIPTS_DIR, AUDIO_DIR
from pipeline.script_gen import ScriptGenerator
from pipeline.tts_gen import TTSGenerator


class NovelToDrama:
    """小说→短剧转换器"""

    EPISODE_TEMPLATE = """你是一位顶尖的短剧编剧。请将以下玄幻小说片段改编为短剧剧本。

## 原著信息
书名: {novel_title}
作者: {novel_author}
简介: {novel_intro}

## 本章内容
{chapter_content}

## 改编要求
1. 这是第{episode}集(共2集)，请完整改编本章的{"前半部分" if episode == 1 else "后半部分"}
2. 保留原著核心情节和人物关系
3. 转化为视觉化的场景，增加画面感和戏剧张力
4. 为每个场景编写英文visual_prompt用于AI视频生成
5. 每个场景控制在4秒内

请返回JSON格式的剧本。"""

    def __init__(self):
        self.script_gen = ScriptGenerator()
        self.tts_gen = TTSGenerator()

    def convert(self, chapter: dict) -> dict:
        """
        将小说章节转换为两集短剧
        
        Args:
            chapter: {"novel_title","novel_author","novel_intro","title","content"}
        
        Returns:
            dict: {"episodes": [ep1_script, ep2_script], "novel_info": {...}}
        """
        novel_title = chapter.get("novel_title", "未知")
        novel_author = chapter.get("novel_author", "未知")
        novel_intro = chapter.get("novel_intro", "")
        content = chapter.get("content", "")
        ch_title = chapter.get("title", "")

        # 拆分内容为两半
        mid = len(content) // 2
        # 在句子边界处分割
        for offset in range(100):
            if mid + offset < len(content) and content[mid + offset] in '。！？\n':
                mid = mid + offset + 1
                break
            if mid - offset >= 0 and content[mid - offset] in '。！？\n':
                mid = mid - offset + 1
                break

        part1 = content[:mid].strip()
        part2 = content[mid:].strip()

        print(f"\n{'='*50}")
        print(f"  Novel: {novel_title} - Ch.{ch_title}")
        print(f"  Split: Part1={len(part1)}chars, Part2={len(part2)}chars")
        print(f"{'='*50}\n")

        episodes = []
        for ep_num, part_content in [(1, part1), (2, part2)]:
            print(f"--- Generating Episode {ep_num}/2 ---")
            prompt = self.EPISODE_TEMPLATE.format(
                novel_title=novel_title,
                novel_author=novel_author,
                novel_intro=novel_intro,
                chapter_content=part_content,
                episode=ep_num,
            )

            try:
                script = self.script_gen.generate(
                    prompt=prompt,
                    characters=None
                )
                episodes.append(script)
            except Exception as e:
                print(f"Episode {ep_num} failed: {e}")
                episodes.append({"error": str(e)})

        # 保存完整项目
        result = {
            "novel_info": {
                "title": novel_title,
                "author": novel_author,
                "intro": novel_intro,
                "chapter": ch_title,
            },
            "episodes": episodes,
            "generated_at": datetime.now().isoformat(),
        }

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = SCRIPTS_DIR / f"novel_drama_{ts}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\nSaved: {save_path}")
        return result

    def generate_audio(self, script: dict, episode_num: int = 1) -> list:
        """为剧本生成配音"""
        scenes = script.get("scenes", [])
        all_audios = []
        for i, scene in enumerate(scenes):
            dialogues = scene.get("dialogues", [])
            narration = scene.get("narration", "")
            if narration:
                ap = self.tts_gen.synthesize(
                    narration,
                    output_name=f"novel_ep{episode_num}_s{i:02d}_narration"
                )
            scene_audios = []
            for d in dialogues:
                ap = self.tts_gen.synthesize(
                    d["text"],
                    output_name=f"novel_ep{episode_num}_s{i:02d}_{d['character']}"
                )
                scene_audios.append({
                    "character": d["character"],
                    "text": d["text"],
                    "audio_path": str(ap)
                })
            all_audios.append(scene_audios)
        return all_audios
