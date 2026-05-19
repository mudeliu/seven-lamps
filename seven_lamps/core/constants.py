"""
Seven Lamps Card Game - Constants
七灯卡牌对战系统 - 游戏常量
"""

# ============ 灯系统 ============
MAX_LAMPS = 7           # 灯数上限
MIN_LAMPS = 0           # 灯数下限
INITIAL_LAMPS_FIRST = 2  # 先手初始灯数
INITIAL_LAMPS_SECOND = 3 # 后手初始灯数（补偿）

# ============ 位置系统（守夜人） ============
POSITION_COUNT = 7      # 1~7号位
ODD_POSITIONS = [1, 3, 5, 7]  # 奇数位（胜利位）
EVEN_POSITIONS = [2, 4, 6]    # 偶数位

# ============ 牌库 ============
POOL_SIZE = 20          # 每职业牌池大小
DECK_SIZE = 10          # 组牌数量
INITIAL_HAND = 4        # 起始手牌
HAND_LIMIT = 7        # 手牌上限

# ============ 响应区 ============
RESPONSE_ZONE_LIMIT = 2  # 响应区上限

# ============ 抽牌规则（分阶段） ============
DRAW_PHASE_1 = 1        # 第1-3回合抽牌数
DRAW_PHASE_2 = 2        # 第4回合起抽牌数

# ============ 回合阶段分界 ============
PHASE_1_END = 3         # 前期结束回合
PHASE_2_END = 6         # 中期结束回合
BREAKOUT_TURN = 7       # 决胜回合（可出2张牌）

# ============ 疲劳规则 ============
FATIGUE_LAMP_BONUS = 2  # 第7回合结束未分胜负，双方+2灯

# ============ 灭灯者胜利计数 ============
EXTINGUISHER_WIN_CONSECUTIVE = 2  # 连续2回合≤2

# ============ 游戏时长 ============
IDEAL_TURN_LIMIT = 7    # 理想对局回合数

# ============ 调试 ============
DEBUG_MODE = False
