"""
Seven Lamps Card Game - AI Base Class
七灯卡牌对战系统 - AI策略基类
"""
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod


class BaseAI(ABC):
    """
    AI策略基类
    
    所有AI需要实现:
    - choose_action: 选择本回合动作 (出牌/放奥秘/跳过)
    - choose_discard: 选择弃牌
    """
    
    def __init__(self, name: str = "AI"):
        self.name = name
    
    @abstractmethod
    def choose_action(self, game_state, player_id: str) -> Dict:
        """
        选择动作
        返回 {"action": "play"/"response"/"skip", "card_index": int}
        """
        pass
    
    def choose_discard(self, game_state, player_id: str, excess: int) -> List[int]:
        """
        选择弃牌（默认弃掉最前面的）
        返回要弃掉的牌索引列表
        """
        return list(range(excess))
    
    def choose_response_replace(self, game_state, player_id: str) -> int:
        """响应区已满时选择替换哪张（默认替换第一张）"""
        return 0
    
    def _get_playable_cards(self, game_state, player_id: str) -> List[Tuple[int, object]]:
        """获取当前可打出的即时牌列表 (手牌索引, 卡牌)"""
        p = game_state.players[player_id]
        playable = []
        for i, card in enumerate(p.hand):
            if card.card_type.value != "响应牌" and card.check_playable(game_state, player_id):
                playable.append((i, card))
        return playable
    
    def _get_response_cards(self, game_state, player_id: str) -> List[Tuple[int, object]]:
        """获取手中响应牌列表"""
        p = game_state.players[player_id]
        responses = []
        for i, card in enumerate(p.hand):
            if card.card_type.value == "响应牌":
                responses.append((i, card))
        return responses
