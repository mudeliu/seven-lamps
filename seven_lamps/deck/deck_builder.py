"""
Seven Lamps Card Game - Deck Builder
七灯卡牌对战系统 - 组牌系统（20选10）
"""
from typing import List, Dict, Optional
import random

from ..core.enums import ClassType
from ..core.constants import POOL_SIZE, DECK_SIZE
from ..cards.card_base import Card
from ..cards.card_registry import get_pool


class DeckBuilder:
    """
    组牌器：从20张牌池中选择10张组成牌库
    
    支持：
    - 预设推荐卡组
    - 随机生成
    - 手动选择
    """
    
    # 预设卡组（基于规则书推荐）
    PRESETS = {
        ClassType.LAMPLIGHTER: {
            "斩杀型": ["LL_01", "LL_02", "LL_03", "LL_04", "LL_19", "LL_11", "LL_13", "LL_06", "LL_10", "LL_15"],
            "防御型": ["LL_07", "LL_08", "LL_09", "LL_10", "LL_20", "LL_15", "LL_16", "LL_01", "LL_04", "LL_18"],
            "均衡型": ["LL_01", "LL_03", "LL_04", "LL_11", "LL_12", "LL_13", "LL_07", "LL_15", "LL_17"],
        },
        ClassType.NIGHTWATCH: {
            "速度型": ["NW_01", "NW_01", "NW_03", "NW_04", "NW_06", "NW_02", "NW_13", "NW_15"],
            "操控型": ["NW_07", "NW_11", "NW_09", "NW_19", "NW_12", "NW_08", "NW_14", "NW_16"],
            "均衡型": ["NW_01", "NW_03", "NW_05", "NW_11", "NW_13", "NW_15"],
            "奇袭型": ["NW_17", "NW_18", "NW_05", "NW_06", "NW_01", "NW_02", "NW_13", "NW_16"],
        },
        ClassType.EXTINGUISHER: {
            "爆发型": ["EX_01", "EX_02", "EX_04", "EX_05", "EX_06", "EX_13", "EX_14", "EX_08", "EX_19", "EX_18"],
            "持续型": ["EX_01", "EX_03", "EX_07", "EX_09", "EX_10", "EX_11", "EX_12", "EX_15", "EX_16"],
            "均衡型": ["EX_01", "EX_02", "EX_03", "EX_07", "EX_09", "EX_13", "EX_15", "EX_17"],
        }
    }
    
    def __init__(self, class_type: ClassType):
        self.class_type = class_type
        self.pool = get_pool(class_type)
        self.pool_by_id = {c.id: c for c in self.pool}
    
    def get_pool_cards(self) -> List[Card]:
        """获取完整牌池"""
        return self.pool
    
    def build_preset(self, preset_name: str) -> List[Card]:
        """使用预设卡组"""
        ids = self.PRESETS.get(self.class_type, {}).get(preset_name, [])
        # 填充到10张（预设可能不足，用随机补充）
        deck = [self.pool_by_id[i] for i in ids if i in self.pool_by_id]
        if len(deck) < DECK_SIZE:
            remaining = [c for c in self.pool if c not in deck]
            random.shuffle(remaining)
            deck.extend(remaining[:DECK_SIZE - len(deck)])
        return deck[:DECK_SIZE]
    
    def build_random(self, response_count: int = 2) -> List[Card]:
        """随机组牌，默认带2张响应牌"""
        responses = [c for c in self.pool if c.card_type.value == "响应牌"]
        non_responses = [c for c in self.pool if c.card_type.value != "响应牌"]
        
        deck = []
        # 选响应牌
        if responses:
            rc = min(response_count, len(responses))
            deck.extend(random.sample(responses, rc))
        # 补满
        needed = DECK_SIZE - len(deck)
        deck.extend(random.sample(non_responses, needed))
        random.shuffle(deck)
        return deck
    
    def build_manual(self, card_ids: List[str]) -> List[Card]:
        """手动指定卡牌ID"""
        deck = [self.pool_by_id[i] for i in card_ids if i in self.pool_by_id]
        return deck[:DECK_SIZE]
    
    def validate_deck(self, deck: List[Card]) -> Dict:
        """验证牌库合法性"""
        if len(deck) != DECK_SIZE:
            return {"valid": False, "msg": f"牌库需 {DECK_SIZE} 张，当前 {len(deck)} 张"}
        if any(c.class_type != self.class_type for c in deck):
            return {"valid": False, "msg": "牌库混入其他职业卡牌"}
        return {"valid": True, "msg": "牌库合法"}
    
    def list_presets(self) -> List[str]:
        """列出当前职业的可用预设"""
        return list(self.PRESETS.get(self.class_type, {}).keys())


def quick_build_deck(class_type: ClassType, preset: Optional[str] = None) -> List[Card]:
    """快速组牌入口"""
    builder = DeckBuilder(class_type)
    if preset and preset in builder.list_presets():
        return builder.build_preset(preset)
    return builder.build_random()
