"""
Seven Lamps Card Game - Response Zone (Mystery) System
七灯卡牌对战系统 - 响应区（奥秘）系统
"""
from typing import List, Dict, Optional
from ..core.enums import CardType
from ..core.constants import RESPONSE_ZONE_LIMIT


class ResponseZone:
    """
    响应区：暗置卡牌区域，最多2张
    对手可见"有几张"但不可见内容
    """
    
    def __init__(self):
        self.cards: List = []  # Card objects, face down
    
    def can_add(self) -> bool:
        return len(self.cards) < RESPONSE_ZONE_LIMIT
    
    def is_full(self) -> bool:
        return len(self.cards) >= RESPONSE_ZONE_LIMIT
    
    def add_card(self, card) -> Dict:
        """放入响应牌，若已满需替换"""
        if self.is_full():
            return {"success": False, "msg": "响应区已满，需替换一张", "need_replace": True}
        self.cards.append(card)
        return {
            "success": True,
            "msg": f"奥秘 [{card.name}] 已暗置",
            "count": len(self.cards)
        }
    
    def replace_card(self, card, replace_idx: int) -> Dict:
        """替换指定位置的响应牌，被替换的进入弃牌堆"""
        if 0 <= replace_idx < len(self.cards):
            old = self.cards[replace_idx]
            self.cards[replace_idx] = card
            return {
                "success": True,
                "msg": f"奥秘 [{card.name}] 替换 [{old.name}]",
                "replaced": old,
                "count": len(self.cards)
            }
        return {"success": False, "msg": "替换位置无效"}
    
    def remove_card(self, idx: int) -> Optional:
        """移除指定位置的响应牌（触发后进入弃牌堆）"""
        if 0 <= idx < len(self.cards):
            return self.cards.pop(idx)
        return None
    
    def check_triggers(self, game_state, owner, action_desc: str, action_card=None) -> List[Dict]:
        """
        检查所有响应牌是否被触发
        返回触发列表，按触发顺序排列
        """
        triggered = []
        for i, card in enumerate(self.cards):
            if card.card_type == CardType.RESPONSE:
                if card.check_trigger(game_state, owner, action_desc, action_card):
                    triggered.append({
                        "index": i,
                        "card": card,
                        "owner": owner,
                    })
        return triggered
    
    def get_public_info(self) -> Dict:
        """对手可见的公开信息"""
        return {
            "count": len(self.cards),
            "has_mystery": len(self.cards) > 0,
        }
    
    def get_full_info(self) -> List[Dict]:
        """持有者可见的完整信息"""
        return [c.to_dict() for c in self.cards]
    
    def to_dict(self) -> Dict:
        return {
            "count": len(self.cards),
            "cards": [c.name for c in self.cards],  # 仅内部使用
        }
