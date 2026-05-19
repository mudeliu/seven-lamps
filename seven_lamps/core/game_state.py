"""
Seven Lamps Card Game - Game State
七灯卡牌对战系统 - 游戏状态管理

这是整个游戏的核心枢纽。所有卡牌效果、响应触发、胜负判定
都通过此接口操作。
"""
from typing import Dict, List, Optional, Tuple
import random
import copy

from ..core.enums import ClassType, CardType, PositionState
from ..core.constants import (
    MAX_LAMPS, MIN_LAMPS, INITIAL_HAND, HAND_LIMIT,
    RESPONSE_ZONE_LIMIT, INITIAL_LAMPS_FIRST, INITIAL_LAMPS_SECOND,
    DRAW_PHASE_1, DRAW_PHASE_2, PHASE_1_END, PHASE_2_END,
    BREAKOUT_TURN, FATIGUE_LAMP_BONUS
)
from ..mechanics.lamp_system import LampSystem
from ..mechanics.response_zone import ResponseZone
from ..mechanics.win_checker import WinChecker


class Player:
    """玩家状态"""
    def __init__(self, player_id: str, name: str, class_type: ClassType):
        self.player_id = player_id
        self.name = name
        self.class_type = class_type
        
        # 灯系统
        self.lamp_system = LampSystem()
        
        # 响应区
        self.response_zone = ResponseZone()
        
        # 牌组
        self.deck: List = []        # 牌库（抽牌堆）
        self.hand: List = []        # 手牌
        self.discard: List = []     # 弃牌堆
        
        # 回合标记
        self.played_this_turn: bool = False
        self.was_reduced_this_turn: bool = False  # 本回合是否被减过灯
        self.played_lamp_increase_this_turn: bool = False  # 本回合是否出过增灯牌
        self.played_lamp_increase_last_turn: bool = False  # 上回合是否出过增灯牌
        self.last_played_card = None
        self.cards_played_this_turn: int = 0
        
        # 状态标记
        self.immune_reduce_next_turn: bool = False
        self.lock_response_next_turn: bool = False
        self.reduce_draw_next_turn: int = 0
        self.next_first_card_halved: bool = False
        self.next_first_card_bonus: int = 0
        self.next_turn_reduce: int = 0
        self.next_turn_card_limit: Optional[int] = None
        
        # 延迟收益/封锁
        self.pending_bonus: Optional[Dict] = None  # 焰心等延迟收益
        self.lock_lamp_increase: bool = False      # 预警封锁增灯
        
    def shuffle_deck(self):
        random.shuffle(self.deck)
    
    def draw(self, count: int = 1) -> List:
        """抽牌，牌库空时洗切弃牌堆"""
        drawn = []
        for _ in range(count):
            if len(self.deck) == 0:
                if len(self.discard) > 0:
                    self.deck = self.discard[:]
                    self.discard = []
                    random.shuffle(self.deck)
                else:
                    break
            if len(self.deck) > 0:
                drawn.append(self.deck.pop(0))
        return drawn
    
    def add_to_hand(self, cards: List):
        """加入手牌，超出上限时保留到上限"""
        self.hand.extend(cards)
        if len(self.hand) > HAND_LIMIT:
            # 需要弃牌（由UI层处理选择）
            excess = len(self.hand) - HAND_LIMIT
            return {"excess": excess, "msg": f"手牌超出上限，需弃 {excess} 张"}
        return {"excess": 0}
    
    def discard_from_hand(self, card):
        """从手牌弃掉一张"""
        if card in self.hand:
            self.hand.remove(card)
            self.discard.append(card)
    
    def play_card(self, card) -> Dict:
        """从手牌打出一张牌"""
        if card in self.hand:
            self.hand.remove(card)
            self.played_this_turn = True
            self.last_played_card = card
            self.cards_played_this_turn += 1
            # 标记本回合是否出了增灯牌
            if card and hasattr(card, 'effect_desc') and card.effect_desc:
                if any(kw in card.effect_desc for kw in ["自己+", "双方各+"]):
                    self.played_lamp_increase_this_turn = True
            return {"success": True}
        return {"success": False, "msg": "手牌中无此牌"}
    
    def reset_turn_flags(self):
        """回合开始时重置标记"""
        # 保存上回合增灯状态（供连焰等牌检查）
        self.played_lamp_increase_last_turn = self.played_lamp_increase_this_turn
        self.played_lamp_increase_this_turn = False
        
        self.played_this_turn = False
        self.was_reduced_this_turn = False
        self.cards_played_this_turn = 0
        self.immune_reduce_next_turn = False
        self.lock_response_next_turn = False
        self.reduce_draw_next_turn = 0
        self.next_first_card_halved = False
        self.next_first_card_bonus = 0
        self.next_turn_reduce = 0
        self.next_turn_card_limit = None
        self.lock_lamp_increase = False
        
    def to_dict(self) -> Dict:
        return {
            "id": self.player_id,
            "name": self.name,
            "class": self.class_type.value,
            "lamps": self.lamp_system.get_lamp_count(),
            "positions": self.lamp_system.to_dict()["positions"],
            "hand_count": len(self.hand),
            "deck_count": len(self.deck),
            "discard_count": len(self.discard),
            "response_zone": self.response_zone.get_public_info(),
        }


