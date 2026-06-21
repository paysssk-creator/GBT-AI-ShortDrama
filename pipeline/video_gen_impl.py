"""
pipeline/video_gen_impl.py — VideoGenerator 的实现方法
(从 video_gen.py 拆分以控制文件大小)
"""
import sys
import random
from pathlib import Path
from typing import Optional
from PIL import Image

sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))

from config.settings import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    VIDEO_FRAMES_PER_SCENE, INFERENCE_STEPS, GUIDANCE_SCALE,
    VIDEOS_DIR
)


def generate_scene(engine_obj, visual_prompt: str, scene_id: int = 0,
                   seed: int = None, image: Optional[Image.Image] = None) -> Path:
    """
    生成单个场景视频
    """
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    video_path = VIDEOS_DIR / f"scene_{scene_id:03d}_s{seed}.mp4"

    if engine_obj.engine == "skyreels":
        return _gen_skyreels(engine_obj, visual_prompt, scene_id, seed, image, video_path)
    elif engine_obj.engine == "diffusers":
        return _gen_diffusers(engine_obj, visual_prompt, scene_id, seed, video_path)
    else:
        return _gen_mock(engine_obj, visual_prompt, scene_id, video_path)


def _gen_skyreels(engine_obj, prompt, scene_id, seed, image, video_path):
    """SkyReels-V1 生成"""
    kwargs = {
        "prompt": prompt,
        "height": VIDEO_HEIGHT,
        "width": VIDEO_WIDTH,
        "num_frames": VIDEO_FRAMES_PER_SCENE,
        "num_inference_steps": INFERENCE_STEPS,
        "seed": seed,
        "guidance_scale": GUIDANCE_SCALE,
        "embedded_guidance_scale": 1.0,
        "negative_prompt": "low quality, blurry, distorted face, bad composition",
        "cfg_for": False,
    }
    if image is not None:
        kwargs["image"] = image
    
    from diffusers.utils import export_to_video
    output = engine_obj.predictor.inference(kwargs)
    export_to_video(output, str(video_path), fps=VIDEO_FPS)
    print(f"  Scene {scene_id}: SkyReels done -> {video_path.name}")
    return video_path


def _gen_diffusers(engine_obj, prompt, scene_id, seed, video_path):
    """Diffusers/CogVideoX 生成"""
    import torch
    video = engine_obj.diffusers_pipe(
        prompt=prompt,
        num_frames=VIDEO_FRAMES_PER_SCENE,
        num_inference_steps=INFERENCE_STEPS,
        generator=torch.Generator().manual_seed(seed),
        guidance_scale=GUIDANCE_SCALE,
    ).frames[0]
    
    from diffusers.utils import export_to_video
    export_to_video(video, str(video_path), fps=VIDEO_FPS)
    print(f"  Scene {scene_id}: Diffusers done -> {video_path.name}")
    return video_path


def _gen_mock(engine_obj, prompt, scene_id, video_path):
    """模拟生成 (无GPU时的兜底)"""
    import numpy as np
    try:
        import imageio
        frames = []
        for i in range(min(VIDEO_FRAMES_PER_SCENE, 48)):
            frame = np.ones((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8) * 30
            frames.append(frame)
        imageio.mimsave(str(video_path), frames, fps=VIDEO_FPS)
        print(f"  Scene {scene_id}: Mock video -> {video_path.name}")
        return video_path
    except Exception as e:
        print(f"  Mock generation failed: {e}")
        video_path.touch()
        return video_path
