"""
Seven Lamps Card Game - Core Enums
七灯卡牌对战系统 - 核心枚举
"""
from enum import Enum, auto


class ClassType(Enum):
    """三职业类型"""
    LAMPLIGHTER = "燃灯者"      # 灯数=7获胜
    NIGHTWATCH = "守夜人"       # 奇数位(1/3/5/7)全亮获胜
    EXTINGUISHER = "灭灯者"     # 敌方连续2回合≤2获胜


class CardType(Enum):
    """卡牌类型"""
    INSTANT = "即时牌"
    RESPONSE = "响应牌"         # 奥秘，暗置
    SPECIAL = "特殊牌"


class CardCategory(Enum):
    """卡牌子分类（用于组牌参考）"""
    # 燃灯者
    ACCUMULATION = "积累"
    COUNTER = "反击"
    COMBO = "组合"
    # 守夜人
    FILL = "填充"
    MANIPULATE = "操控"
    # 灭灯者
    REDUCE = "减灯"
    LOCK = "封锁"
    # 通用
    RESPONSE = "奥秘"
    SPECIAL = "特殊"


class Phase(Enum):
    """回合阶段"""
    TURN_START = auto()
    DRAW = auto()
    PLAY = auto()
    RESOLVE = auto()
    WIN_CHECK = auto()
    TURN_END = auto()


class PlayAction(Enum):
    """出牌阶段可执行的动作"""
    PLAY_INSTANT = auto()       # 打出即时牌
    PLAY_RESPONSE = auto()      # 放入响应牌（奥秘）
    SKIP = auto()               # 跳过


class Target(Enum):
    """效果目标"""
    SELF = auto()
    OPPONENT = auto()
    BOTH = auto()


class PositionState(Enum):
    """位置状态（守夜人）"""
    EMPTY = auto()
    LIT = auto()
