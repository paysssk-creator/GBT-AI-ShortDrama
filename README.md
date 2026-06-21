# 🎬 GBT AI Short Drama Factory

> GBT小土豆全能开发者 — AI短剧全自动生成工厂

基于 GBT AI Agent 框架编排 SkyReels-V1 / CogVideoX / ChatTTS 等开源引擎，实现 **剧本→视频→配音→合成** 全自动流水线。

## 🏗️ 架构

```
GBTXIAOTUDOUAI (大脑)     SkyReels-V1/CogVideoX     ChatTTS/Edge-TTS
   SmartRouter         →   视频生成引擎          →  语音合成引擎
   AutonomousBrain          (不改原仓库)            (不改原仓库)
        ↓                        ↓                       ↓
   ┌─────────────────────────────────────────────────┐
   │           GBT AI Short Drama Factory             │
   │  main.py → orchestrator → script_gen            │
   │                          → video_gen             │
   │                          → tts_gen               │
   │                          → compose               │
   └─────────────────────────────────────────────────┘
                           ↓
                    最终短剧 .mp4
```

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置 LLM API Key (任一即可)
set GLM_API_KEY=your_zhipu_key
set OPENAI_API_KEY=your_openai_key

# 3. 生成短剧
python main.py --prompt "古装武侠短剧，主角为师父复仇"

# 仅生成剧本预览
python main.py --prompt "现代都市甜宠短剧" --script-only

# 不生成视频(仅剧本+配音)
python main.py --prompt "悬疑推理短剧" --no-video
```

## 📂 项目结构

```
GBT-AI-ShortDrama/
├── main.py                    # 入口
├── pipeline/                  # 流水线核心
│   ├── orchestrator.py        # 总调度器
│   ├── script_gen.py          # 剧本生成(GBTLLM)
│   ├── video_gen.py           # 视频生成适配器
│   ├── video_gen_impl.py      # 视频生成实现
│   ├── tts_gen.py             # 语音合成适配器
│   └── compose.py             # 剪辑合成器
├── gbt_adapter/               # GBT框架集成
│   └── drama_agent.py         # 短剧导演Agent
├── config/                    # 配置
│   ├── settings.py            # 全局设置
│   └── characters.json        # 角色库
├── engines/                   # 引擎清单
│   └── README.md              # 引擎使用说明
├── output/                    # 生成产物
│   ├── scripts/               # 剧本JSON
│   ├── videos/                # 场景视频
│   ├── audio/                 # 配音文件
│   └── final/                 # 最终短剧
└── requirements.txt
```

## 🔧 引擎配置

通过环境变量切换引擎：

```bash
# 视频引擎: skyreels | diffusers | comfyui
set GBT_VIDEO_ENGINE=diffusers

# TTS引擎: edge-tts | chattts
set GBT_TTS_ENGINE=edge-tts

# LLM提供商: auto | zhipu | openai | deepseek | ollama
set GBT_DRAMA_LLM=zhipu
```

## 📝 剧本格式

生成的剧本为 JSON 格式，每个场景包含：

- `visual_prompt`: 英文画面描述(用于AI视频生成)
- `dialogues`: 角色对话
- `narration`: 旁白
- `location/time/mood`: 场景设定

## ⚠️ 前置要求

- Python 3.11+
- FFmpeg (系统安装)
- GPU (可选，有GPU时视频生成更快)
  - RTX 4090: 可使用 SkyReels-V1 引擎
  - RTX 3060+: 可使用 CogVideoX/Diffusers 引擎
  - 无GPU: 仅生成剧本+配音

## 📄 License

MIT — 基于多个开源项目组装，各引擎遵循各自的许可证。
