"""
Seven Lamps - Pygame UI Module
七灯 pygame 图形界面模块

Usage:
    from seven_lamps.ui.pygame import PygameUI
    ui = PygameUI()
    ui.run()

Or from CLI:
    python -m seven_lamps.ui.pygame
"""
from .game_app import GameApp


class PygameUI:
    """Pygame 界面包装类"""
    
    def __init__(self):
        self.app = GameApp()
    
    def run(self):
        """启动游戏"""
        self.app.run()


def main():
    """命令行入口"""
    ui = PygameUI()
    ui.run()


if __name__ == "__main__":
    main()
