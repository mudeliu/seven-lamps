"""
Seven Lamps - Pygame Assets
七灯 pygame 资源与样式定义
"""
import pygame

# ============ 窗口 ============
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# ============ 颜色 ============
class Colors:
    BG = (15, 20, 35)           # 深蓝黑背景
    BG_PANEL = (25, 32, 55)     # 面板背景
    BG_CARD = (45, 52, 75)      # 卡牌背景
    
    TEXT = (220, 220, 230)      # 主文字
    TEXT_DIM = (140, 145, 160)  # 次要文字
    TEXT_HIGHLIGHT = (255, 215, 100)  # 高亮文字（金色）
    
    LAMP_LIT = (255, 200, 80)   # 灯亮（暖黄）
    LAMP_EMPTY = (60, 65, 85)   # 灯灭（暗灰）
    
    BORDER = (70, 78, 105)      # 边框
    BORDER_ACTIVE = (100, 160, 255)  # 激活边框（蓝色）
    
    CARD_INSTANT = (80, 130, 180)   # 即时牌
    CARD_RESPONSE = (140, 100, 160) # 响应牌
    CARD_SPECIAL = (180, 130, 80)   # 特殊牌
    
    BUTTON = (60, 70, 100)      # 按钮
    BUTTON_HOVER = (80, 95, 140) # 按钮悬停
    
    RED = (220, 90, 90)         # 红色（警告/减灯）
    GREEN = (100, 200, 120)     # 绿色（加灯/正面）
    BLUE = (100, 160, 220)      # 蓝色（信息）

# ============ 字体 ============
def get_font(size: int) -> pygame.font.Font:
    """获取字体，优先系统黑体"""
    fonts_to_try = [
        "simhei",           # 黑体（Windows常见）
        "microsoftyahei",   # 微软雅黑
        "simsun",           # 宋体
        "arialunicode",     # Arial Unicode
    ]
    for name in fonts_to_try:
        try:
            return pygame.font.SysFont(name, size)
        except:
            continue
    return pygame.font.SysFont("arial", size)

# ============ 卡牌尺寸 ============
CARD_WIDTH = 140
CARD_HEIGHT = 200
CARD_MARGIN = 16

# ============ 位置布局 ============
class Layout:
    # 玩家1（自己）区域 — 底部
    P1_PANEL_Y = 520
    P1_PANEL_H = 200
    
    # 玩家2（对手）区域 — 顶部
    P2_PANEL_Y = 0
    P2_PANEL_H = 200
    
    # 中间战场区域
    BATTLE_Y = 200
    BATTLE_H = 320
    
    # 手牌区域
    HAND_Y = 560
    
    # 中央信息区
    CENTER_INFO_X = 540
    CENTER_INFO_Y = 320

# ============ 动画常量 ============
ANIM_DURATION = 0.3  # 动画持续时间（秒）
