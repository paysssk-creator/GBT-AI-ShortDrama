"""
pipeline/video_gen.py — 视频生成引擎适配器
统一接口，支持 SkyReels-V1 / Diffusers / ComfyUI / Mock
"""
import sys
from pathlib import Path
from typing import Optional
from PIL import Image

sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))

from config.settings import (
    VIDEO_ENGINE, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    VIDEO_FRAMES_PER_SCENE, INFERENCE_STEPS, GUIDANCE_SCALE,
    GPU_COUNT, USE_QUANT, USE_OFFLOAD, VIDEOS_DIR, SKYREELS_V1
)


class VideoGenerator:
    """统一视频生成接口"""

    def __init__(self, engine: str = None):
        self.engine = engine or VIDEO_ENGINE
        self.predictor = None
        self._init_engine()

    def _init_engine(self):
        """初始化视频生成引擎"""
        if self.engine == "skyreels":
            self._init_skyreels()
        elif self.engine == "diffusers":
            self._init_diffusers()
        elif self.engine == "comfyui":
            self._init_comfyui()
        else:
            print(f"Unknown engine '{self.engine}', fallback to diffusers")
            self._init_diffusers()

    def _init_skyreels(self):
        """初始化 SkyReels-V1 引擎 (需要RTX4090)"""
        try:
            sys.path.insert(0, str(SKYREELS_V1))
            from skyreelsinfer import TaskType
            from skyreelsinfer.offload import OffloadConfig
            from skyreelsinfer.skyreels_video_infer import SkyReelsVideoInfer

            self.predictor = SkyReelsVideoInfer(
                task_type=TaskType.T2V,
                model_id="Skywork/SkyReels-V1-Hunyuan-T2V",
                quant_model=USE_QUANT,
                world_size=GPU_COUNT,
                is_offload=USE_OFFLOAD,
                offload_config=OffloadConfig(
                    high_cpu_memory=True,
                    parameters_level=True,
                    compiler_transformer=False,
                ),
                enable_cfg_parallel=GUIDANCE_SCALE > 1.0,
            )
            self._task_type = TaskType.T2V
            print(f"SkyReels-V1 engine ready (GPU x{GPU_COUNT})")
        except Exception as e:
            print(f"SkyReels-V1 init failed: {e}, fallback to Diffusers")
            self._init_diffusers()

    def _init_diffusers(self):
        """初始化 Diffusers/CogVideoX 引擎"""
        try:
            import torch
            from diffusers import CogVideoXPipeline
            model_id = "THUDM/CogVideoX-2b"
            self.diffusers_pipe = CogVideoXPipeline.from_pretrained(
                model_id, torch_dtype=torch.bfloat16)
            if torch.cuda.is_available():
                self.diffusers_pipe.to("cuda")
                self.diffusers_pipe.enable_model_cpu_offload()
                self.diffusers_pipe.vae.enable_tiling()
            self.engine = "diffusers"
            print("Diffusers/CogVideoX engine ready")
        except Exception as e:
            print(f"Diffusers init failed: {e}, using mock mode")
            self.engine = "mock"

    def _init_comfyui(self):
        """初始化 ComfyUI API 引擎"""
        try:
            import requests
            self.comfyui_url = "http://127.0.0.1:8188"
            resp = requests.get(f"{self.comfyui_url}/system_stats", timeout=5)
            if resp.status_code == 200:
                self.engine = "comfyui"
                print(f"ComfyUI engine ready: {self.comfyui_url}")
            else:
                raise Exception("ComfyUI unreachable")
        except Exception as e:
            print(f"ComfyUI not available: {e}")
            self._init_diffusers()

    def generate_scene(self, visual_prompt, scene_id=0, seed=None, image=None):
        """生成单个场景视频 (委托给 video_gen_impl)"""
        from pipeline.video_gen_impl import generate_scene as _gen
        return _gen(self, visual_prompt, scene_id, seed, image)
