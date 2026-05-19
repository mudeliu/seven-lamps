"""
Seven Lamps Card Game - Greedy AI
七灯卡牌对战系统 - 贪心AI（按职业特性优先选择）
"""
import random
from typing import Dict, List, Tuple
from .base import BaseAI
from ..core.enums import ClassType


class GreedyAI(BaseAI):
    """
    贪心AI - 按职业目标最大化即时收益
    
    燃灯者: 优先选择使自己灯数增加最多的牌
    守夜人: 优先选择能亮起奇数位的牌
    灭灯者: 优先选择能减少敌方灯数的牌
    
    所有职业: 血量危险时(≤2)优先使用反击/绝境牌
    """
    
    def __init__(self, name: str = "GreedyAI"):
        super().__init__(name)
    
    def choose_action(self, game_state, player_id: str) -> Dict:
        p = game_state.players[player_id]
        class_type = p.class_type
        lamps = game_state.get_lamps(player_id)
        opp = game_state.get_opponent(player_id)
        opp_lamps = game_state.get_lamps(opp.player_id)
        
        playable = self._get_playable_cards(game_state, player_id)
        responses = self._get_response_cards(game_state, player_id)
        can_response = not p.lock_response_next_turn and len(p.response_zone.cards) < 2
        
        # 绝境判断: 血量极低时优先保命牌
        is_danger = lamps <= 2
        
        # 评分所有可选动作
        candidates = []
        
        # 1. 即时牌评分
        for idx, card in playable:
            score = self._score_card(game_state, player_id, card, lamps, opp_lamps, class_type, is_danger)
            candidates.append(("play", idx, score, card.name))
        
        # 2. 响应牌评分 (奥秘有一定价值，但不宜过多)
        if responses and can_response:
            response_score = 15 if len(p.response_zone.cards) == 0 else 5
            for idx, card in responses:
                candidates.append(("response", idx, response_score, card.name))
        
        # 3. 跳过
        candidates.append(("skip", -1, 0, "skip"))
        
        if not candidates:
            return {"action": "skip"}
        
        # 选择最高分 (有10%随机性避免过于死板)
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        # 前两名有竞争时随机
        if len(candidates) >= 2 and random.random() < 0.1:
            top = candidates[:2]
        else:
            top = candidates[:1]
        
        chosen = random.choice(top)
        return {"action": chosen[0], "card_index": chosen[1]}
    
    def _score_card(self, gs, pid, card, lamps, opp_lamps, class_type, is_danger) -> float:
        """为单张牌打分"""
        score = 10  # 基础分
        name = card.name
        desc = card.effect_desc
        
        # === 通用评分 ===
        # 斩杀牌高分
        if "斩杀" in card.tags or "获胜" in desc:
            score += 100
        
        # 绝境牌在危险时极高
        if is_danger and ("绝境" in card.tags or "反击" in card.tags):
            score += 80
        
        # 过牌有价值
        if "抽" in desc:
            score += 15
        
        # === 职业特化评分 ===
        if class_type == ClassType.LAMPLIGHTER:
            score += self._score_lamplighter(name, desc, lamps, opp_lamps, card.tags)
        elif class_type == ClassType.NIGHTWATCH:
            score += self._score_nightwatch(name, desc, gs, pid, card.tags)
        elif class_type == ClassType.EXTINGUISHER:
            score += self._score_extinguisher(name, desc, lamps, opp_lamps, card.tags)
        
        return score
    
    def _score_lamplighter(self, name, desc, lamps, opp_lamps, tags) -> float:
        s = 0
        # 加灯效果量化
        if "+3" in desc: s += 50
        elif "+2" in desc: s += 40
        elif "+1" in desc: s += 20
        
        # 接近胜利时斩杀牌极高
        if lamps >= 5:
            if "斩杀" in tags or name in ["辉耀", "焚天"]:
                s += 100
        
        # 组合牌有配合价值
        if name == "引火" and "复制" in desc:
            s += 35  # 假设能复制到+2就是高收益
        
        # 防御奥秘
        if "护焰" in name or "反噬" in name:
            s += 25
        
        return s
    
    def _score_nightwatch(self, name, desc, gs, pid, tags) -> float:
        s = 0
        p = gs.players[pid]
        odd_lit = p.lamp_system.count_odd_lit()
        
        # 亮起奇位直接推进胜利
        if "亮起" in desc and "奇位" in desc:
            s += 50
        if "全明" in name:
            s += 60
        
        # 操控敌方有价值
        if "熄灭" in desc and "敌方" in desc:
            s += 35
        if "换位" in name or "散位" in name:
            s += 30
        
        # 特殊逆转牌
        if "位换" in name and odd_lit <= 1:
            s += 70  # 劣势时价值极高
        if "隐位" in name:
            even_count = p.lamp_system.count_even_lit()
            s += even_count * 25  # 偶位越多价值越高
        
        return s
    
    def _score_extinguisher(self, name, desc, lamps, opp_lamps, tags) -> float:
        s = 0
        # 减灯效果
        if "-3" in desc: s += 60
        elif "-2" in desc: s += 45
        elif "-1" in desc: s += 25
        
        # 敌方高灯时深幽/熄灯价值高
        if opp_lamps >= 5:
            if "深幽" in name or "熄灯" in name:
                s += 40
        
        # 封锁有价值
        if "封锁" in tags or "不能" in desc:
            s += 20
        
        # 特殊牌
        if "暗雾" in name and opp_lamps <= 3:
            s += 55  # 可能直接触发胜利条件
        
        return s
    
    def choose_discard(self, game_state, player_id: str, excess: int) -> List[int]:
        p = game_state.players[player_id]
        # 评分每张手牌，弃掉价值最低的
        scored = []
        for i, card in enumerate(p.hand):
            # 响应牌通常保留，绝境牌保留
            if "响应牌" in card.card_type.value:
                score = 100
            elif "绝境" in card.tags:
                score = 90
            else:
                score = 10
            scored.append((score, i))
        
        scored.sort()
        return [idx for _, idx in scored[:excess]]
