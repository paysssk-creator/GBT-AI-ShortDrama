"""
desktop_app.py — GBT AI短剧工厂 桌面APP
Gradio Web UI + 一键启动
"""
import sys, os, json, time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, "C:/Users/ADMIN/GBTXIAOTUDOUAI")

import gradio as gr
from config.settings import *
from pipeline.script_gen import ScriptGenerator
from pipeline.tts_gen import TTSGenerator
from pipeline.compose import VideoComposer
from pipeline.novel_scraper import NovelScraper
from pipeline.novel_pipeline import NovelDramaPipeline

# 懒加载
_script_gen = None
_tts_gen = None

def get_script_gen():
    global _script_gen
    if _script_gen is None: _script_gen = ScriptGenerator()
    return _script_gen

def get_tts_gen():
    global _tts_gen
    if _tts_gen is None: _tts_gen = TTSGenerator()
    return _tts_gen

# === UI 回調函數 ===

def generate_script_ui(prompt, genre, scene_count):
    if not prompt.strip(): return "请输入创作需求", None, None
    log = [f"[{datetime.now().strftime('%H:%M:%S')}] 开始创作..."]
    try:
        gen = get_script_gen()
        full_prompt = f"{prompt}\n类型:{genre}\n场景数:{scene_count}"
        script = gen.generate(full_prompt)
        title = script.get("title", "未命名")
        scenes = script.get("scenes", [])
        log.append(f"✅ 《{title}》| {len(scenes)}个场景")
        preview = ""
        for s in scenes:
            sid = s.get("scene_id","?")
            loc = s.get("location","")
            mood = s.get("mood","")
            action = s.get("action","")
            dlg = " | ".join(f"{d['character']}: {d['text']}" for d in s.get("dialogues",[])[:2])
            preview += f"### 场景{sid}: {loc} ({mood})\n> {action}\n> 💬 {dlg}\n\n"
        return "\n".join(log), preview, json.dumps(script, ensure_ascii=False, indent=2)
    except Exception as e:
        log.append(f"❌ {e}")
        return "\n".join(log), f"失败: {e}", None

def generate_tts_ui(text, voice, speed):
    if not text.strip(): return "请输入文本", None
    log = [f"[{datetime.now().strftime('%H:%M:%S')}] 合成中..."]
    try:
        tts = get_tts_gen()
        path = tts.synthesize(text, voice, f"tts_preview_{int(time.time())}")
        log.append(f"✅ {path.name}")
        return "\n".join(log), str(path)
    except Exception as e:
        log.append(f"❌ {e}")
        return "\n".join(log), None

def run_full_pipeline_ui(prompt, genre, scene_count, enable_audio):
    log = []
    if not prompt.strip():
        return "❌ 请输入创作需求", None
    log.append("━"*40)
    log.append(f"  GBT AI短剧工厂 v1.0 | {datetime.now().strftime('%H:%M:%S')}")
    log.append("━"*40)
    try:
        # Step1: 剧本
        log.append(f"\n📜 [1/3] 生成剧本...")
        gen = get_script_gen()
        script = gen.generate(f"{prompt}\n类型:{genre}\n场景数:{scene_count}")
        scenes = script.get("scenes", [])
        log.append(f"  ✅ 《{script.get('title','N/A')}》{len(scenes)}个场景")
        # Step2: 配音
        all_audios = []
        if enable_audio:
            log.append(f"\n🔊 [2/3] 生成配音...")
            tts = get_tts_gen()
            for i, scene in enumerate(scenes):
                dialogues = scene.get("dialogues", [])
                narration = scene.get("narration", "")
                if narration:
                    tts.synthesize(narration, output_name=f"scene_{i+1:02d}_narration")
                scene_audios = []
                for d in dialogues:
                    ap = tts.synthesize(d["text"], output_name=f"scene_{i+1:02d}_{d['character']}")
                    scene_audios.append({"character": d["character"], "text": d["text"], "audio_path": ap})
                all_audios.append(scene_audios)
                log.append(f"  场景{i+1}: {len(scene_audios)}句 ✓")
        else:
            log.append(f"\n⏭️ [2/3] 跳过配音")
        # Step3: 保存
        log.append(f"\n💾 [3/3] 保存项目...")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sp = SCRIPTS_DIR / f"script_{ts}.json"
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        log.append(f"  ✅ 剧本: {sp.name}")
        log.append(f"  ✅ 配音: {AUDIO_DIR}")
        log.append(f"\n🎬 完成! 输出: {OUTPUT_DIR}")
        log.append(f"   ⚠️ 视频需GPU: pip install diffusers")
        return "\n".join(log), str(sp)
    except Exception as e:
        import traceback
        log.append(f"\n❌ {e}\n{traceback.format_exc()}")
        return "\n".join(log), None

