"""
pipeline/script_gen.py — AI剧本生成器
LLM优先级: DeepSeek网页版(免费) > API > Ollama本地
"""
import json, os, sys, re, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))
from config.settings import SCRIPTS_DIR, MAX_SCENES


class DeepSeekBrowser:
    """免费DeepSeek网页版 — Playwright + nanobrowser扩展"""
    
    CHAT_URL = "https://chat.deepseek.com"
    NANO_EXT = r"C:\Users\ADMIN\nanobrowser\chrome-extension"

    def __init__(self):
        self.page = None
        self.browser = None
        self._pw = None
        self._init_browser()

    def _init_browser(self):
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            # 加载nanobrowser扩展
            args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
            self.browser = self._pw.chromium.launch(
                headless=False, args=args,
                slow_mo=100  # 模拟人类操作速度
            )
            ctx = self.browser.new_context(
                locale="zh-CN",
                viewport={"width": 1280, "height": 900}
            )
            self.page = ctx.new_page()
            # 去掉webdriver标记
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)
            self.page.goto(self.CHAT_URL, timeout=30000, wait_until="networkidle")
            time.sleep(5)
            print("[OK] DeepSeek Browser + nanobrowser ready")
        except Exception as e:
            print(f"Browser init failed: {e}")
            self.browser = None

    def chat(self, prompt: str) -> str:
        if not self.page:
            return ""
        try:
            # DeepSeek新版输入框
            selectors = [
                "textarea[placeholder*='发消息']",
                "textarea[placeholder*='message']",
                "#chat-input",
                "textarea",
                "[contenteditable='true']",
            ]
            editor = None
            for sel in selectors:
                try:
                    el = self.page.locator(sel).first
                    if el.is_visible(timeout=2000):
                        editor = el
                        break
                except:
                    continue
            if not editor:
                return ""
            
            editor.click()
            time.sleep(0.5)
            editor.fill(prompt)
            time.sleep(1)
            
            # 点发送
            send_btns = [
                "button[type='submit']",
                "[data-testid='send-button']",
                "button:has(svg)",
                ".ds-icon-button",
            ]
            for sb in send_btns:
                try:
                    btn = self.page.locator(sb).last
                    if btn.is_visible(timeout=1000):
                        btn.click()
                        break
                except:
                    continue
            
            # 等AI回复(最长120秒)
            reply_selectors = ".ds-markdown, .ds-markdown--break, [class*='markdown']"
            try:
                self.page.wait_for_function(
                    f"document.querySelectorAll('{reply_selectors}').length > 0",
                    timeout=120000
                )
            except:
                pass
            time.sleep(5)
            
            # 取最后一条
            replies = self.page.locator(reply_selectors).all()
            if replies:
                return replies[-1].inner_text()
            return ""
        except Exception as e:
            print(f"Chat err: {e}")
            return ""

    def close(self):
        if self.browser:
            try:
                self.browser.close()
            except:
                pass


class ScriptGenerator:
    """AI短剧剧本生成器"""

    SYS = """你是短剧编剧。返回严格JSON:
{"title":"剧名","genre":"类型","summary":"简介","scenes":[
{"scene_id":1,"location":"场景","time":"时间","mood":"氛围",
"visual_prompt":"英文画面描述","action":"动作",
"dialogues":[{"character":"角色","text":"台词"}],"narration":"旁白","duration_sec":4}]}
规则:3~5场景,visual_prompt英文50词内,只输出JSON"""

    def __init__(self):
        self.llm = None
        self.model = "none"
        self._openai = False
        self._browser = None
        self._init()

    def _init(self):
        # 1. DeepSeek网页(完全免费)
        try:
            self._browser = DeepSeekBrowser()
            if self._browser.browser:
                self.llm = self._browser
                self.model = "deepseek-browser"
                print("[OK] LLM: DeepSeek Web (free)")
                return
        except: pass
        # 2. DeepSeek API
        k = os.getenv("DEEPSEEK_API_KEY","")
        if k.startswith("sk-") and len(k)>20:
            try:
                from openai import OpenAI
                self.llm = OpenAI(api_key=k,base_url="https://api.deepseek.com/v1")
                self.model="deepseek-chat"; self._openai=True
                print("[OK] LLM: DeepSeek API"); return
            except: pass
        # 3. GLM
        k = os.getenv("GLM_API_KEY","")
        if k:
            try:
                from openai import OpenAI
                self.llm=OpenAI(api_key=k,base_url="https://open.bigmodel.cn/api/paas/v4")
                self.model="glm-4-flash"; self._openai=True
                print("[OK] LLM: GLM"); return
            except: pass
        # 4. OpenAI
        k = os.getenv("OPENAI_API_KEY","")
        if k.startswith("sk-"):
            try:
                from openai import OpenAI
                self.llm=OpenAI(api_key=k); self.model="gpt-4o-mini"
                self._openai=True; print("[OK] LLM: OpenAI"); return
            except: pass
        # 5. Ollama
        try:
            from gbt.llm import GBTLLM
            self.llm=GBTLLM(provider="ollama"); self.model=self.llm.model
            print(f"[OK] LLM: Ollama/{self.model}"); return
        except: pass
        raise RuntimeError("No LLM")

    def generate(self, prompt: str, characters: list = None) -> dict:
        user = f"创作需求：{prompt}"
        if characters:
            user += "\n角色：" + ",".join(c["name"] for c in characters)
        user += f"\n请生成{MAX_SCENES}个场景以内的短剧剧本。"
        msg = [{"role":"system","content":self.SYS},{"role":"user","content":user}]
        try:
            if isinstance(self.llm, DeepSeekBrowser):
                text = self._browser.chat(f"{self.SYS}\n\n{user}\n只输出JSON:")
                if not text: return self._fallback(prompt)
            elif self._openai:
                resp = self.llm.chat.completions.create(
                    model=self.model, messages=msg,
                    response_format={"type":"json_object"}, temperature=0.8)
                text = resp.choices[0].message.content
            else:
                text = self.llm.invoke(messages=msg)
            text = self._clean(text)
            s = json.loads(text)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            (SCRIPTS_DIR / f"script_{ts}.json").write_text(
                json.dumps(s,ensure_ascii=False,indent=2), encoding="utf-8")
            print(f"📜 {s['title']} | {len(s.get('scenes',[]))} scenes")
            return s
        except Exception as e:
            print(f"❌ {e}")
            return self._fallback(prompt)

    def _clean(self, t: str) -> str:
        t = t.strip()
        if t.startswith("```"): t = re.sub(r"^```\w*\n?","",t); t = re.sub(r"\n?```$","",t)
        return t

    def _fallback(self, p: str) -> dict:
        return {"title":"短剧创作","genre":"未知","summary":p[:50],
            "scenes":[{"scene_id":1,"location":"古风庭院","time":"白天",
            "mood":"宁静","visual_prompt":"FPS-24,wide shot,ancient Chinese courtyard",
            "action":"主角登场","dialogues":[{"character":"主角","text":"新的征程开始了。"}],
            "duration_sec":4}]}

