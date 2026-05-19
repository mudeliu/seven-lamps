"""
Seven Lamps Card Game
七灯卡牌对战系统 - 入口

运行方式:
    python main.py           # 默认启动 CLI
    python main.py --pygame  # 启动 Pygame 图形界面
    python main.py --cli     # 启动 CLI（显式）
"""
import sys
import os

# 确保能导入本地模块（项目根目录）
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)


def main():
    # 解析参数
    use_pygame = "--pygame" in sys.argv
    
    if use_pygame:
        try:
            from seven_lamps.ui.pygame import PygameUI
            ui = PygameUI()
            ui.run()
        except ImportError as e:
            print(f"❌ Pygame 启动失败: {e}")
            print("请确保已安装 pygame: pip install pygame")
            sys.exit(1)
    else:
        from seven_lamps.ui.cli import CLI
        cli = CLI()
        try:
            cli.run()
        except KeyboardInterrupt:
            print("\n\n游戏中断。再见！")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