# === 玄幻小说 → 短剧 ===

def fetch_ranking_ui(source):
    """UI: 获取玄幻排行榜"""
    try:
        scraper = NovelScraper(source)
        novels = scraper.fetch_ranking(15)
        if not novels:
            return "No novels found", gr.update(choices=[])
        table = "| # | Title | Author |\n|---|-------|--------|\n"
        choices = []
        for n in novels:
            table += f"| {n['rank']} | {n['title'][:30]} | {n['author']} |\n"
            choices.append(f"#{n['rank']} {n['title'][:40]} - {n['author']}")
        return table, gr.update(choices=choices, value=choices[0] if choices else None)
    except Exception as e:
        return f"Error: {e}", gr.update(choices=[])

def novel_to_drama_ui(source, rank, enable_audio):
    """UI: 玄幻小说→AI短剧 全自动"""
    if not rank or not rank.strip():
        return "Please fetch ranking first", None, None
    log = []
    try:
        rank_num = int(rank.split("#")[1].split()[0]) if "#" in rank else 1
    except:
        rank_num = 1

    log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting novel->drama pipeline")
    
    try:
        pipeline = NovelDramaPipeline()
        result = pipeline.run_novel(rank=rank_num)
        
        if not result.get("ok"):
            err = result.get("error", "Unknown error")
            log_lines = result.get("log", [])
            return "\n".join(log_lines), f"FAILED: {err}", None
        
        if result.get("skipped"):
            return "\n".join(result.get("log", [])), "SKIPPED (already processed)", None
        
        log_lines = result.get("log", [])
        scripts = result.get("scripts", [])
        total = result.get("total_chapters", 0)
        done = result.get("completed", 0)
        
        preview = json.dumps({
            "total_chapters": total,
            "completed": done,
            "skipped": result.get("skipped", 0),
            "failed": result.get("failed", 0),
            "sample": scripts[0] if scripts else None,
        }, ensure_ascii=False, indent=2)
        
        return "\n".join(log_lines), f"DONE: {done}/{total} chapters", preview
    except Exception as e:
        import traceback
        return str(e), f"Error: {e}", None

