# AI Engines — 引擎库

本目录记录 AI 短剧工厂使用的所有外部引擎。所有引擎保持原样，不做修改。

## 已使用的引擎

| 引擎 | 路径 | 用途 | 状态 |
|------|------|------|------|
| GBTXIAOTUDOUAI | `C:/Users/ADMIN/GBTXIAOTUDOUAI` | AI Agent框架(大脑) | ✅ 已就绪 |
| SkyReels-V1 | `C:/Users/ADMIN/SkyReels-V1` | 视频生成(文生视频) | ⚠️ 需RTX4090 |
| ChatTTS | `C:/Users/ADMIN/AI-Engines/ChatTTS` | 语音合成 | ⏳ 克隆中 |

## 推荐补充的引擎

| 引擎 | GitHub | 用途 | 优先级 |
|------|--------|------|--------|
| ComfyUI | comfyanonymous/ComfyUI | 可视化视频生成 | 🔴 高 |
| CogVideoX | THUDM/CogVideoX | 低门槛视频生成(12GB) | 🔴 高 |
| GPT-SoVITS | RVC-Boss/GPT-SoVITS | 高质量语音克隆 | 🟡 中 |
| Wan2.1 | Wan-Video/Wan2.1 | 最新开源视频模型 | 🟡 中 |
| InstantID | InstantID/InstantID | 角色一致性 | 🟡 中 |
| FFmpeg | (系统安装) | 视频剪辑合成 | 🔴 必需 |

## 使用原则

- 所有引擎保持与原仓库一致，不做任何修改
- 通过 `pipeline/` 中的适配器统一调用
- 配置路径放在 `config/settings.py`
