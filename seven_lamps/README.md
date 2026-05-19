"""
七灯 (Seven Lamps) - 双人卡牌对战系统 v3.0
===============================================

一个专为数值策划求职Demo设计的卡牌对战引擎。

## 项目结构

```
seven_lamps/
├── core/              # 核心引擎
│   ├── enums.py       # 枚举定义（职业、卡牌类型、阶段）
│   ├── constants.py   # 游戏常量（上限、抽牌规则、疲劳）
│   ├── game_state.py  # 游戏状态管理（Player + GameState）
│   └── __init__.py
├── cards/             # 卡牌系统
│   ├── card_base.py   # Card基类（门槛/效果/触发）
│   ├── card_registry.py # 60张牌完整注册表（20×3职业）
│   └── __init__.py
├── mechanics/         # 游戏机制
│   ├── lamp_system.py    # 灯数/位置系统
│   ├── response_zone.py  # 响应区（奥秘）
│   ├── win_checker.py  # 胜负判定（三职业差异化）
│   └── __init__.py
├── deck/              # 组牌系统
│   ├── deck_builder.py # 20选10 + 预设卡组
│   └── __init__.py
├── ui/                # 交互界面
│   ├── cli.py         # 命令行对战界面
│   └── __init__.py
├── tests/             # 单元测试（待补充）
├── main.py            # 入口
└── README.md          # 本文件
```

## 快速开始

```bash
# 运行CLI对战
uv run --python 3.13 python main.py

# 或直接用Python
python main.py
```

## 核心设计

### 三职业
| 职业 | 胜利条件 | 风格 |
|------|---------|------|
| 燃灯者 | 灯数=7 | 积累/组合/斩杀 |
| 守夜人 | 奇位(1/3/5/7)全亮 | 位置操控/布局 |
| 灭灯者 | 敌方连续2回合≤2 | 压制/封锁 |

### 响应区（奥秘）
- 最多暗置2张，对手不可见内容
- 条件满足时自动触发
- 两张同时满足时由持有者决定顺序

### 组牌（20选10）
- 每职业20张专属牌，选10张组成牌库
- 预设卡组：斩杀型/防御型/均衡型/速度型/操控型/爆发型/持续型

## 调整框架

### 修改卡牌效果
编辑 `cards/card_registry.py`：
```python
cards.append(Card(
    id="LL_01", name="聚光",
    threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥1"),
    effect_fn=lambda gs, c, t: gs.add_lamps(c, 1),  # ← 改这里
))
```

### 修改常量
编辑 `core/constants.py`：
```python
MAX_LAMPS = 7           # 灯数上限
INITIAL_HAND = 4        # 起始手牌
FATIGUE_LAMP_BONUS = 2  # 疲劳加灯数
```

### 修改胜负条件
编辑 `mechanics/win_checker.py`

### 修改抽牌规则
编辑 `ui/cli.py` 中的 `get_draw_count()` 和 `get_play_limit()`

## 待完成

- [ ] 单元测试（卡牌效果验证、胜负边界）
- [ ] AI对战（随机策略 / 贪心策略 / MCTS）
- [ ] 蒙特卡洛平衡模拟器
- [ ] 可视化输出（回合日志图表）
- [ ] Web界面（可选）

## 作者
刘嘉骏 — 数值/经济系统策划求职作品集