class GameState:
    """
    游戏状态主类：所有卡牌效果操作的中枢
    
    设计为"大面板"模式：卡牌效果函数直接操作此对象
    这样卡牌定义可以简洁地使用 lambda gs, c, t: gs.xxx()
    """
    
    def __init__(self, player_configs: List[Dict]):
        """
        player_configs: [{"id": "p1", "name": "玩家1", "class": ClassType.LAMPLIGHTER}, ...]
        """
        self.players: Dict[str, Player] = {}
        self.player_ids: List[str] = []
        self.win_checker = WinChecker()
        self.extinguisher_counters: Dict[str, int] = {}  # 灭灯者计数
        self.turn: int = 0           # 当前回合数
        self.active_player_id: Optional[str] = None
        self.game_over: bool = False
        self.winner_id: Optional[str] = None
        self.logs: List[str] = []    # 游戏日志
        
        for config in player_configs:
            pid = config["id"]
            p = Player(pid, config["name"], config["class"])
            self.players[pid] = p
            self.player_ids.append(pid)
            self.extinguisher_counters[pid] = 0
        
        # 先手/后手
        self.first_player = self.player_ids[0]
        self.second_player = self.player_ids[1]
        
        # 初始化灯数
        self.players[self.first_player].lamp_system.set_lamps(INITIAL_LAMPS_FIRST)
        self.players[self.second_player].lamp_system.set_lamps(INITIAL_LAMPS_SECOND)
    
    # ============ 灯数操作接口（供卡牌调用） ============
    def get_lamps(self, player_id: str) -> int:
        return self.players[player_id].lamp_system.get_lamp_count()
    
    def set_lamps(self, player_id: str, value: int) -> Dict:
        old = self.get_lamps(player_id)
        self.players[player_id].lamp_system.set_lamps(value)
        new = self.get_lamps(player_id)
        return {"success": True, "old": old, "new": new, "msg": f"灯数 {old} → {new}"}
    
    def add_lamps(self, player_id: str, amount: int, from_borrow: bool = False) -> Dict:
        """增加灯数"""
        if from_borrow:
            # 借光：双方+1，自己再+1
            opp = self.get_opponent(player_id)
            self.players[opp.player_id].lamp_system.add_lamps(1)
        result = self.players[player_id].lamp_system.add_lamps(amount)
        self._log(result.get("msg", ""))
        return result
    
    def reduce_lamps(self, player_id: str, amount: int) -> Dict:
        """减少灯数（受免疫保护）"""
        p = self.players[player_id]
        if p.immune_reduce_next_turn:
            self._log(f"[{p.name}] 免疫减灯效果！")
            return {"success": False, "msg": "免疫减灯", "canceled": True}
        
        result = p.lamp_system.reduce_lamps(amount)
        p.was_reduced_this_turn = True
        self._log(result.get("msg", ""))
        return result
    
    def reduce_lamps_and_destroy_response(self, player_id: str, amount: int) -> Dict:
        """晦影：减灯+破坏响应牌"""
        result = self.reduce_lamps(player_id, amount)
        opp = self.players[player_id]
        if opp.response_zone.cards:
            removed = opp.response_zone.remove_card(0)
            if removed:
                opp.discard.append(removed)
                result["destroyed_response"] = removed.name
                self._log(f"破坏了奥秘 [{removed.name}]")
        return result
    
    def reduce_and_deny_draw(self, player_id: str, amount: int) -> Dict:
        """晦明：减灯+可能禁抽"""
        result = self.reduce_lamps(player_id, amount)
        if self.get_lamps(player_id) <= 1:
            self.players[player_id].reduce_draw_next_turn = 1
            self._log(f"[{self.players[player_id].name}] 下回合不能抽牌！")
        return result
    
    def reflect_reduce(self, player_id: str) -> Dict:
        """反噬：反转减灯效果"""
        # 标记本回合的减灯效果反转
        return {"success": True, "msg": "减灯效果已反转！", "reflected": True}
    
    def steal_lamp_gain(self, player_id: str) -> Dict:
        """夺光：窃取敌方加灯效果"""
        # 在结算层处理
        return {"success": True, "msg": "加灯效果转移！", "stolen": True}
    
    def cancel_and_reduce(self, player_id: str, amount: int) -> Dict:
        """暗盾：取消减灯+敌方反减"""
        opp = self.get_opponent(player_id)
        return {**self.reduce_lamps(opp.player_id, amount), "canceled": True}
    
    def cancel_and_light(self, player_id: str) -> Dict:
        """守影：取消熄灭+亮起"""
        # 在结算层处理
        return {"success": True, "msg": "熄灭无效，位置亮起！", "canceled": True}
    
    def reverse_to_extinguish(self, player_id: str) -> Dict:
        """引晦：反转亮起为熄灭"""
        return {"success": True, "msg": "亮起改为熄灭！", "reversed": True}
    
    def reduce_both_and_check_win(self, player_id: str, target_id: str, amount: int) -> Dict:
        """暗雾：双方各减，检查胜利"""
        r1 = self.reduce_lamps(player_id, amount)
        r2 = self.reduce_lamps(target_id, amount)
        result = {"success": True, "msg": f"双方各-{amount}", "both_reduced": True}
        # 灭灯者计数在回合结束时检查
        return result
    
    # ============ 位置操作接口（守夜人） ============
    def light_lowest_empty_odd(self, player_id: str) -> Dict:
        """亮起编号最低的空奇数位"""
        p = self.players[player_id]
        empty_odds = p.lamp_system.get_empty_odd_positions()
        if empty_odds:
            pos = min(empty_odds)
            p.lamp_system.light_position(pos)
            return {"success": True, "msg": f"亮起 {pos} 号位", "position": pos}
        else:
            p.lamp_system.add_lamps(1)
            return {"success": True, "msg": "奇位已满，灯数+1", "lamp_fallback": True}
    
    def light_two_odd(self, player_id: str) -> Dict:
        """亮起两个奇数位"""
        p = self.players[player_id]
        empty_odds = p.lamp_system.get_empty_odd_positions()
        lit = []
        for pos in sorted(empty_odds)[:2]:
            p.lamp_system.light_position(pos)
            lit.append(pos)
        return {"success": True, "msg": f"亮起 {lit}", "positions": lit}
    
    def light_all_empty_odd(self, player_id: str) -> Dict:
        """亮起所有空奇数位"""
        p = self.players[player_id]
        empty_odds = p.lamp_system.get_empty_odd_positions()
        for pos in empty_odds:
            p.lamp_system.light_position(pos)
        return {"success": True, "msg": f"亮起所有空奇位 {empty_odds}", "positions": empty_odds}
    
    def move_even_to_odd(self, player_id: str) -> Dict:
        """将偶位灯移到最近空奇位"""
        p = self.players[player_id]
        even_lit = p.lamp_system.get_lit_even_positions()
        empty_odds = p.lamp_system.get_empty_odd_positions()
        if even_lit and empty_odds:
            # 找最近的
            best = None
            best_dist = 999
            for e in even_lit:
                for o in empty_odds:
                    d = abs(e - o)
                    if d < best_dist:
                        best_dist = d
                        best = (e, o)
            if best:
                p.lamp_system.move_position(best[0], best[1])
                return {"success": True, "msg": f"{best[0]}→{best[1]}"}
        return {"success": False, "msg": "无可移动灯"}
    
    def light_odd_with_chain(self, player_id: str) -> Dict:
        """连灯：亮起奇位，相邻已亮则再亮"""
        p = self.players[player_id]
        empty_odds = p.lamp_system.get_empty_odd_positions()
        lit = []
        if empty_odds:
            pos = min(empty_odds)
            p.lamp_system.light_position(pos)
            lit.append(pos)
            # 检查相邻奇位
            for adj in [pos - 2, pos + 2]:
                if adj in [1, 3, 5, 7] and p.lamp_system.position_states.get(adj) == PositionState.LIT:
                    # 再亮一个
                    remaining = [o for o in empty_odds if o != pos and o not in lit]
                    if remaining:
                        p.lamp_system.light_position(min(remaining))
                        lit.append(min(remaining))
                        break
        return {"success": True, "msg": f"亮起 {lit}", "positions": lit}
    
    def extinguish_last_odd(self, player_id: str) -> Dict:
        """熄灭敌方最后亮起的奇数位"""
        opp = self.get_opponent(player_id)
        last = opp.lamp_system.get_last_lit_odd()
        if last:
            opp.lamp_system.extinguish_position(last)
            return {"success": True, "msg": f"熄灭 {last} 号位", "position": last}
        return {"success": False, "msg": "无亮起奇位"}
    
    def sacrifice_even_for_odd(self, player_id: str) -> Dict:
        """隐位：熄偶位灯，每熄一个亮一个奇位"""
        p = self.players[player_id]
        even_lit = p.lamp_system.get_lit_even_positions()
        empty_odds = p.lamp_system.get_empty_odd_positions()
        sacrificed = 0
        for pos in even_lit[:]:
            p.lamp_system.extinguish_position(pos)
            sacrificed += 1
            if empty_odds:
                p.lamp_system.light_position(empty_odds.pop(0))
        return {"success": True, "msg": f"牺牲 {sacrificed} 偶位→亮 {sacrificed} 奇位"}
    
    def swap_odd_count(self, player_id: str) -> Dict:
        """位换：交换双方奇位亮灯数量"""
        p = self.players[player_id]
        opp = self.get_opponent(player_id)
        # 记录当前
        p_odd = p.lamp_system.count_odd_lit()
        opp_odd = opp.lamp_system.count_odd_lit()
        # 复杂操作：清空后重新点亮
        for pos in [1, 3, 5, 7]:
            p.lamp_system.position_states[pos] = PositionState.EMPTY
            opp.lamp_system.position_states[pos] = PositionState.EMPTY
        # 重新点亮
        p_empty = [1, 3, 5, 7]
        for _ in range(opp_odd):
            if p_empty:
                p.lamp_system.light_position(p_empty.pop(0))
        opp_empty = [1, 3, 5, 7]
        for _ in range(p_odd):
            if opp_empty:
                opp.lamp_system.light_position(opp_empty.pop(0))
        return {"success": True, "msg": f"奇位亮灯数交换 {p_odd}↔{opp_odd}"}
    
    # ============ 组合/特殊牌接口 ============
    def copy_last_turn_effect(self, player_id: str) -> Dict:
        """引火：复制上回合效果"""
        p = self.players[player_id]
        last_card = p.last_played_card
        if last_card and last_card.effect_fn:
            # 防止复制复制牌导致无限递归
            if last_card.name in ["引火", "幻灯"]:
                return {"success": False, "msg": "无法复制复制牌本身"}
            return last_card.effect_fn(self, player_id, self.get_opponent(player_id).player_id)
        return {"success": False, "msg": "上回合无牌可复制"}
    
    def copy_opponent_last_effect(self, player_id: str) -> Dict:
        """幻灯：复制敌方上回合效果"""
        opp = self.get_opponent(player_id)
        last_card = opp.last_played_card
        if last_card and last_card.effect_fn:
            # 防止复制复制牌导致无限递归
            if last_card.name in ["引火", "幻灯"]:
                return {"success": False, "msg": "无法复制复制牌本身"}
            return last_card.effect_fn(self, player_id, self.get_opponent(player_id).player_id)
        return {"success": False, "msg": "敌方上回合无牌可复制"}
    
    def was_reduced_this_turn(self, player_id: str) -> bool:
        return self.players[player_id].was_reduced_this_turn
    
    def played_lamp_increase_last_turn(self, player_id: str) -> bool:
        return self.players[player_id].played_lamp_increase_last_turn
    
    def opponent_played_this_turn(self, player_id: str) -> bool:
        opp = self.get_opponent(player_id)
        return opp.played_this_turn
    
    # ============ 抽牌 ============
    def draw_cards(self, player_id: str, count: int) -> Dict:
        p = self.players[player_id]
        actual_count = max(0, count - p.reduce_draw_next_turn)
        drawn = p.draw(actual_count)
        result = p.add_to_hand(drawn)
        self._log(f"[{p.name}] 抽了 {len(drawn)} 张牌")
        return {"drawn": len(drawn), "cards": drawn, **result}
    
    # ============ 辅助方法 ============
    def get_opponent(self, player_id: str) -> Player:
        for pid in self.player_ids:
            if pid != player_id:
                return self.players[pid]
        return None
    
    def resolve_choice(self, player_id: str, choice_type: str) -> Dict:
        """
        需要玩家选择的牌，返回占位符
        实际选择由UI层处理后再调用具体效果
        """
        return {"success": True, "needs_choice": True, "choice_type": choice_type, "msg": "需要选择"}
    
    def apply_pending_bonus(self, player_id: str) -> Dict:
        """执行延迟收益（焰心等）"""
        p = self.players[player_id]
        if not p.pending_bonus:
            return {"success": False, "msg": "无延迟收益"}
        
        bonus = p.pending_bonus
        p.pending_bonus = None
        
        # 焰心：检查当前灯数是否≥打出时的灯数
        if bonus.get("check_lamps", False):
            current_lamps = self.get_lamps(player_id)
            required_lamps = bonus.get("required_lamps", 0)
            if current_lamps < required_lamps:
                return {"success": False, "msg": f"灯数 {current_lamps} < {required_lamps}，延迟收益未触发"}
        
        amount = bonus.get("amount", 0)
        if amount > 0:
            return self.add_lamps(player_id, amount)
        return {"success": True, "msg": "延迟收益已结算"}
    
    def lock_lamp_increase_player(self, player_id: str) -> Dict:
        """封锁玩家本回合的增灯牌（预警效果）"""
        self.players[player_id].lock_lamp_increase = True
        return {"success": True, "msg": "本回合不能打出增加灯数的牌"}
    
    def is_lamp_increase_locked(self, player_id: str) -> bool:
        """检查玩家是否被封锁增灯"""
        return self.players[player_id].lock_lamp_increase
    
    def _log(self, msg: str):
        self.logs.append(msg)
        print(f"  [LOG] {msg}")
    
    def to_dict(self) -> Dict:
        return {
            "turn": self.turn,
            "active": self.active_player_id,
            "game_over": self.game_over,
            "winner": self.winner_id,
            "players": {pid: p.to_dict() for pid, p in self.players.items()},
            "logs": self.logs[-10:],  # 最近10条
        }
