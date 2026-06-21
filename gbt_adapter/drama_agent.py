"""
gbt_adapter/drama_agent.py — GBT AI短剧 Agent
将短剧工厂能力注册到 GBT 智能体框架
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))

from gbt.agent import SimpleAgent, AgentConfig
from gbt.tool import ToolRegistry


DRAMA_SYSTEM_PROMPT = """你是 GBT AI短剧导演。你负责协调整个AI短剧制作流程。

## 能力
- write_script: 根据需求创作剧本
- generate_scene: 生成单个场景视频
- synthesize_voice: 合成配音
- compose_video: 剪辑合成最终视频
- run_full_pipeline: 一键生成完整短剧

## 工作流程
1. 理解用户创作需求
2. 调用 write_script 生成剧本
3. 逐场景生成视频
4. 合成配音
5. 剪辑输出最终短剧

## 角色库
角色从 config/characters.json 加载，支持古装武侠、现代甜宠、悬疑推理等类型。
"""


class DramaAgent(SimpleAgent):
    """GBT短剧导演Agent"""

    def __init__(self, provider: str = "auto", model: str = None):
        from gbt.llm import GBTLLM
        llm = GBTLLM(provider=provider, model=model, temperature=0.8)
        
        tools = ToolRegistry()
        self._register_tools(tools)
        
        config = AgentConfig(name="DramaDirector", max_steps=10)
        
        super().__init__(
            name="DramaDirector",
            llm=llm,
            system_prompt=DRAMA_SYSTEM_PROMPT,
            config=config,
            tool_registry=tools,
            enable_tool_calling=True
        )
        print("Drama Director Agent ready")

    def _register_tools(self, tools: ToolRegistry):
        """注册短剧制作工具到 GBT 工具注册表"""
        
        def write_script(prompt: str) -> str:
            """创作短剧剧本"""
            from pipeline.script_gen import ScriptGenerator
            gen = ScriptGenerator()
            script = gen.generate(prompt)
            return json.dumps(script, ensure_ascii=False, indent=2)

        def run_pipeline(prompt: str) -> str:
            """一键生成完整短剧"""
            from pipeline.orchestrator import DramaOrchestrator
            orch = DramaOrchestrator()
            result = orch.run(prompt)
            return f"短剧生成完成: {result}"

        tools.register("write_script", "创作短剧剧本。参数: prompt(创作需求)", 
                       lambda prompt: write_script(prompt))
        tools.register("run_pipeline", "一键生成完整短剧。参数: prompt(创作需求)",
                       lambda prompt: run_pipeline(prompt))