def view_output_files():
    files = []
    for d in [SCRIPTS_DIR, AUDIO_DIR]:
        if d.exists():
            for f in sorted(d.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                files.append(str(f))
    return "\n".join(files) if files else "暂无输出"

# === CSS ===
css = """
.gradio-container { max-width: 900px !important; margin: auto !important; }
.header { text-align: center; padding: 20px; background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; border-radius: 12px; margin-bottom: 20px; }
.header h1 { font-size: 2em; margin: 0; }
.log-box { font-family: Consolas, monospace; font-size: 13px; }
"""

# === 构建Gradio界面 ===
with gr.Blocks(title="GBT AI短剧工厂") as demo:
    gr.HTML("""
    <div class="header">
      <h1>🎬 GBT AI Short Drama Factory</h1>
      <p>AI短剧全自动生成工厂 | 剧本→配音→合成</p>
    </div>""")
    
    with gr.Tabs():
        with gr.TabItem("🚀 一键生成"):
            with gr.Row():
                with gr.Column(scale=2):
                    prompt_input = gr.Textbox(label="创作需求", placeholder="例: 古装武侠短剧，主角为师父复仇，5个场景", lines=3)
                    with gr.Row():
                        genre_dd = gr.Dropdown(choices=["古装武侠","现代甜宠","悬疑推理","玄幻修仙","都市逆袭","科幻未来"], value="古装武侠", label="类型")
                        scene_sl = gr.Slider(3, 10, value=5, step=1, label="场景数")
                    enable_audio_cb = gr.Checkbox(label="生成配音", value=True)
                    gen_btn = gr.Button("🎬 一键生成", variant="primary")
                with gr.Column(scale=3):
                    output_log = gr.Textbox(label="生成日志", lines=16, elem_classes="log-box")
                    output_file = gr.Textbox(label="输出文件", visible=False)
            gen_btn.click(fn=run_full_pipeline_ui, inputs=[prompt_input, genre_dd, scene_sl, enable_audio_cb], outputs=[output_log, output_file])
        
        with gr.TabItem("📜 剧本创作"):
            with gr.Row():
                with gr.Column(scale=1):
                    sp = gr.Textbox(label="故事创意", placeholder="描述你想创作的故事...", lines=4)
                    sg = gr.Dropdown(choices=["古装武侠","现代甜宠","悬疑推理","玄幻修仙","都市逆袭","科幻未来"], value="古装武侠", label="类型")
                    ss = gr.Slider(3, 10, value=5, step=1, label="场景数")
                    sb = gr.Button("📝 生成剧本", variant="primary")
                    sl = gr.Textbox(label="状态", lines=3, elem_classes="log-box")
                with gr.Column(scale=2):
                    sm = gr.Markdown("### 场景预览")
                    sj = gr.Code(label="剧本JSON", language="json", lines=14)
            sb.click(fn=generate_script_ui, inputs=[sp, sg, ss], outputs=[sl, sm, sj])
        
        with gr.TabItem("🔊 配音工坊"):
            with gr.Row():
                with gr.Column(scale=1):
                    tt = gr.Textbox(label="配音文本", placeholder="输入需要配音的文本...", lines=4)
                    tv = gr.Dropdown(choices=["zh-CN-XiaoxiaoNeural","zh-CN-YunxiNeural","zh-CN-YunyangNeural","zh-CN-YunyeNeural"], value="zh-CN-XiaoxiaoNeural", label="音色")
                    ts = gr.Dropdown(choices=["-20%","-10%","+0%","+10%","+20%"], value="+0%", label="语速")
                    tb = gr.Button("🔊 生成配音", variant="primary")
                    tl = gr.Textbox(label="状态", lines=2, elem_classes="log-box")
                with gr.Column(scale=1):
                    ta = gr.Audio(label="试听", type="filepath")
            tb.click(fn=generate_tts_ui, inputs=[tt, tv, ts], outputs=[tl, ta])
        
        with gr.TabItem("📚 玄幻小说→短剧"):
            gr.Markdown("### 玄幻排行榜 → 整本小说逐章→每章2集短剧→完结才换书")
            with gr.Row():
                with gr.Column(scale=1):
                    nsource = gr.Dropdown(choices=["biquge","69shu","biqukan"], value="biquge", label="小说源")
                    fetch_btn = gr.Button("📊 获取排行榜", variant="primary")
                    ntable = gr.Markdown("点击获取玄幻小说排行榜")
                    nrank = gr.Dropdown(choices=[], label="选择小说", interactive=True)
                    naudio = gr.Checkbox(label="生成配音", value=True)
                    ndrama_btn = gr.Button("🎬 整本→短剧(逐章2集)", variant="primary", size="lg")
                with gr.Column(scale=2):
                    nlog = gr.Textbox(label="流程日志", lines=12, elem_classes="log-box")
                    ntitle = gr.Textbox(label="结果", visible=False)
                    nscript = gr.Code(label="两集剧本 (Episode 1 + 2)", language="json", lines=16)
            fetch_btn.click(fn=fetch_ranking_ui, inputs=[nsource], outputs=[ntable, nrank])
            ndrama_btn.click(fn=novel_to_drama_ui, inputs=[nsource, nrank, naudio], outputs=[nlog, ntitle, nscript])
        
        with gr.TabItem("⚙️ 设置"):
            status = gr.Textbox(label="系统状态", value=f"""
✅ GBT框架: C:/Users/ADMIN/GBTXIAOTUDOUAI
✅ Edge-TTS: 免费可用  
⚠️ 视频生成: 需GPU + pip install diffusers
📂 {OUTPUT_DIR}""", lines=8, interactive=False)
            rb = gr.Button("🔄 刷新输出")
            fo = gr.Textbox(label="最新文件", lines=6)
            rb.click(fn=view_output_files, outputs=[fo])


if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        try: sys.stdout.reconfigure(encoding='utf-8')
        except: pass
    print("━"*50)
    print("  GBT AI Short Drama Factory - v1.0 Desktop")
    print("━"*50)
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True,
        theme=gr.themes.Soft(),
        css=css
    )
