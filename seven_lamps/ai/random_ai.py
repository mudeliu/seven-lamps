"""
Seven Lamps Card Game - Random AI
七灯卡牌对战系统 - 随机AI（基准对照组）
"""
import random
from typing import Dict, List
from .base import BaseAI


class RandomAI(BaseAI):
    """
    完全随机AI
    - 有可出牌时: 50%概率出牌, 30%放奥秘, 20%跳过
    - 无即时牌时: 50%放奥秘, 50%跳过
    - 无响应牌时: 出牌或跳过
    """
    
    def __init__(self, seed: int = None):
        super().__init__("RandomAI")
        if seed is not None:
            random.seed(seed)
    
    def choose_action(self, game_state, player_id: str) -> Dict:
        p = game_state.players[player_id]
        playable = self._get_playable_cards(game_state, player_id)
        responses = self._get_response_cards(game_state, player_id)
        
        # 被封锁响应区
        can_response = not p.lock_response_next_turn and len(p.response_zone.cards) < 2
        
        choices = []
        if playable:
            choices.append(("play", 0.5))
        if responses and can_response:
            choices.append(("response", 0.3))
        choices.append(("skip", 0.2))
        
        if not choices:
            return {"action": "skip"}
        
        # 按权重随机选择
        total = sum(w for _, w in choices)
        r = random.uniform(0, total)
        cum = 0
        for action, weight in choices:
            cum += weight
            if r <= cum:
                if action == "play":
                    idx = random.choice(playable)[0]
                    return {"action": "play", "card_index": idx}
                elif action == "response":
                    idx = random.choice(responses)[0]
                    return {"action": "response", "card_index": idx}
                else:
                    return {"action": "skip"}
        
        return {"action": "skip"}
    
    def choose_discard(self, game_state, player_id: str, excess: int) -> List[int]:
        p = game_state.players[player_id]
        indices = list(range(len(p.hand)))
        random.shuffle(indices)
        return indices[:excess]
    
    def choose_response_replace(self, game_state, player_id: str) -> int:
        return random.randint(0, 1)
