"""
pipeline/tts_gen.py — 语音合成引擎适配器
统一接口，支持 edge-tts / ChatTTS / GPT-SoVITS
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))

from config.settings import TTS_ENGINE, TTS_VOICE, TTS_SPEED, AUDIO_DIR, CHATTTS


class TTSGenerator:
    """统一语音合成接口"""

    def __init__(self, engine: str = None):
        self.engine = engine or TTS_ENGINE
        self._chattts = None
        print(f"TTS engine: {self.engine}")

    def synthesize(self, text: str, voice: str = None, output_name: str = None) -> Path:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            voice: 音色
            output_name: 输出文件名(不含扩展名)
        
        Returns:
            Path: 音频文件路径
        """
        voice = voice or TTS_VOICE
        output_name = output_name or f"tts_{hash(text) & 0xFFFF:04x}"
        output_path = AUDIO_DIR / f"{output_name}.mp3"

        if self.engine == "edge-tts":
            return self._edge_tts(text, voice, output_path)
        elif self.engine == "chattts":
            return self._chattts_gen(text, output_path)
        else:
            return self._edge_tts(text, voice, output_path)

    def _edge_tts(self, text: str, voice: str, output_path: Path) -> Path:
        """使用 Edge-TTS (免费、无需GPU)"""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice, rate=TTS_SPEED)
            asyncio.run(communicate.save(str(output_path)))
            print(f"TTS (edge): {output_path.name}")
            return output_path
        except Exception as e:
            print(f"Edge-TTS failed: {e}")
            return self._fallback_silence(output_path)

    def _chattts_gen(self, text: str, output_path: Path) -> Path:
        """使用 ChatTTS (需要GPU，效果更好)"""
        try:
            if self._chattts is None:
                sys.path.insert(0, str(CHATTTS))
                import ChatTTS
                import torch
                self._chattts = ChatTTS.Chat()
                self._chattts.load(compile=False)

            wavs = self._chattts.infer([text], use_decoder=True)
            import soundfile as sf
            sf.write(str(output_path), wavs[0], 24000)
            print(f"TTS (ChatTTS): {output_path.name}")
            return output_path
        except Exception as e:
            print(f"ChatTTS failed: {e}, fallback to edge-tts")
            return self._edge_tts(text, TTS_VOICE, output_path)

    def _fallback_silence(self, output_path: Path) -> Path:
        """生成静音文件兜底"""
        import numpy as np
        try:
            import soundfile as sf
            silence = np.zeros(24000, dtype=np.float32)
            sf.write(str(output_path), silence, 24000)
        except Exception:
            output_path.touch()
        return output_path

    def synthesize_dialogues(self, dialogues: list, character_voices: dict = None) -> list:
        """
        批量合成场景对话
        
        Returns:
            list[dict]: [{character, text, audio_path, start_time}]
        """
        results = []
        for i, d in enumerate(dialogues):
            char = d.get("character", "旁白")
            text = d.get("text", "")
            voice = (character_voices or {}).get(char, TTS_VOICE)
            audio_path = self.synthesize(text, voice, f"dialogue_{i:03d}")
            results.append({
                "character": char,
                "text": text,
                "audio_path": audio_path,
                "order": i
            })
        return results
