"""
GBT AI Short Drama Factory — 全局配置
所有引擎路径、参数集中管理
"""
import os
from pathlib import Path

# === 项目根目录 ===
ROOT_DIR = Path(__file__).parent.parent

# === 引擎路径 (不改动原仓库) ===
ENGINES_DIR = Path("C:/Users/ADMIN/AI-Engines")
GBT_FRAMEWORK = Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")
SKYREELS_V1 = Path("C:/Users/ADMIN/SkyReels-V1")
CHATTTS = ENGINES_DIR / "ChatTTS"

# === 输出目录 ===
OUTPUT_DIR = ROOT_DIR / "output"
SCRIPTS_DIR = OUTPUT_DIR / "scripts"
VIDEOS_DIR = OUTPUT_DIR / "videos"
AUDIO_DIR = OUTPUT_DIR / "audio"
FINAL_DIR = OUTPUT_DIR / "final"
SUBTITLES_DIR = OUTPUT_DIR / "subtitles"

for d in [OUTPUT_DIR, SCRIPTS_DIR, VIDEOS_DIR, AUDIO_DIR, FINAL_DIR, SUBTITLES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# === LLM 配置 ===
LLM_PROVIDER = os.getenv("GBT_DRAMA_LLM", "auto")  # auto/zhipu/openai/deepseek/ollama
LLM_MODEL = os.getenv("GBT_DRAMA_MODEL", None)  # None = default

# === 视频生成配置 ===
VIDEO_ENGINE = os.getenv("GBT_VIDEO_ENGINE", "diffusers")  # diffusers/skyreels/comfyui
VIDEO_WIDTH = 960
VIDEO_HEIGHT = 544
VIDEO_FPS = 24
VIDEO_FRAMES_PER_SCENE = 97  # ~4 seconds
INFERENCE_STEPS = 30
GUIDANCE_SCALE = 6.0

# === TTS 配置 ===
TTS_ENGINE = os.getenv("GBT_TTS_ENGINE", "edge-tts")  # edge-tts/chattts/gpt-sovits
TTS_VOICE = os.getenv("GBT_TTS_VOICE", "zh-CN-XiaoxiaoNeural")
TTS_SPEED = "+0%"

# === 短剧参数 ===
MAX_SCENES = 10
CHARACTER_PROFILES = ROOT_DIR / "config" / "characters.json"

# === GPU 配置 ===
GPU_COUNT = int(os.getenv("GBT_GPU_COUNT", "1"))
USE_QUANT = os.getenv("GBT_USE_QUANT", "true").lower() == "true"
USE_OFFLOAD = os.getenv("GBT_USE_OFFLOAD", "true").lower() == "true"

# === FFmpeg ===
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
