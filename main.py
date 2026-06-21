"""
main.py — GBT AI短剧工厂入口
一键生成AI短剧
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("C:/Users/ADMIN/GBTXIAOTUDOUAI")))

from pipeline.orchestrator import DramaOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="GBT AI Short Drama Factory - 一键AI短剧生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --prompt "古装武侠短剧，主角为师父复仇"
  python main.py --prompt "现代都市甜宠短剧，霸总与灰姑娘" --no-video
  python main.py --prompt "悬疑推理短剧，密室杀人案" --output mystery
  python main.py --script-only --prompt "玄幻修仙短剧"
        """
    )
    parser.add_argument("--prompt", "-p", type=str, required=True,
                        help="创作需求描述")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="输出文件名(不含扩展名)")
    parser.add_argument("--no-video", action="store_true",
                        help="跳过视频生成(仅剧本+配音)")
    parser.add_argument("--no-audio", action="store_true",
                        help="跳过配音生成")
    parser.add_argument("--script-only", action="store_true",
                        help="仅生成剧本JSON")

    args = parser.parse_args()

    orch = DramaOrchestrator()

    if args.script_only:
        script = orch.generate_script_only(args.prompt)
        print(f"\n剧本已生成: {orch.script_gen.SCRIPTS_DIR}")
    else:
        final_path = orch.run(
            prompt=args.prompt,
            output_name=args.output,
            generate_video=not args.no_video,
            generate_audio=not args.no_audio
        )
        print(f"\n✅ 短剧已生成: {final_path}")


if __name__ == "__main__":
    main()
