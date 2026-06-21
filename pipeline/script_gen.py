"""
pipeline/script_gen.py — AI剧本生成器
基于 GBTLLM 多模型能力生成短剧剧本
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加 GBT 框架路径
sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))

from config.settings import LLM_PROVIDER, LLM_MODEL, SCRIPTS_DIR, MAX_SCENES


class ScriptGenerator:
    """AI短剧剧本生成器"""

    SYSTEM_PROMPT = """你是一位专业的短剧编剧。你需要根据用户的要求，创作一个完整的短剧剧本。

你必须返回严格JSON格式，结构如下：
{
    "title": "短剧标题",
    "genre": "类型(古装/现代/悬疑/甜宠/逆袭等)",
    "summary": "一句话简介",
    "scenes": [
        {
            "scene_id": 1,
            "location": "场景地点描述",
            "time": "时间(白天/夜晚/黄昏等)",
            "mood": "氛围(紧张/温馨/悲伤等)",
            "visual_prompt": "用于AI视频生成的英文画面描述(50词以内,注重构图和光线)",
            "action": "动作描述(15字以内)",
            "dialogues": [
                {"character": "角色名", "text": "台词内容"}
            ],
            "narration": "旁白内容(可选)",
            "duration_sec": 4
        }
    ]
}

规则：
1. 场景数控制在5~10个
2. visual_prompt用英文写，格式如："FPS-24, cinematic shot, close-up of a young man in white robe, ancient Chinese courtyard, soft morning light, shallow depth of field, 4K quality"
3. 每个场景配备至少1句台词
4. 剧情要有起承转合
5. 角色名从人物列表中选择"""

    def __init__(self):
        self.llm = None
        self._init_llm()

    def _init_llm(self):
        """初始化 LLM"""
        try:
            from gbt.llm import GBTLLM
            self.llm = GBTLLM(
                provider=LLM_PROVIDER,
                model=LLM_MODEL,
                temperature=0.8,
                max_tokens=8192
            )
            print(f"✅ 剧本生成器就绪: {self.llm.provider_name} / {self.llm.model}")
        except Exception as e:
            print(f"⚠️ GBTLLM 初始化失败: {e}")
            print(f"💡 将使用 OpenAI 兼容接口")
            from openai import OpenAI
            self.llm = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            )
            self._use_openai = True

    def generate(self, prompt: str, characters: list = None) -> dict:
        """
        生成短剧剧本
        
        Args:
            prompt: 用户创作要求
            characters: 可选的人物列表
        
        Returns:
            dict: 完整剧本JSON
        """
        user_prompt = f"创作需求：{prompt}\n"
        if characters:
            char_desc = "\n".join(
                f"- {c['name']}({c.get('archetype','')}): {c.get('personality','')}, 外貌:{c.get('appearance','')}"
                for c in characters
            )
            user_prompt += f"\n可用角色：\n{char_desc}"
        
        user_prompt += f"\n请生成{MAX_SCENES}个场景以内的短剧剧本。"

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        try:
            if hasattr(self, '_use_openai'):
                resp = self.llm.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.8
                )
                text = resp.choices[0].message.content
            else:
                text = self.llm.chat(messages)
            
            # 清洗JSON
            text = self._clean_json(text)
            try:
                script = json.loads(text)
            except json.JSONDecodeError:
                # Retry with simpler prompt for small models
                print("  Retry: JSON parse failed, trying simpler prompt...")
                text = self._retry_simple(prompt, characters)
                text = self._clean_json(text)
                try:
                    script = json.loads(text)
                except json.JSONDecodeError:
                    print("  Retry2: still failed, using fallback")
                    return self._fallback_script(prompt)
            
            # 质量检查: 如果只有1个场景且标题是"短剧创作", 说明模型没理解
            if script.get("title") == "短剧创作" and len(script.get("scenes", [])) <= 1:
                print("  Quality check failed, retrying...")
                text = self._retry_simple(prompt, characters)
                text = self._clean_json(text)
                try:
                    script = json.loads(text)
                except json.JSONDecodeError:
                    pass
            
            # 保存剧本
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_path = SCRIPTS_DIR / f"script_{timestamp}.json"
            with open(script_path, "w", encoding="utf-8") as f:
                json.dump(script, f, ensure_ascii=False, indent=2)
            
            print(f"📜 剧本已生成: {script_path}")
            print(f"   标题: {script.get('title','N/A')}")
            print(f"   场景数: {len(script.get('scenes',[]))}")
            
            return script
            
        except Exception as e:
            print(f"❌ 剧本生成失败: {e}")
            return self._fallback_script(prompt)

    def _clean_json(self, text: str) -> str:
        """清洗 LLM 返回的 JSON"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _retry_simple(self, prompt: str, characters: list = None) -> str:
        """小模型专用简化提示 - 分步引导输出JSON"""
        simple = f"""写一个短剧剧本，主题：{prompt[:100]}

直接输出JSON，不要别的文字：
{{"title":"剧名","genre":"类型","summary":"简介","scenes":[
{{"scene_id":1,"location":"地点","time":"时间","mood":"氛围","visual_prompt":"英文画面描述","action":"动作","dialogues":[{{"character":"角色","text":"台词"}}],"narration":"旁白","duration_sec":4}}
]}}

要求：
- 写3到5个场景
- visual_prompt写英文，比如 "FPS-24, wide shot of..."
- 角色名用中文
- 只输出JSON

JSON:"""
        try:
            if hasattr(self, '_use_openai'):
                resp = self.llm.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": simple}],
                    temperature=0.8
                )
                return resp.choices[0].message.content
            else:
                return self.llm.chat([{"role": "user", "content": simple}])
        except:
            return "{}"

    def _fallback_script(self, prompt: str) -> dict:
    def _fallback_script(self, prompt: str) -> dict:
        """兜底剧本模板"""
        return {
            "title": "短剧创作",
            "genre": "未知",
            "summary": prompt[:50],
            "scenes": [
                {
                    "scene_id": 1,
                    "location": "古风庭院",
                    "time": "白天",
                    "mood": "宁静",
                    "visual_prompt": "FPS-24, wide shot of ancient Chinese courtyard, cherry blossoms falling, soft sunlight through leaves, cinematic quality",
                    "action": "主角漫步于庭院",
                    "dialogues": [
                        {"character": "主角", "text": "这片天地，终究是我的归宿。"}
                    ],
                    "duration_sec": 4
                }
            ]
        }
