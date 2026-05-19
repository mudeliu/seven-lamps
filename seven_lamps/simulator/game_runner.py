"""
Seven Lamps Card Game - Automated Game Runner
七灯卡牌对战系统 - 自动化对战引擎（AI vs AI）
"""
from typing import Dict, List, Optional, Tuple
from ..core.enums import ClassType
from ..core.game_state import GameState
from ..core.constants import (
    INITIAL_HAND, HAND_LIMIT, BREAKOUT_TURN,
    DRAW_PHASE_1, DRAW_PHASE_2, PHASE_1_END, PHASE_2_END
)
from ..deck.deck_builder import quick_build_deck


class AIGameRunner:
    """
    AI对战引擎
    
    替代CLI的人类输入，用AI策略自动运行完整对局
    """
    
    def __init__(self, ai1, ai2, verbose: bool = False):
        """
        ai1, ai2: BaseAI 实例
        verbose: 是否打印对局过程
        """
        self.ai_map = {"p1": ai1, "p2": ai2}
        self.verbose = verbose
        self.game: Optional[GameState] = None
        self.history: List[Dict] = []  # 对局历史
    
    def setup(self, p1_config: Dict, p2_config: Dict) -> GameState:
        """
        设置游戏
        p1_config: {"name": str, "class": ClassType, "preset": str or None}
        """
        configs = [
            {"id": "p1", "name": p1_config["name"], "class": p1_config["class"]},
            {"id": "p2", "name": p2_config["name"], "class": p2_config["class"]},
        ]
        game = GameState(configs)
        
        # 组牌
        p1_deck = quick_build_deck(p1_config["class"], p1_config.get("preset"))
        p2_deck = quick_build_deck(p2_config["class"], p2_config.get("preset"))
        
        game.players["p1"].deck = p1_deck[:]
        game.players["p1"].shuffle_deck()
        game.players["p2"].deck = p2_deck[:]
        game.players["p2"].shuffle_deck()
        
        # 起始手牌
        for pid in game.player_ids:
            drawn = game.players[pid].draw(INITIAL_HAND)
            game.players[pid].add_to_hand(drawn)
        
        game.active_player_id = game.first_player
        game.turn = 1
        
        self.game = game
        return game
    
    def run(self, max_turns: int = 20) -> Dict:
        """
        运行完整对局
        返回结果字典
        """
        g = self.game
        
        while not g.game_over and g.turn <= max_turns:
            self._run_turn()
        
        return self._make_result()
    
    def _run_turn(self):
        """执行一个回合"""
        g = self.game
        pid = g.active_player_id
        p = g.players[pid]
        ai = self.ai_map[pid]
        
        if self.verbose:
            print(f"\n--- Turn {g.turn} | {p.name} ({p.class_type.value}) ---")
            print(f"  Lamps: {g.get_lamps('p1')} vs {g.get_lamps('p2')}")
        
        # 1. 回合开始处理
        p.reset_turn_flags()
        
        # 处理上回合遗留效果（余波DOT等）
        if p.next_turn_reduce > 0:
            opp = g.get_opponent(pid)
            g.reduce_lamps(opp.player_id, p.next_turn_reduce)
            p.next_turn_reduce = 0
        
        # 2. 抽牌
        draw_count = self._get_draw_count(pid)
        result = g.draw_cards(pid, draw_count)
        if result.get("excess", 0) > 0:
            discard_indices = ai.choose_discard(g, pid, result["excess"])
            for idx in sorted(discard_indices, reverse=True):
                if 0 <= idx < len(p.hand):
                    card = p.hand[idx]
                    p.discard_from_hand(card)
        
        # 3. 出牌阶段
        play_limit = self._get_play_limit(pid)
        plays = 0
        
        while plays < play_limit and p.hand and not g.game_over:
            action = ai.choose_action(g, pid)
            
            if action["action"] == "skip":
                if self.verbose:
                    print(f"  {p.name} skips")
                self._check_response_triggers(pid, "跳过出牌")
                break
            
            elif action["action"] == "response":
                # 放入响应牌
                idx = action["card_index"]
                if 0 <= idx < len(p.hand):
                    card = p.hand[idx]
                    if card.card_type.value == "响应牌":
                        p.hand.remove(card)
                        if p.response_zone.is_full():
                            rep_idx = ai.choose_response_replace(g, pid)
                            result = p.response_zone.replace_card(card, rep_idx)
                            if result["success"]:
                                p.discard.append(result["replaced"])
                        else:
                            p.response_zone.add_card(card)
                        if self.verbose:
                            print(f"  {p.name} plays response [{card.name}]")
                        plays += 1
            
            elif action["action"] == "play":
                idx = action["card_index"]
                if 0 <= idx < len(p.hand):
                    card = p.hand[idx]
                    if not card.check_playable(g, pid):
                        continue
                    
                    p.play_card(card)
                    if self.verbose:
                        print(f"  {p.name} plays [{card.name}] -> {card.effect_desc}")
                    
                    # 检查敌方响应区触发
                    opp = g.get_opponent(pid)
                    self._check_response_triggers(opp.player_id, f"敌方打出{card.card_type.value}", card)
                    
                    # 执行效果
                    target_id = opp.player_id
                    effect_result = card.execute(g, pid, target_id)
                    
                    if self.verbose and effect_result.get("msg"):
                        print(f"    Effect: {effect_result.get('msg')}")
                    
                    # 检查胜利
                    win = g.win_checker.check_victory(g, pid)
                    if win["won"]:
                        g.game_over = True
                        g.winner_id = pid
                        if self.verbose:
                            print(f"\n  >>> {win['reason']}")
                        return
                    
                    p.discard.append(card)
                    plays += 1
        
        # 4. 回合结束
        if g.game_over:
            return
        
        # 灭灯者计数更新
        for other_pid in g.player_ids:
            if g.players[other_pid].class_type == ClassType.EXTINGUISHER:
                g.win_checker.update_extinguisher_counter(g, other_pid)
                ex_win = g.win_checker.check_victory(g, other_pid)
                if ex_win["won"]:
                    g.game_over = True
                    g.winner_id = other_pid
                    if self.verbose:
                        print(f"\n  >>> {ex_win['reason']}")
                    return
        
        # 手牌上限
        if len(p.hand) > HAND_LIMIT:
            excess = len(p.hand) - HAND_LIMIT
            discard_indices = ai.choose_discard(g, pid, excess)
            for idx in sorted(discard_indices, reverse=True):
                if 0 <= idx < len(p.hand):
                    card = p.hand[idx]
                    p.discard_from_hand(card)
        
        # 疲劳
        if g.turn == BREAKOUT_TURN:
            winner = g.win_checker.resolve_winner(g)
            if winner is None:
                g.win_checker.apply_fatigue(g)
                if self.verbose:
                    print(f"  Fatigue applied!")
        
        # 切换
        g.active_player_id = g.get_opponent(pid).player_id
        g.turn += 1
    
    def _check_response_triggers(self, player_id: str, action_desc: str, action_card=None):
        """检查响应牌触发"""
        g = self.game
        p = g.players[player_id]
        triggers = p.response_zone.check_triggers(g, player_id, action_desc, action_card)
        
        for t in triggers:
            card = t["card"]
            if self.verbose:
                print(f"    Response triggered: [{card.name}]!")
            opp = g.get_opponent(player_id)
            result = card.execute(g, player_id, opp.player_id)
            if self.verbose and result.get("msg"):
                print(f"      -> {result.get('msg')}")
            p.response_zone.remove_card(t["index"])
            p.discard.append(card)
            
            # 响应后检查胜利
            win = g.win_checker.check_victory(g, player_id)
            if win["won"]:
                g.game_over = True
                g.winner_id = player_id
                return
    
    def _get_draw_count(self, player_id: str) -> int:
        turn = self.game.turn
        p = self.game.players[player_id]
        base = DRAW_PHASE_1 if turn <= PHASE_1_END else DRAW_PHASE_2
        actual = max(0, base - p.reduce_draw_next_turn)
        p.reduce_draw_next_turn = 0
        return actual
    
    def _get_play_limit(self, player_id: str) -> int:
        turn = self.game.turn
        p = self.game.players[player_id]
        if p.next_turn_card_limit is not None:
            limit = p.next_turn_card_limit
            p.next_turn_card_limit = None
            return limit
        return 2 if turn >= BREAKOUT_TURN else 1
    
    def _make_result(self) -> Dict:
        g = self.game
        result = {
            "game_over": g.game_over,
            "turns": g.turn - 1,
            "winner_id": g.winner_id,
            "winner_name": None,
            "winner_class": None,
            "p1_class": g.players["p1"].class_type.value,
            "p2_class": g.players["p2"].class_type.value,
            "p1_lamps": g.get_lamps("p1"),
            "p2_lamps": g.get_lamps("p2"),
            "logs": g.logs,
        }
        if g.winner_id:
            w = g.players[g.winner_id]
            result["winner_name"] = w.name
            result["winner_class"] = w.class_type.value
        return result
