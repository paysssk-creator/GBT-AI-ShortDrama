"""
pipeline/orchestrator.py — GBT AI短剧总调度器
全自动流水线: 剧本 → 分镜 → 视频 → 配音 → 合成
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))

from config.settings import (
    SCRIPTS_DIR, VIDEOS_DIR, AUDIO_DIR, FINAL_DIR,
    CHARACTER_PROFILES, MAX_SCENES, VIDEO_FPS
)
from pipeline.script_gen import ScriptGenerator
from pipeline.video_gen import VideoGenerator
from pipeline.tts_gen import TTSGenerator
from pipeline.compose import VideoComposer


class DramaOrchestrator:
    """AI短剧总调度器 — 一键生成完整短剧"""

    def __init__(self):
        print("━" * 50)
        print("  GBT AI Short Drama Factory v1.0")
        print("  全能AI短剧自动生成工厂")
        print("━" * 50)

        # 加载角色库
        self.characters = self._load_characters()
        self.character_voices = {
            c["name"]: c.get("voice", "zh-CN-XiaoxiaoNeural")
            for c in self.characters
        }

        # 初始化引擎
        print("\n[1/4] Initializing engines...")
        self.script_gen = ScriptGenerator()
        self.video_gen = VideoGenerator()
        self.tts_gen = TTSGenerator()
        self.composer = VideoComposer()
        print("All engines ready.\n")

    def _load_characters(self):
        """加载角色设定"""
        if CHARACTER_PROFILES.exists():
            with open(CHARACTER_PROFILES, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("characters", [])
        return []

    def run(self, prompt: str, 
            output_name: str = None,
            generate_video: bool = True,
            generate_audio: bool = True) -> Path:
        """
        一键生成完整短剧
        
        Args:
            prompt: 创作需求 (例如："武侠短剧，主角复仇的故事")
            output_name: 输出文件名
            generate_video: 是否生成视频
            generate_audio: 是否生成配音
        
        Returns:
            Path: 最终视频路径
        """
        start_time = datetime.now()
        output_name = output_name or f"drama_{start_time.strftime('%Y%m%d_%H%M%S')}"
        print(f"\n{'='*50}")
        print(f"  Starting: {output_name}")
        print(f"  Prompt: {prompt}")
        print(f"{'='*50}\n")

        # === Step 1: 生成剧本 ===
        print("[2/4] Generating script...")
        script = self.script_gen.generate(prompt, self.characters)
        scenes = script.get("scenes", [])
        print(f"Script ready: {script.get('title','N/A')} ({len(scenes)} scenes)\n")

        # === Step 2: 生成所有场景视频 ===
        video_paths = []
        if generate_video and scenes:
            print(f"[3/4] Generating {len(scenes)} scene videos...")
            for i, scene in enumerate(scenes):
                visual_prompt = scene.get("visual_prompt", f"scene {i}")
                print(f"  Scene {i+1}/{len(scenes)}: {scene.get('location','N/A')}")
                vp = self.video_gen.generate_scene(
                    visual_prompt=visual_prompt,
                    scene_id=i + 1
                )
                video_paths.append(vp)
            print(f"Videos generated: {len(video_paths)}\n")
        else:
            print("[3/4] Video generation skipped\n")
            video_paths = [VIDEOS_DIR / f"scene_{i:03d}.mp4" for i in range(1, len(scenes)+1)]

        # === Step 3: 生成所有配音 ===
        all_audios = []
        if generate_audio and scenes:
            print(f"[4/4] Generating voiceovers for {len(scenes)} scenes...")
            for i, scene in enumerate(scenes):
                dialogues = scene.get("dialogues", [])
                narration = scene.get("narration", "")
                
                # 旁白
                if narration:
                    audio_path = self.tts_gen.synthesize(
                        narration, self.character_voices.get("旁白", "zh-CN-YunxiNeural"),
                        f"narrate_{i:03d}"
                    )
                    dialogues = [{"character": "旁白", "text": narration}] + dialogues
                
                # 对话
                scene_audios = self.tts_gen.synthesize_dialogues(
                    dialogues, self.character_voices
                )
                all_audios.append(scene_audios)
                print(f"  Scene {i+1}/{len(scenes)}: {len(scene_audios)} dialogues")
        else:
            print("[4/4] Audio generation skipped\n")
            all_audios = [[] for _ in scenes]

        # === Step 4: 合成最终视频 ===
        print("\nComposing final video...")
        final_path = self.composer.compose(
            video_clips=video_paths,
            audio_clips=all_audios,
            output_name=output_name
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n{'='*50}")
        print(f"  DONE! Elapsed: {elapsed:.1f}s")
        print(f"  Output: {final_path}")
        print(f"  Scenes: {len(scenes)}")
        print(f"{'='*50}")

        return final_path

    def generate_script_only(self, prompt: str) -> dict:
        """仅生成剧本(预览模式)"""
        return self.script_gen.generate(prompt, self.characters)
