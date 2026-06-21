"""
pipeline/compose.py — 视频剪辑合成器
将视频片段+配音+字幕合成为完整短剧
"""
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))

from config.settings import FINAL_DIR, FFMPEG_PATH, VIDEO_FPS


class VideoComposer:
    """视频剪辑合成器"""

    def __init__(self):
        self.ffmpeg = FFMPEG_PATH

    def compose(self,
                video_clips: List[Path],
                audio_clips: List[List[dict]],  # per-scene dialogue audios
                subtitles: List[List[dict]] = None,
                output_name: str = "final_drama",
                bgm_path: Path = None) -> Path:
        """
        合成完整短剧
        
        Args:
            video_clips: 场景视频片段列表
            audio_clips: 每个场景的配音列表
            subtitles: 每个场景的字幕列表
            output_name: 输出文件名
            bgm_path: 背景音乐路径
        
        Returns:
            Path: 最终视频路径
        """
        try:
            import ffmpeg
            return self._compose_ffmpeg_python(
                video_clips, audio_clips, output_name, bgm_path)
        except ImportError:
            print("ffmpeg-python not installed, using subprocess")
            return self._compose_subprocess(
                video_clips, audio_clips, output_name, bgm_path)

    def _compose_ffmpeg_python(self, video_clips, audio_clips,
                                output_name, bgm_path=None):
        """使用 ffmpeg-python 合成"""
        import ffmpeg

        # 1. 拼接视频
        concat_file = FINAL_DIR / f"{output_name}_concat.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for v in video_clips:
                if v.exists():
                    f.write(f"file '{v.as_posix()}'\n")

        merged_video = FINAL_DIR / f"{output_name}_merged.mp4"
        ffmpeg.input(str(concat_file), format="concat", safe=0).output(
            str(merged_video), c="copy", vcodec="libx264").run(
                overwrite_output=True, quiet=True)
        print(f"Video merged: {merged_video}")

        # 2. 合并音频
        audio_inputs = []
        for scene_audios in audio_clips:
            for a in scene_audios:
                if Path(a["audio_path"]).exists():
                    audio_inputs.append(ffmpeg.input(str(a["audio_path"])))

        if audio_inputs:
            merged_audio = FINAL_DIR / f"{output_name}_audio.mp3"
            ffmpeg.concat(*audio_inputs, v=0, a=1).output(
                str(merged_audio)).run(overwrite_output=True, quiet=True)
            print(f"Audio merged: {merged_audio}")

        # 3. 合成最终视频
        final_path = FINAL_DIR / f"{output_name}.mp4"
        stream = ffmpeg.input(str(merged_video))
        if audio_inputs:
            audio_stream = ffmpeg.input(str(merged_audio))
            stream = ffmpeg.output(
                stream, audio_stream, str(final_path),
                vcodec="libx264", acodec="aac", shortest=None)
        else:
            stream = ffmpeg.output(stream, str(final_path), vcodec="libx264")

        stream.run(overwrite_output=True, quiet=True)
        print(f"Final: {final_path}")
        return final_path

    def _compose_subprocess(self, video_clips, audio_clips,
                             output_name, bgm_path=None):
        """使用 subprocess + ffmpeg 命令 (备选)"""
        import subprocess

        concat_file = FINAL_DIR / f"{output_name}_concat.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for v in video_clips:
                if v.exists():
                    f.write(f"file '{v.as_posix()}'\n")

        final_path = FINAL_DIR / f"{output_name}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(final_path)
        ]
        subprocess.run(cmd, capture_output=True)
        print(f"Final video: {final_path}")
        return final_path
