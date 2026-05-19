"""
Seven Lamps Card Game - Base Card Class
七灯卡牌对战系统 - 卡牌基类
"""
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass, field
from ..core.enums import CardType, CardCategory, ClassType


@dataclass
class Card:
    """
    卡牌基类 - 所有卡牌的统一接口
    
    设计原则：
    - 用数据驱动：门槛、效果、触发条件都是配置
    - effect_fn 是核心：接收 (game_state, caster, target) 返回执行日志
    - check_playable 判断是否可打出（门槛检查）
    - response_check 判断响应牌是否触发
    """
    id: str                      # 唯一标识
    name: str                    # 牌名
    class_type: ClassType        # 所属职业
    card_type: CardType          # 卡牌类型
    category: CardCategory       # 子分类
    
    # 门槛条件（字符串表达式，用于描述和程序判断）
    threshold_desc: str = ""     # 如 "≥1", "=6", "≤2", "敌方≥3"
    threshold_fn: Optional[Callable] = None  # 判断门槛的函数
    
    # 效果
    effect_desc: str = ""        # 效果文本描述
    effect_fn: Optional[Callable] = None       # 效果执行函数
    
    # 响应牌专用
    trigger_desc: str = ""      # 触发条件描述
    trigger_fn: Optional[Callable] = None    # 触发条件判断函数
    
    # 元数据
    is_breakthrough: bool = False  # 是否跳过响应检查（如焚天）
    tags: List[str] = field(default_factory=list)  # 标签：如 ["斩杀", "绝境", "DOT"]
    
    def __post_init__(self):
        """确保函数有默认值"""
        if self.threshold_fn is None:
            self.threshold_fn = lambda gs, p: True  # 默认无门槛
        if self.effect_fn is None:
            self.effect_fn = lambda gs, caster, target: {"success": False, "msg": "无效果"}
        if self.trigger_fn is None:
            self.trigger_fn = lambda gs, owner, action, action_card: False
    
    def check_playable(self, game_state, player) -> bool:
        """检查当前玩家是否满足打出条件"""
        return self.threshold_fn(game_state, player)
    
    def check_trigger(self, game_state, owner, action_desc: str, action_card=None) -> bool:
        """检查响应牌是否被触发"""
        if self.card_type != CardType.RESPONSE:
            return False
        return self.trigger_fn(game_state, owner, action_desc, action_card)
    
    def execute(self, game_state, caster, target) -> Dict[str, Any]:
        """执行卡牌效果，返回执行日志"""
        return self.effect_fn(game_state, caster, target)
    
    def __repr__(self):
        return f"Card({self.name}, {self.class_type.value}, {self.card_type.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化，用于存档/网络传输"""
        return {
            "id": self.id,
            "name": self.name,
            "class_type": self.class_type.value,
            "card_type": self.card_type.value,
            "category": self.category.value,
            "threshold_desc": self.threshold_desc,
            "effect_desc": self.effect_desc,
            "trigger_desc": self.trigger_desc if self.card_type == CardType.RESPONSE else None,
            "tags": self.tags,
        }
