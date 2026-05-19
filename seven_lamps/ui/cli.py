"""
Seven Lamps Card Game - CLI Interface
七灯卡牌对战系统 - 命令行交互界面 (Demo版)

支持模式:
  1. 人人对战 (PVP)
  2. 人机对战 (PVE) — 玩家 vs GreedyAI
  3. AI观战 (AI vs AI) — 看AI互殴
"""
import sys
import time
from typing import Dict, Optional

from ..core.enums import ClassType
from ..core.game_state import GameState, Player
from ..core.constants import (
    INITIAL_HAND, HAND_LIMIT, BREAKOUT_TURN,
    DRAW_PHASE_1, DRAW_PHASE_2, PHASE_1_END, PHASE_2_END,
    RESPONSE_ZONE_LIMIT, INITIAL_LAMPS_FIRST, INITIAL_LAMPS_SECOND
)
from ..deck.deck_builder import quick_build_deck
from ..mechanics.win_checker import WinChecker
from ..ai.greedy_ai import GreedyAI
from ..ai.random_ai import RandomAI
from ..simulator.game_runner import AIGameRunner


class CLI:
    """命令行交互界面"""
    
    def __init__(self):
        self.game: Optional[GameState] = None
        self.ai_map: Dict[str, object] = {}  # player_id -> AI实例
    
    def print_banner(self):
        print("╔══════════════════════════════════════╗")
        print("║           七灯 (Seven Lamps)           ║")
        print("║     双人卡牌对战 — v3.0 Demo引擎      ║")
        print("╚══════════════════════════════════════╝")
        print()
    
    # ==================== 模式选择 ====================
    
    def run(self):
        """主入口"""
        self.print_banner()
        
        print("【游戏模式】")
        print("  1. 人人对战 (PVP)")
        print("  2. 人机对战 (PVE) — 你 vs AI")
        print("  3. AI观战 (AI vs AI)")
        print("  4. 退出")
        print()
        
        while True:
            mode = input("选择模式 (1/2/3/4): ").strip()
            if mode == "1":
                self._run_pvp()
                break
            elif mode == "2":
                self._run_pve()
                break
            elif mode == "3":
                self._run_ai_vs_ai()
                break
            elif mode == "4":
                print("再见！")
                break
            else:
                print("无效输入，请重试")
    
    def _run_pvp(self):
        """人人对战"""
        print("\n【人人对战】\n")
        self.setup_game()
        self._game_loop()
    
    def _run_pve(self):
        """人机对战"""
        print("\n【人机对战】\n")
        
        # 玩家选择
        print("选择你的职业:")
        print("  1. 燃灯者 — 灯数=7获胜")
        print("  2. 灭灯者 — 敌方连续2回合≤2获胜")
        print()
        
        human_class = self._choose_class("你")
        human_preset = self._choose_preset(human_class, "你")
        
        print("\n选择AI职业:")
        ai_class = self._choose_class("AI")
        ai_preset = self._choose_preset(ai_class, "AI")
        
        # 选择先后手
        print("\n选择先后手:")
        print("  1. 你先手")
        print("  2. AI先手")
        while True:
            c = input("选择 (1/2): ").strip()
            if c == "1":
                p1_config = {"id": "p1", "name": "玩家", "class": human_class, "preset": human_preset}
                p2_config = {"id": "p2", "name": "AI", "class": ai_class, "preset": ai_preset}
                self.ai_map = {"p2": GreedyAI("AI")}
                break
            elif c == "2":
                p1_config = {"id": "p1", "name": "AI", "class": ai_class, "preset": ai_preset}
                p2_config = {"id": "p2", "name": "玩家", "class": human_class, "preset": human_preset}
                self.ai_map = {"p1": GreedyAI("AI")}
                break
            print("无效输入")
        
        self._setup_game_from_configs([p1_config, p2_config])
        self._game_loop()
    
    def _run_ai_vs_ai(self):
        """AI观战模式"""
        print("\n【AI观战模式】\n")
        
        print("选择AI1职业:")
        c1 = self._choose_class("AI1")
        p1 = self._choose_preset(c1, "AI1")
        
        print("\n选择AI2职业:")
        c2 = self._choose_class("AI2")
        p2 = self._choose_preset(c2, "AI2")
        
        print("\n选择AI类型:")
        print("  1. GreedyAI (贪心策略)")
        print("  2. RandomAI (随机策略)")
        ai_type = "greedy"
        while True:
            c = input("选择 (1/2): ").strip()
            if c == "1":
                ai_type = "greedy"
                break
            elif c == "2":
                ai_type = "random"
                break
            print("无效输入")
        
        # 使用 AIGameRunner
        if ai_type == "greedy":
            ai1 = GreedyAI("AI1")
            ai2 = GreedyAI("AI2")
        else:
            ai1 = RandomAI()
            ai2 = RandomAI()
        
        runner = AIGameRunner(ai1, ai2, verbose=True)
        runner.setup(
            {"name": "AI1", "class": c1, "preset": p1},
            {"name": "AI2", "class": c2, "preset": p2}
        )
        
        print("\n" + "="*50)
        print("开始对局...")
        print("="*50)
        
        result = runner.run()
        
        print("\n" + "="*50)
        if result["game_over"]:
            print(f"🏆 获胜者: {result['winner_name']} ({result['winner_class']})")
        else:
            print("⏱ 回合上限，平局！")
        print(f"总回合数: {result['turns']}")
        print(f"最终灯数: AI1={result['p1_lamps']}, AI2={result['p2_lamps']}")
        print("="*50)
    
    # ==================== 游戏设置 ====================
    
    def setup_game(self) -> GameState:
        """设置新游戏 (PVP)"""
        print("【选择职业】")
        print("1. 燃灯者 — 灯数=7获胜（积累/组合）")
        print("2. 守夜人 — 奇位全亮获胜（位置/操控）")
        print("3. 灭灯者 — 敌方连续2回合≤2获胜（压制）")
        print()
        
        p1_class = self._choose_class("玩家1")
        p1_preset = self._choose_preset(p1_class, "玩家1")
        p2_class = self._choose_class("玩家2")
        p2_preset = self._choose_preset(p2_class, "玩家2")
        
        configs = [
            {"id": "p1", "name": "玩家1", "class": p1_class, "preset": p1_preset},
            {"id": "p2", "name": "玩家2", "class": p2_class, "preset": p2_preset},
        ]
        return self._setup_game_from_configs(configs)
    
    def _setup_game_from_configs(self, configs):
        """从配置创建游戏"""
        game = GameState([{"id": c["id"], "name": c["name"], "class": c["class"]} for c in configs])
        
        for c in configs:
            pid = c["id"]
            deck = quick_build_deck(c["class"], c.get("preset"))
            game.players[pid].deck = deck[:]
            game.players[pid].shuffle_deck()
        
        for pid in game.player_ids:
            drawn = game.players[pid].draw(INITIAL_HAND)
            game.players[pid].add_to_hand(drawn)
        
        game.active_player_id = game.first_player
        game.turn = 1
        
        self.game = game
        return game
    
    def _choose_class(self, label: str) -> ClassType:
        while True:
            c = input(f"{label} 选择职业 (1/2/3): ").strip()
            if c == "1":
                return ClassType.LAMPLIGHTER
            elif c == "2":
                return ClassType.NIGHTWATCH
            elif c == "3":
                return ClassType.EXTINGUISHER
            print("无效输入，请重试")
    
    def _choose_preset(self, class_type: ClassType, label: str) -> Optional[str]:
        from ..deck.deck_builder import DeckBuilder
        builder = DeckBuilder(class_type)
        presets = builder.list_presets()
        if not presets:
            return None
        print(f"\n{label} 可用卡组预设:")
        for i, name in enumerate(presets, 1):
            print(f"  {i}. {name}")
        print(f"  r. 随机组牌")
        while True:
            c = input(f"选择卡组 (1-{len(presets)}/r): ").strip().lower()
            if c == "r":
                return None
            try:
                idx = int(c) - 1
                if 0 <= idx < len(presets):
                    return presets[idx]
            except:
                pass
            print("无效输入，请重试")
    
    # ==================== 游戏循环 ====================
    
    def _game_loop(self):
        """主游戏循环"""
        print(f"\n✅ 游戏设置完成！")
        p1 = self.game.players["p1"]
        p2 = self.game.players["p2"]
        print(f"   {p1.name} [{p1.class_type.value}] vs {p2.name} [{p2.class_type.value}]")
        fp = self.game.players[self.game.first_player]
        sp = self.game.players[self.game.get_opponent(self.game.first_player).player_id]
        print(f"   先手：{fp.name}（{INITIAL_LAMPS_FIRST}盏）  后手：{sp.name}（{INITIAL_LAMPS_SECOND}盏）")
        print()
        
        while not self.game.game_over and self.game.turn <= 20:
            self.run_turn()
            if self.game.game_over:
                break
        
        if not self.game.game_over:
            print(f"\n⏱ 回合上限 reached，平局！")
        else:
            winner = self.game.players[self.game.winner_id]
            print(f"\n🏆 游戏结束！获胜者: {winner.name} ({winner.class_type.value})")
        
        print(f"\n游戏日志:")
        for log in self.game.logs:
            print(f"  {log}")
    
    def print_state(self):
        """打印当前游戏状态"""
        g = self.game
        print(f"\n{'='*50}")
        print(f"【第 {g.turn} 回合】 当前玩家: {g.players[g.active_player_id].name}")
        print(f"{'='*50}")
        
        for pid in g.player_ids:
            p = g.players[pid]
            is_active = "▶ " if pid == g.active_player_id else "  "
            print(f"\n{is_active}[{p.name}] {p.class_type.value}")
            
            if p.class_type == ClassType.NIGHTWATCH:
                positions = []
                for i in range(1, 8):
                    s = p.lamp_system.position_states[i]
                    ch = "●" if s.name == "LIT" else "○"
                    positions.append(f"{ch}{i}")
                print(f"   位置: {' '.join(positions)}")
                print(f"   灯数: {p.lamp_system.get_lamp_count()} (奇位亮: {p.lamp_system.count_odd_lit()})")
            else:
                print(f"   灯数: {p.lamp_system.get_lamp_count()}")
            
            rz = p.response_zone.get_public_info()
            print(f"   响应区: {rz['count']} 张奥秘")
            
            if pid == g.active_player_id:
                print(f"   手牌 ({len(p.hand)} 张):")
                for i, card in enumerate(p.hand, 1):
                    playable = "✓" if card.check_playable(g, pid) else "✗"
                    print(f"     {i}. [{playable}] {card.name} ({card.threshold_desc}) — {card.effect_desc}")
            else:
                print(f"   手牌: {len(p.hand)} 张")
        
        print(f"\n{'='*50}")
    
    def get_draw_count(self, player_id: str) -> int:
        turn = self.game.turn
        if turn <= PHASE_1_END:
            return DRAW_PHASE_1
        else:
            return DRAW_PHASE_2
    
    def get_play_limit(self, player_id: str) -> int:
        turn = self.game.turn
        p = self.game.players[player_id]
        if p.next_turn_card_limit is not None:
            limit = p.next_turn_card_limit
            p.next_turn_card_limit = None
            return limit
        if turn >= BREAKOUT_TURN:
            return 2
        return 1
    
    def run_turn(self):
        """执行一个完整回合"""
        g = self.game
        pid = g.active_player_id
        p = g.players[pid]
        is_ai = pid in self.ai_map
        
        print(f"\n{'━'*50}")
        print(f"【{p.name} 的第 {g.turn} 回合】")
        if is_ai:
            print(f"   (AI思考中...)")
            time.sleep(0.3)
        
        # 1. 回合开始处理
        p.reset_turn_flags()
        
        if p.next_turn_reduce > 0:
            opp = g.get_opponent(pid)
            g.reduce_lamps(opp.player_id, p.next_turn_reduce)
            p.next_turn_reduce = 0
        
        # 2. 抽牌
        draw_count = self.get_draw_count(pid)
        print(f"→ 抽牌阶段：抽 {draw_count} 张")
        result = g.draw_cards(pid, draw_count)
        if result.get("excess", 0) > 0:
            print(f"⚠ 手牌上限 {HAND_LIMIT}，需弃 {result['excess']} 张")
            if is_ai:
                ai = self.ai_map[pid]
                discard_indices = ai.choose_discard(g, pid, result["excess"])
                for idx in sorted(discard_indices, reverse=True):
                    if 0 <= idx < len(p.hand):
                        card = p.hand[idx]
                        p.discard_from_hand(card)
                        print(f"   AI弃掉了 [{card.name}]")
            else:
                self._discard_excess(pid, result["excess"])
        
        # 3. 出牌阶段
        play_limit = self.get_play_limit(pid)
        plays = 0
        
        while plays < play_limit and p.hand:
            self.print_state()
            
            if is_ai:
                action = self._ai_action(pid)
            else:
                action = self._human_action(pid)
            
            if action is None or action["action"] == "skip":
                print(f"→ {p.name} 跳过出牌")
                self._check_response_triggers(pid, "跳过出牌")
                break
            
            elif action["action"] == "response":
                idx = action["card_index"]
                if 0 <= idx < len(p.hand):
                    card = p.hand[idx]
                    if card.card_type.value == "响应牌":
                        p.hand.remove(card)
                        if p.response_zone.is_full():
                            rep_idx = 0
                            if is_ai:
                                rep_idx = self.ai_map[pid].choose_response_replace(g, pid)
                            result = p.response_zone.replace_card(card, rep_idx)
                            if result["success"]:
                                p.discard.append(result["replaced"])
                                print(f"✓ {result['msg']}")
                        else:
                            result = p.response_zone.add_card(card)
                            print(f"✓ {result['msg']}")
                plays += 1
                continue
            
            elif action["action"] == "play":
                idx = action["card_index"]
                if 0 <= idx < len(p.hand):
                    card = p.hand[idx]
                    if not card.check_playable(g, pid):
                        if is_ai:
                            continue
                        print(f"✗ 不满足门槛: {card.threshold_desc}")
                        continue
                    
                    p.play_card(card)
                    print(f"→ 打出 [{card.name}] — {card.effect_desc}")
                    
                    opp = g.get_opponent(pid)
                    self._check_response_triggers(opp.player_id, f"敌方打出{card.card_type.value}", card)
                    
                    target_id = opp.player_id
                    effect_result = card.execute(g, pid, target_id)
                    print(f"   效果: {effect_result.get('msg', '')}")
                    
                    win = g.win_checker.check_victory(g, pid)
                    if win["won"]:
                        print(f"\n🏆 {win['reason']}")
                        g.game_over = True
                        g.winner_id = pid
                        return
                    
                    p.discard.append(card)
                    plays += 1
        
        # 4. 回合结束
        print(f"→ 回合结束")
        
        for other_pid in g.player_ids:
            if g.players[other_pid].class_type == ClassType.EXTINGUISHER:
                g.win_checker.update_extinguisher_counter(g, other_pid)
                ex_win = g.win_checker.check_victory(g, other_pid)
                if ex_win["won"]:
                    print(f"\n🏆 {ex_win['reason']}")
                    g.game_over = True
                    g.winner_id = other_pid
                    return
        
        if len(p.hand) > HAND_LIMIT:
            excess = len(p.hand) - HAND_LIMIT
            print(f"⚠ 回合结束手牌超出上限，需弃 {excess} 张")
            if is_ai:
                ai = self.ai_map[pid]
                discard_indices = ai.choose_discard(g, pid, excess)
                for idx in sorted(discard_indices, reverse=True):
                    if 0 <= idx < len(p.hand):
                        card = p.hand[idx]
                        p.discard_from_hand(card)
            else:
                self._discard_excess(pid, excess)
        
        if g.turn == BREAKOUT_TURN:
            winner = g.win_checker.resolve_winner(g)
            if winner is None:
                print(f"\n⚡ 第7回合结束未分胜负，疲劳触发！")
                fatigue = g.win_checker.apply_fatigue(g)
                for ch in fatigue["changes"]:
                    print(f"   {ch['msg']}")
        
        g.active_player_id = g.get_opponent(pid).player_id
        g.turn += 1
    
    def _human_action(self, pid: str) -> Optional[Dict]:
        """获取人类玩家动作"""
        p = self.game.players[pid]
        action = input(f"\n[{p.name}] 行动 (数字=出牌 / r=响应牌 / s=跳过 / q=退出): ").strip().lower()
        
        if action == "q":
            print("游戏退出")
            sys.exit(0)
        
        if action == "s" or action == "":
            return {"action": "skip"}
        
        if action == "r":
            resp_cards = [(i, c) for i, c in enumerate(p.hand) if c.card_type.value == "响应牌"]
            if not resp_cards:
                print("手中没有响应牌")
                return None
            print("可放入响应区的牌：")
            for idx, (i, c) in enumerate(resp_cards, 1):
                print(f"  {idx}. [{i+1}] {c.name} — {c.trigger_desc}")
            try:
                choice = int(input("选择奥秘编号: ")) - 1
                if 0 <= choice < len(resp_cards):
                    real_idx, _ = resp_cards[choice]
                    return {"action": "response", "card_index": real_idx}
            except (ValueError, IndexError):
                pass
            print("无效选择")
            return None
        
        try:
            card_idx = int(action) - 1
            if 0 <= card_idx < len(p.hand):
                return {"action": "play", "card_index": card_idx}
            print("无效手牌编号")
        except ValueError:
            print("无效输入")
        return None
    
    def _ai_action(self, pid: str) -> Dict:
        """获取AI动作"""
        ai = self.ai_map[pid]
        return ai.choose_action(self.game, pid)
    
    def _check_response_triggers(self, player_id: str, action_desc: str, action_card=None):
        """检查响应牌触发"""
        g = self.game
        p = g.players[player_id]
        
        triggers = p.response_zone.check_triggers(g, player_id, action_desc, action_card)
        if not triggers:
            return
        
        print(f"\n💥 奥秘触发！")
        for t in triggers:
            card = t["card"]
            print(f"   揭示 [{card.name}]！{card.effect_desc}")
            
            opp = g.get_opponent(player_id)
            result = card.execute(g, player_id, opp.player_id)
            print(f"   → {result.get('msg', '')}")
            
            p.response_zone.remove_card(t["index"])
            p.discard.append(card)
            
            win = g.win_checker.check_victory(g, player_id)
            if win["won"]:
                print(f"\n🏆 {win['reason']}")
                g.game_over = True
                g.winner_id = player_id
                return
    
    def _discard_excess(self, player_id: str, count: int):
        """让玩家弃掉多余手牌"""
        g = self.game
        p = g.players[player_id]
        
        for _ in range(count):
            if not p.hand:
                break
            print(f"\n需弃 {count} 张，当前手牌:")
            for i, c in enumerate(p.hand, 1):
                print(f"  {i}. {c.name}")
            try:
                idx = int(input("选择要弃的牌: ")) - 1
                if 0 <= idx < len(p.hand):
                    card = p.hand[idx]
                    p.discard_from_hand(card)
                    print(f"弃掉了 [{card.name}]")
                else:
                    card = p.hand[0]
                    p.discard_from_hand(card)
            except (ValueError, IndexError):
                card = p.hand[0]
                p.discard_from_hand(card)
