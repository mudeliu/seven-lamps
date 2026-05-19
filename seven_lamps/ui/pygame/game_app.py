"""
Seven Lamps - Pygame Game Application
七灯 pygame 主应用

游戏循环、场景管理、事件处理
"""
import sys
import time
import pygame
from typing import Optional, Dict, List, Tuple

from .assets import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, Colors, Layout, CARD_WIDTH, CARD_HEIGHT, CARD_MARGIN
from .renderer import Renderer
from .animator import Animator
from .audio import AudioManager
from ...core.enums import ClassType, CardType
from ...core.game_state import GameState
from ...core.constants import INITIAL_HAND, HAND_LIMIT, BREAKOUT_TURN, DRAW_PHASE_1, DRAW_PHASE_2, PHASE_1_END
from ...deck.deck_builder import quick_build_deck
from ...ai.greedy_ai import GreedyAI
from ...ai.random_ai import RandomAI


class GameApp:
    """pygame 游戏应用主类"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("七灯 (Seven Lamps) - v0.5 Pygame")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.animator = Animator()
        self.audio = AudioManager(enabled=True, master_volume=0.35)
        self.running = True
        
        # 游戏状态
        self.game: Optional[GameState] = None
        self.ai_map: Dict[str, object] = {}
        
        # 交互状态
        self.selected_card_idx: Optional[int] = None
        self.hover_card_idx: Optional[int] = None
        self.message = ""
        self.message_timer = 0
        
        # 响应牌交互状态
        self.response_mode: Optional[str] = None  # None / "selecting_replace"
        self.response_button_hovered = False
        self.replace_hover_idx: Optional[int] = None
        
        # 选择弹窗状态（明灭等需要选择的牌）
        self.choice_mode: bool = False
        self.choice_options: List[str] = []
        self.choice_selected: int = 0
        self.choice_callback = None  # 选择后的回调函数
        self.choice_title: str = ""
        
        # 行动历史记录
        self.action_history: List[Dict] = []
        
        # 场景
        self.scene = "menu"  # menu / game / gameover
        self.menu_selected = 0
        self.menu_options = [
            "人机对战 (PVP)",
            "PVE推关模式",
            "AI观战 (AI vs AI)",
            "退出"
        ]
        
        # PVE状态
        self.pve_game = None
        self.pve_level = 1
        self.pve_max_level = 5
        self.pve_relic = None
        self.pve_scene = "relic_select"  # relic_select / battle / reward / victory / defeat
        self.pve_reward_cards = []
        self.pve_reward_selected = 0
        self.pve_relic_selected = 0
    
    def run(self):
        """主循环"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            if self.scene == "menu":
                self._handle_menu_events()
                self._draw_menu()
            elif self.scene == "game":
                self._handle_game_events()
                self._update_game(dt)
                self._draw_game()
            elif self.scene == "pve":
                self._handle_pve_events()
                self._update_pve(dt)
                self._draw_pve()
            elif self.scene == "gameover":
                self._handle_gameover_events()
                self._draw_gameover()
            
            pygame.display.flip()
        
        pygame.quit()
    
    # ============ 菜单场景 ============
    
    def _handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
                elif event.key == pygame.K_DOWN:
                    self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
                elif event.key == pygame.K_RETURN:
                    self._select_menu()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._check_menu_click()
    
    def _check_menu_click(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for i in range(len(self.menu_options)):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 300 + i * 60, 300, 50)
            if rect.collidepoint(mouse_x, mouse_y):
                self.menu_selected = i
                self._select_menu()
    
    def _select_menu(self):
        if self.menu_selected == 0:
            self._start_pvp()
        elif self.menu_selected == 1:
            self._start_pve()
        elif self.menu_selected == 2:
            self._start_ai_vs_ai()
        elif self.menu_selected == 3:
            self.running = False
    
    def _draw_menu(self):
        self.renderer.clear()
        
        # 标题
        title = self.renderer.font_xl.render("七灯 (Seven Lamps)", True, Colors.TEXT_HIGHLIGHT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)
        
        subtitle = self.renderer.font_medium.render("数值驱动TCG - v0.5 Pygame可视化", True, Colors.TEXT_DIM)
        sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 240))
        self.screen.blit(subtitle, sub_rect)
        
        # 选项
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for i, option in enumerate(self.menu_options):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 300 + i * 70, 300, 55)
            is_hovered = rect.collidepoint(mouse_x, mouse_y)
            is_selected = (i == self.menu_selected)
            
            color = Colors.BUTTON_HOVER if (is_hovered or is_selected) else Colors.BUTTON
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, Colors.BORDER_ACTIVE if is_selected else Colors.BORDER, 
                           rect, 2, border_radius=8)
            
            text = self.renderer.font_large.render(option, True, Colors.TEXT)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)
        
        # 操作提示
        hint = self.renderer.font_small.render("↑↓选择 / Enter确认 / 鼠标点击", True, Colors.TEXT_DIM)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 50))
    
    # ============ 游戏初始化 ============
    
    def _start_pvp(self):
        """开始人机对战（PVP）"""
        configs = [
            {"id": "p1", "name": "玩家", "class": ClassType.LAMPLIGHTER},
            {"id": "p2", "name": "AI", "class": ClassType.EXTINGUISHER},
        ]
        self._setup_game(configs)
        self.ai_map = {"p2": GreedyAI("AI")}
        self.scene = "game"
        self._set_message("游戏开始！你是燃灯者，目标是灯数达到7。AI是灭灯者。")
    
    def _start_pve(self):
        """开始PVE推关模式"""
        self.pve_level = 1
        self.pve_relic = None
        self.pve_scene = "relic_select"
        self.pve_relic_selected = 0
        self.scene = "pve"
        self._set_message("PVE模式：先选择遗物，然后挑战5关！")
    
    def _start_ai_vs_ai(self):
        """开始AI观战"""
        configs = [
            {"id": "p1", "name": "AI燃灯", "class": ClassType.LAMPLIGHTER},
            {"id": "p2", "name": "AI灭灯", "class": ClassType.EXTINGUISHER},
        ]
        self._setup_game(configs)
        self.ai_map = {"p1": GreedyAI("AI燃灯"), "p2": GreedyAI("AI灭灯")}
        self.scene = "game"
        self._set_message("AI观战模式")
    
    def _setup_game(self, configs: List[Dict]):
        """初始化游戏状态"""
        game = GameState([{"id": c["id"], "name": c["name"], "class": c["class"]} for c in configs])
        
        for c in configs:
            pid = c["id"]
            deck = quick_build_deck(c["class"], None)
            game.players[pid].deck = deck[:]
            game.players[pid].shuffle_deck()
        
        for pid in game.player_ids:
            drawn = game.players[pid].draw(INITIAL_HAND)
            game.players[pid].add_to_hand(drawn)
        
        game.active_player_id = game.first_player
        game.turn = 1
        self.game = game
        self.selected_card_idx = None
    
    # ============ 游戏场景 ============
    
    def _handle_game_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.choice_mode:
                self._handle_choice_events(event)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.response_mode:
                        self.response_mode = None
                        self.selected_card_idx = None
                    else:
                        self.scene = "menu"
                elif event.key == pygame.K_SPACE:
                    self._skip_play()
                elif event.key == pygame.K_r:
                    self._try_place_response()
                elif event.key == pygame.K_RETURN and self.selected_card_idx is not None:
                    if self.response_mode == "selecting_replace":
                        pass  # 替换模式用鼠标点击槽位
                    else:
                        self._play_selected_card()
                elif event.key == pygame.K_1:
                    self._select_card_by_index(0)
                elif event.key == pygame.K_2:
                    self._select_card_by_index(1)
                elif event.key == pygame.K_3:
                    self._select_card_by_index(2)
                elif event.key == pygame.K_4:
                    self._select_card_by_index(3)
                elif event.key == pygame.K_5:
                    self._select_card_by_index(4)
                elif event.key == pygame.K_6:
                    self._select_card_by_index(5)
                elif event.key == pygame.K_7:
                    self._select_card_by_index(6)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    self._handle_mouse_click()
    
    def _select_card_by_index(self, idx: int):
        """通过数字键选择手牌"""
        if self.game is None:
            return
        active_pid = self.game.active_player_id
        if active_pid in self.ai_map:
            return
        player = self.game.players[active_pid]
        if idx < len(player.hand):
            if self.selected_card_idx == idx and self.response_mode != "selecting_replace":
                # 再次选中 = 出牌（即时牌）或尝试放入响应区（响应牌）
                card = player.hand[idx]
                if card.card_type == CardType.RESPONSE and self.response_mode is None:
                    self._try_place_response()
                else:
                    self._play_card(idx)
            else:
                self.selected_card_idx = idx
                self.response_mode = None
    
    def _handle_mouse_click(self):
        """处理鼠标点击"""
        if self.game is None:
            return
        
        active_pid = self.game.active_player_id
        if active_pid in self.ai_map:
            return  # AI回合，忽略点击
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        player = self.game.players[active_pid]
        
        # 1. 检查是否点击响应区槽位（替换模式）
        if self.response_mode == "selecting_replace":
            slot_rects = self.renderer.get_response_slot_rects(is_bottom=True)
            for i, rect in enumerate(slot_rects):
                if rect.collidepoint(mouse_x, mouse_y):
                    self._confirm_replace(i)
                    return
            # 点击空白处取消
            self.response_mode = None
            self.selected_card_idx = None
            return
        
        # 2. 检查是否点击"暗置"按钮
        if self._is_response_card_selected():
            btn_rect = self.renderer.get_response_button_rect()
            if btn_rect and btn_rect.collidepoint(mouse_x, mouse_y):
                self._try_place_response()
                return
        
        # 3. 检查是否点击手牌
        if player.hand:
            from .assets import CARD_WIDTH, CARD_MARGIN
            total_width = len(player.hand) * CARD_WIDTH + (len(player.hand) - 1) * CARD_MARGIN
            start_x = (SCREEN_WIDTH - total_width) // 2
            y = Layout.HAND_Y
            
            for i in range(len(player.hand)):
                x = start_x + i * (CARD_WIDTH + CARD_MARGIN)
                rect = pygame.Rect(x, y - 10, CARD_WIDTH, 220)
                if rect.collidepoint(mouse_x, mouse_y):
                    if self.selected_card_idx == i:
                        # 再次点击 = 出牌或放入响应区
                        card = player.hand[i]
                        if card.card_type == CardType.RESPONSE:
                            self._try_place_response()
                        else:
                            self._play_card(i)
                    else:
                        self.selected_card_idx = i
                    return
            
            # 点击手牌区域外，取消选中
            self.selected_card_idx = None
    
    def _is_response_card_selected(self) -> bool:
        """检查当前选中的牌是否是响应牌"""
        if self.selected_card_idx is None or self.game is None:
            return False
        active_pid = self.game.active_player_id
        player = self.game.players[active_pid]
        if self.selected_card_idx >= len(player.hand):
            return False
        return player.hand[self.selected_card_idx].card_type == CardType.RESPONSE
    
    def _try_place_response(self):
        """尝试将选中的响应牌放入响应区"""
        if not self._is_response_card_selected():
            return
        
        g = self.game
        pid = g.active_player_id
        p = g.players[pid]
        card = p.hand[self.selected_card_idx]
        
        if p.response_zone.is_full():
            # 进入替换选择模式
            self.response_mode = "selecting_replace"
            self._set_message("响应区已满，请点击要替换的奥秘")
            self.audio.play("error")
        else:
            # 直接放入
            p.hand.remove(card)
            result = p.response_zone.add_card(card)
            self._set_message(f"奥秘 [{card.name}] 已暗置")
            self.selected_card_idx = None
            self.audio.play("response_place")
            # 文字弹出动画
            self.animator.play_text_popup(f"奥秘 [{card.name}] 已暗置", 
                                          color=Colors.CARD_RESPONSE)
    
    def _confirm_replace(self, replace_idx: int):
        """确认替换指定位置的响应牌"""
        if self.selected_card_idx is None or self.game is None:
            return
        
        g = self.game
        pid = g.active_player_id
        p = g.players[pid]
        card = p.hand[self.selected_card_idx]
        
        if replace_idx < len(p.response_zone.cards):
            old_name = p.response_zone.cards[replace_idx].name
            p.hand.remove(card)
            result = p.response_zone.replace_card(card, replace_idx)
            if result["success"]:
                p.discard.append(result["replaced"])
                self._set_message(f"奥秘 [{card.name}] 替换 [{old_name}]")
        
        self.response_mode = None
        self.selected_card_idx = None
    
    def _handle_choice_events(self, event):
        """处理选择弹窗的事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.choice_mode = False
                self.choice_callback = None
            elif event.key == pygame.K_UP or event.key == pygame.K_LEFT:
                self.choice_selected = (self.choice_selected - 1) % len(self.choice_options)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_RIGHT:
                self.choice_selected = (self.choice_selected + 1) % len(self.choice_options)
            elif event.key == pygame.K_RETURN:
                self._confirm_choice()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                btn_rects = self.renderer.get_choice_button_rects(len(self.choice_options))
                for i, rect in enumerate(btn_rects):
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.choice_selected = i
                        self._confirm_choice()
                        break
    
    def _confirm_choice(self):
        """确认选择"""
        if self.choice_callback:
            self.choice_callback(self.choice_selected)
        self.choice_mode = False
        self.choice_callback = None
    
    def _show_choice(self, title: str, options: List[str], callback):
        """显示选择弹窗"""
        self.choice_mode = True
        self.choice_title = title
        self.choice_options = options
        self.choice_selected = 0
        self.choice_callback = callback
    
    def _play_selected_card(self):
        """打出当前选中的牌"""
        if self.selected_card_idx is not None:
            self._play_card(self.selected_card_idx)
    
    def _play_card(self, card_idx: int):
        """打出指定手牌"""
        g = self.game
        pid = g.active_player_id
        p = g.players[pid]
        
        if card_idx < 0 or card_idx >= len(p.hand):
            return
        
        card = p.hand[card_idx]
        
        # 响应牌不能直接打出，只能通过放入响应区使用
        if card.card_type == CardType.RESPONSE:
            self._set_message("响应牌请按 R 或点击'暗置'按钮放入响应区")
            self.audio.play("error")
            return
        
        if not card.check_playable(g, pid):
            self._set_message(f"不满足门槛: {card.threshold_desc}")
            self.audio.play("error")
            return
        
        # 检查是否被封锁增灯（预警效果）
        if g.is_lamp_increase_locked(pid) and any(kw in card.effect_desc for kw in ["自己+", "双方各+"]):
            self._set_message("本回合被封锁，不能打出增加灯数的牌")
            self.audio.play("error")
            return
        
        # 记录执行前的灯数
        old_lamps = {p_id: g.players[p_id].lamp_system.get_lamp_count() 
                     for p_id in g.player_ids}
        
        # 卡牌飞行动画
        start_pos = self._get_card_screen_pos(card_idx, len(p.hand))
        card_color = Colors.CARD_RESPONSE if card.card_type == CardType.RESPONSE else \
                     Colors.CARD_SPECIAL if card.card_type == CardType.SPECIAL else \
                     Colors.CARD_INSTANT
        self.animator.play_card_fly(card.name, card_color, start_pos)
        self.audio.play("play_card")
        
        p.play_card(card)
        self._set_message(f"打出 [{card.name}] — {card.effect_desc}")
        
        # 记录行动历史
        self.action_history.append({
            "turn": g.turn,
            "player_name": p.name,
            "card_name": card.name,
            "effect_desc": card.effect_desc,
            "is_enemy": pid in self.ai_map,
        })
        if len(self.action_history) > 20:
            self.action_history = self.action_history[-20:]
        
        opp = g.get_opponent(pid)
        
        # 检查响应牌触发
        self._check_response_triggers(opp.player_id, f"敌方打出{card.card_type.value}", card)
        if g.game_over:
            return
        
        # 执行效果
        target_id = opp.player_id
        effect_result = card.execute(g, pid, target_id)
        
        # 显示效果消息（特别是引火/幻灯等复制牌）
        if effect_result and effect_result.get("msg"):
            self._set_message(f"效果: {effect_result['msg']}")
        
        # 处理需要选择的牌（明灭等）
        if effect_result and effect_result.get("needs_choice"):
            choice_type = effect_result.get("choice_type", "")
            if choice_type == "ming_mie":
                self._show_choice("明灭：选择效果", ["自己+1", "敌方-1"],
                    lambda choice: self._resolve_choice_and_finish(
                        choice, "ming_mie", pid, target_id, card, old_lamps
                    ))
            else:
                # 其他选择牌默认执行第一个选项
                self._resolve_choice_and_finish(0, choice_type, pid, target_id, card, old_lamps)
            return  # 等待选择完成
        
        # 直接完成出牌流程
        self._finish_play_card(effect_result, pid, target_id, card, old_lamps)
    
    def _resolve_choice_and_finish(self, choice: int, choice_type: str, 
                                    pid: str, target_id: str, card, old_lamps: dict):
        """处理选择并完成出牌"""
        g = self.game
        
        if choice_type == "ming_mie":
            if choice == 0:
                result = g.add_lamps(pid, 1)
            else:
                result = g.reduce_lamps(target_id, 1)
            self._set_message(f"明灭效果: {result.get('msg', '')}")
            # 更新old_lamps以反映选择带来的变化
            old_lamps = {p_id: g.players[p_id].lamp_system.get_lamp_count() 
                         for p_id in g.player_ids}
        
        # 继续完成出牌
        self._finish_play_card(None, pid, target_id, card, old_lamps)
    
    def _finish_play_card(self, effect_result, pid: str, target_id: str, card, old_lamps: dict):
        """完成出牌流程（灯数动画、胜利检查、弃牌、结束回合）"""
        g = self.game
        p = g.players[pid]
        
        # 处理预警封锁效果
        if effect_result and effect_result.get("lock_lamp_increase"):
            g.lock_lamp_increase_player(target_id)
            self._set_message(f"[{g.players[target_id].name}] 本回合不能打出增加灯数的牌")
        
        # 处理焰心延迟收益
        if effect_result and effect_result.get("next_turn_bonus"):
            p.pending_bonus = {
                "check_lamps": True,
                "required_lamps": effect_result.get("old", 0),
                "amount": effect_result.get("bonus_lamps", 1)
            }
            self._set_message(f"[{p.name}] 延迟收益已记录，下回合若灯数≥{effect_result.get('old', 0)}再+{effect_result.get('bonus_lamps', 1)}")
        
        # 检查灯数变化并触发动画
        for p_id in g.player_ids:
            new_lamps = g.players[p_id].lamp_system.get_lamp_count()
            if new_lamps != old_lamps[p_id]:
                diff = abs(new_lamps - old_lamps[p_id])
                is_gain = new_lamps > old_lamps[p_id]
                pos = self._get_lamp_screen_pos(p_id)
                self.animator.play_lamp_change(diff, pos, is_gain)
                self.audio.play("lamp_up" if is_gain else "lamp_down")
        
        # 检查胜利
        from ...mechanics.win_checker import WinChecker
        win = g.win_checker.check_victory(g, pid)
        if win["won"]:
            self._set_message(f"[VICTORY] {win['reason']}")
            self.audio.play("victory")
            self.animator.play_victory((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            g.game_over = True
            g.winner_id = pid
            self.scene = "gameover"
            return
        
        p.discard.append(card)
        self.selected_card_idx = None
        
        # 如果达到出牌上限，结束回合
        play_limit = self._get_play_limit(pid)
        if p.cards_played_this_turn >= play_limit:
            self._end_turn()
    
    def _skip_play(self):
        """跳过出牌"""
        g = self.game
        pid = g.active_player_id
        
        if pid in self.ai_map:
            return
        
        self._set_message(f"{g.players[pid].name} 跳过出牌")
        self._end_turn()
    
    def _end_turn(self):
        """结束当前回合"""
        g = self.game
        pid = g.active_player_id
        p = g.players[pid]
        
        # 回合结束检查
        for other_pid in g.player_ids:
            if g.players[other_pid].class_type == ClassType.EXTINGUISHER:
                g.win_checker.update_extinguisher_counter(g, other_pid)
                ex_win = g.win_checker.check_victory(g, other_pid)
                if ex_win["won"]:
                    self._set_message(f"[VICTORY] {ex_win['reason']}")
                    self.audio.play("victory")
                    self.animator.play_victory((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                    g.game_over = True
                    g.winner_id = other_pid
                    self.scene = "gameover"
                    return
        
        # 切换玩家
        g.active_player_id = g.get_opponent(pid).player_id
        g.turn += 1
        
        # 检查回合上限
        if g.turn > 20:
            self._set_message("[TIMEOUT] 回合上限，平局！")
            g.game_over = True
            self.scene = "gameover"
            return
        
        # 新回合开始处理
        new_pid = g.active_player_id
        new_p = g.players[new_pid]
        
        # 先处理上回合的减抽效果（必须在reset_turn_flags之前）
        draw_count = DRAW_PHASE_1 if g.turn <= PHASE_1_END else DRAW_PHASE_2
        actual_draw = max(0, draw_count - new_p.reduce_draw_next_turn)
        new_p.reduce_draw_next_turn = 0
        
        new_p.reset_turn_flags()
        
        # 执行延迟收益（焰心等）
        bonus_result = g.apply_pending_bonus(new_pid)
        if bonus_result.get("success"):
            self._set_message(f"延迟收益: {bonus_result.get('msg', '')}")
            # 延迟收益动画
            if bonus_result.get("old") is not None and bonus_result.get("new") is not None:
                diff = abs(bonus_result["new"] - bonus_result["old"])
                is_gain = bonus_result["new"] > bonus_result["old"]
                pos = self._get_lamp_screen_pos(new_pid)
                self.animator.play_lamp_change(diff, pos, is_gain)
                self.audio.play("lamp_up" if is_gain else "lamp_down")
        
        # 回合开始减灯效果
        if new_p.next_turn_reduce > 0:
            opp = g.get_opponent(new_pid)
            g.reduce_lamps(opp.player_id, new_p.next_turn_reduce)
            new_p.next_turn_reduce = 0
        
        # 抽牌
        result = g.draw_cards(new_pid, actual_draw)
        
        self.selected_card_idx = None
        self.response_mode = None
        self.replace_hover_idx = None
        self._set_message(f"第 {g.turn} 回合 — {new_p.name} 的回合，抽了 {result.get('drawn', 0)} 张牌")
        
        # 抽牌音效
        if result.get("drawn", 0) > 0:
            self.audio.play("draw")
        self.audio.play("turn_start")
        
        # 决胜回合检查
        if g.turn == BREAKOUT_TURN:
            winner = g.win_checker.resolve_winner(g)
            if winner is None:
                self._set_message("[FATIGUE] 第7回合结束未分胜负，疲劳触发！双方+2灯")
                g.win_checker.apply_fatigue(g)
    
    def _get_play_limit(self, player_id: str) -> int:
        """获取当前出牌上限"""
        p = self.game.players[player_id]
        if p.next_turn_card_limit is not None:
            limit = p.next_turn_card_limit
            p.next_turn_card_limit = None
            return limit
        if self.game.turn >= BREAKOUT_TURN:
            return 2
        return 1
    
    def _update_game(self, dt: float):
        """更新游戏逻辑（主要是AI回合）"""
        # 更新动画
        self.animator.update(dt)
        
        if self.game is None or self.game.game_over:
            return
        
        pid = self.game.active_player_id
        if pid in self.ai_map:
            # AI回合
            self._run_ai_turn(pid)
    
    def _run_ai_turn(self, pid: str):
        """执行AI回合"""
        g = self.game
        p = g.players[pid]
        ai = self.ai_map[pid]
        
        # 回合开始处理
        p.reset_turn_flags()
        
        if p.next_turn_reduce > 0:
            opp = g.get_opponent(pid)
            g.reduce_lamps(opp.player_id, p.next_turn_reduce)
            p.next_turn_reduce = 0
        
        # 抽牌
        draw_count = DRAW_PHASE_1 if g.turn <= PHASE_1_END else DRAW_PHASE_2
        result = g.draw_cards(pid, draw_count)
        
        # AI思考延迟
        time.sleep(0.5)
        
        # AI行动
        play_limit = self._get_play_limit(pid)
        plays = 0
        
        while plays < play_limit and p.hand:
            action = ai.choose_action(g, pid)
            
            if action is None or action.get("action") == "skip":
                break
            
            if action["action"] == "play":
                idx = action["card_index"]
                if 0 <= idx < len(p.hand):
                    card = p.hand[idx]
                    if card.check_playable(g, pid):
                        # 记录执行前灯数（用于动画）
                        old_lamps = {p_id: g.players[p_id].lamp_system.get_lamp_count() 
                                     for p_id in g.player_ids}
                        
                        p.play_card(card)
                        self._set_message(f"AI打出 [{card.name}]")
                        
                        # 记录行动历史
                        self.action_history.append({
                            "turn": g.turn,
                            "player_name": p.name,
                            "card_name": card.name,
                            "effect_desc": card.effect_desc,
                            "is_enemy": True,
                        })
                        if len(self.action_history) > 20:
                            self.action_history = self.action_history[-20:]
                        
                        # 敌方出牌大字播报
                        from .assets import Colors as AssetColors
                        if card.card_type == CardType.RESPONSE:
                            popup_color = AssetColors.CARD_RESPONSE
                        elif card.card_type == CardType.SPECIAL:
                            popup_color = AssetColors.CARD_SPECIAL
                        else:
                            popup_color = AssetColors.CARD_INSTANT
                        self.animator.play_text_popup(
                            f"敌方打出 [{card.name}]",
                            pos=(SCREEN_WIDTH // 2, Layout.BATTLE_Y + 30),
                            color=popup_color
                        )
                        
                        opp = g.get_opponent(pid)
                        
                        # 检查响应牌触发（人类玩家的响应区）
                        self._check_response_triggers(opp.player_id, f"敌方打出{card.card_type.value}", card)
                        if g.game_over:
                            return
                        
                        effect_result = card.execute(g, pid, opp.player_id)
                        
                        # 显示AI效果消息
                        if effect_result and effect_result.get("msg"):
                            self._set_message(f"AI效果: {effect_result['msg']}")
                        
                        # AI自动处理需要选择的牌（选第一个选项）
                        if effect_result and effect_result.get("needs_choice"):
                            choice_type = effect_result.get("choice_type", "")
                            if choice_type == "ming_mie":
                                # AI优先选择自己+1
                                result = g.add_lamps(pid, 1)
                                self._set_message(f"AI明灭效果: {result.get('msg', '')}")
                            elif choice_type in ("gu_wei", "xi_wei", "huan_wei", "zhuan_wei", "yi_deng", "san_wei", "ding_zhen"):
                                # 其他选择牌AI暂时不处理（这些多为守夜人牌，AI当前职业不会遇到）
                                self._set_message(f"AI选择牌 [{card.name}] 自动跳过")
                            # 更新old_lamps以反映选择带来的变化
                            old_lamps = {p_id: g.players[p_id].lamp_system.get_lamp_count() 
                                         for p_id in g.player_ids}
                        
                        # AI出牌动画
                        start_pos = self._get_card_screen_pos(idx, len(p.hand) + 1)
                        from .assets import Colors as AssetColors
                        card_color = AssetColors.CARD_RESPONSE if card.card_type == CardType.RESPONSE else \
                                     AssetColors.CARD_SPECIAL if card.card_type == CardType.SPECIAL else \
                                     AssetColors.CARD_INSTANT
                        self.animator.play_card_fly(card.name, card_color, start_pos)
                        self.audio.play("play_card")
                        
                        # 检查灯数变化
                        for p_id in g.player_ids:
                            new_lamps = g.players[p_id].lamp_system.get_lamp_count()
                            if new_lamps != old_lamps[p_id]:
                                diff = abs(new_lamps - old_lamps[p_id])
                                is_gain = new_lamps > old_lamps[p_id]
                                pos = self._get_lamp_screen_pos(p_id)
                                self.animator.play_lamp_change(diff, pos, is_gain)
                                self.audio.play("lamp_up" if is_gain else "lamp_down")
                        
                        # 检查胜利
                        win = g.win_checker.check_victory(g, pid)
                        if win["won"]:
                            self._set_message(f"[VICTORY] {win['reason']}")
                            self.audio.play("victory")
                            self.animator.play_victory((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                            g.game_over = True
                            g.winner_id = pid
                            self.scene = "gameover"
                            return
                        
                        p.discard.append(card)
                        plays += 1
                        time.sleep(0.3)
                        break  # 简化：AI每回合只出一张
            
            elif action["action"] == "response":
                # AI放入响应牌
                idx = action["card_index"]
                if 0 <= idx < len(p.hand):
                    card = p.hand[idx]
                    if card.card_type == CardType.RESPONSE:
                        p.hand.remove(card)
                        if p.response_zone.is_full():
                            # AI简单替换第一张
                            result = p.response_zone.replace_card(card, 0)
                            if result["success"]:
                                p.discard.append(result["replaced"])
                                self._set_message(f"AI替换奥秘 [{card.name}]")
                        else:
                            result = p.response_zone.add_card(card)
                            self._set_message(f"AI暗置奥秘 [{card.name}]")
                        self.audio.play("response_place")
                        plays += 1
                        time.sleep(0.3)
                        break
            
            else:
                break
        
        # AI回合结束
        self._end_turn()
    
    def _draw_game(self):
        """绘制游戏画面"""
        # 更新悬停状态
        self._update_hover()
        
        self.renderer.draw_game(
            self.game,
            selected_card_idx=self.selected_card_idx,
            hover_card_idx=self.hover_card_idx,
            message=self.message,
            show_response_button=self._is_response_card_selected(),
            response_button_hovered=self.response_button_hovered,
            response_mode=self.response_mode,
            replace_hover_idx=self.replace_hover_idx,
            action_history=self.action_history
        )
        
        # 绘制选中卡牌详情面板
        if self.selected_card_idx is not None and self.game is not None:
            active_pid = self.game.active_player_id
            player = self.game.players.get(active_pid)
            if player and self.selected_card_idx < len(player.hand):
                card = player.hand[self.selected_card_idx]
                self.renderer.draw_card_detail(card)
        
        # 绘制动画层（在UI之上）
        self.animator.draw(self.screen)
        
        # 绘制选择弹窗（最上层）
        if self.choice_mode:
            self.renderer.draw_choice_popup(
                self.choice_title, self.choice_options, self.choice_selected
            )
        
        # 绘制操作提示
        if self.choice_mode:
            hint_text = "选择模式: ↑↓切换 | Enter确认 | ESC取消"
        else:
            hint_text = "点击出牌 | R暗置奥秘 | Enter确认 | 空格跳过 | ESC菜单 | M静音"
        hint = self.renderer.font_small.render(hint_text, True, Colors.TEXT_DIM)
        self.screen.blit(hint, (20, SCREEN_HEIGHT - 25))
    
    def _update_hover(self):
        """更新鼠标悬停状态"""
        self.hover_card_idx = None
        self.response_button_hovered = False
        self.replace_hover_idx = None
        
        # 选择模式：检查按钮悬停
        if self.choice_mode:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            btn_rects = self.renderer.get_choice_button_rects(len(self.choice_options))
            for i, rect in enumerate(btn_rects):
                if rect.collidepoint(mouse_x, mouse_y):
                    self.choice_selected = i
                    return
            return
        
        if self.game is None:
            return
        
        active_pid = self.game.active_player_id
        if active_pid in self.ai_map:
            return
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # 1. 检查响应区槽位悬停（替换模式）
        if self.response_mode == "selecting_replace":
            slot_rects = self.renderer.get_response_slot_rects(is_bottom=True)
            for i, rect in enumerate(slot_rects):
                if rect.collidepoint(mouse_x, mouse_y):
                    self.replace_hover_idx = i
                    return
            return
        
        # 2. 检查"暗置"按钮悬停
        if self._is_response_card_selected():
            btn_rect = self.renderer.get_response_button_rect()
            if btn_rect and btn_rect.collidepoint(mouse_x, mouse_y):
                self.response_button_hovered = True
                return
        
        # 3. 检查手牌悬停
        player = self.game.players[active_pid]
        if not player.hand:
            return
        
        from .assets import CARD_WIDTH, CARD_MARGIN
        total_width = len(player.hand) * CARD_WIDTH + (len(player.hand) - 1) * CARD_MARGIN
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = Layout.HAND_Y
        
        for i in range(len(player.hand)):
            x = start_x + i * (CARD_WIDTH + CARD_MARGIN)
            rect = pygame.Rect(x, y - 10, CARD_WIDTH, 220)
            if rect.collidepoint(mouse_x, mouse_y):
                self.hover_card_idx = i
                break
    
    def _check_response_triggers(self, player_id: str, action_desc: str, action_card=None):
        """检查响应牌触发"""
        g = self.game
        p = g.players[player_id]
        
        triggers = p.response_zone.check_triggers(g, player_id, action_desc, action_card)
        if not triggers:
            return
        
        # 记录执行前的灯数
        old_lamps = {p_id: g.players[p_id].lamp_system.get_lamp_count() 
                     for p_id in g.player_ids}
        
        for t in triggers:
            card = t["card"]
            self._set_message(f"奥秘 [{card.name}] 触发！{card.effect_desc}")
            self.audio.play("mystery")
            
            # 奥秘触发动画
            pos = self._get_response_zone_pos(player_id)
            self.animator.play_text_popup(f"奥秘触发: {card.name}", pos, Colors.CARD_RESPONSE)
            self.animator.play_particle_burst(pos, Colors.CARD_RESPONSE, 8)
            
            opp = g.get_opponent(player_id)
            result = card.execute(g, player_id, opp.player_id)
            
            p.response_zone.remove_card(t["index"])
            p.discard.append(card)
            
            # 检查灯数变化
            for p_id in g.player_ids:
                new_lamps = g.players[p_id].lamp_system.get_lamp_count()
                if new_lamps != old_lamps[p_id]:
                    diff = abs(new_lamps - old_lamps[p_id])
                    is_gain = new_lamps > old_lamps[p_id]
                    pos_lamp = self._get_lamp_screen_pos(p_id)
                    self.animator.play_lamp_change(diff, pos_lamp, is_gain)
                    self.audio.play("lamp_up" if is_gain else "lamp_down")
                    old_lamps[p_id] = new_lamps
            
            win = g.win_checker.check_victory(g, player_id)
            if win["won"]:
                self._set_message(f"[VICTORY] {win['reason']}")
                self.audio.play("victory")
                self.animator.play_victory((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                g.game_over = True
                g.winner_id = player_id
                self.scene = "gameover"
                return
    
    def _get_card_screen_pos(self, card_idx: int, hand_size: int) -> Tuple[int, int]:
        """获取指定手牌在屏幕上的中心位置"""
        total_width = hand_size * CARD_WIDTH + (hand_size - 1) * CARD_MARGIN
        start_x = (SCREEN_WIDTH - total_width) // 2
        x = start_x + card_idx * (CARD_WIDTH + CARD_MARGIN) + CARD_WIDTH // 2
        y = Layout.HAND_Y + CARD_HEIGHT // 2
        return (x, y)
    
    def _get_lamp_screen_pos(self, player_id: str) -> Tuple[int, int]:
        """获取玩家灯数显示在屏幕上的位置"""
        margin = 20
        if player_id == self.game.player_ids[0]:  # p1 底部
            y = Layout.P1_PANEL_Y + 80
        else:  # p2 顶部
            y = Layout.P2_PANEL_Y + 80
        return (margin + 35, y)
    
    def _get_response_zone_pos(self, player_id: str) -> Tuple[int, int]:
        """获取响应区中心位置"""
        from ...core.constants import RESPONSE_ZONE_LIMIT
        slot_w = 100
        margin = 20
        x = SCREEN_WIDTH - margin - RESPONSE_ZONE_LIMIT * (slot_w + 10) + 10 + slot_w // 2
        if player_id == self.game.player_ids[0]:
            y = Layout.HAND_Y - 35
        else:
            y = Layout.P2_PANEL_Y + Layout.P2_PANEL_H - 30
        return (x, y)
    
    def _set_message(self, msg: str):
        """设置提示消息"""
        self.message = msg
        self.message_timer = 3.0
        print(f"[UI] {msg}")
    
    # ============ PVE场景 ============
    
    def _handle_pve_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.pve_scene == "relic_select":
                self._handle_pve_relic_events(event)
            elif self.pve_scene == "battle":
                self._handle_pve_battle_events(event)
            elif self.pve_scene == "reward":
                self._handle_pve_reward_events(event)
            elif self.pve_scene in ("victory", "defeat"):
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    if self.pve_scene == "victory" and self.pve_level < self.pve_max_level:
                        self.pve_level += 1
                        self._start_pve_battle()
                    else:
                        self.scene = "menu"
    
    def _handle_pve_relic_events(self, event):
        relics = ["连火之心", "余烬之握", "窥焰之眼"]
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.pve_relic_selected = (self.pve_relic_selected - 1) % len(relics)
            elif event.key == pygame.K_DOWN:
                self.pve_relic_selected = (self.pve_relic_selected + 1) % len(relics)
            elif event.key == pygame.K_RETURN:
                self.pve_relic = relics[self.pve_relic_selected]
                self._start_pve_battle()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_y = pygame.mouse.get_pos()[1]
            for i in range(len(relics)):
                y = 300 + i * 80
                if y <= mouse_y <= y + 60:
                    if self.pve_relic_selected == i:
                        # 再次点击同一项 = 确认
                        self.pve_relic = relics[i]
                        self._start_pve_battle()
                    else:
                        self.pve_relic_selected = i
                    return
    
    def _start_pve_battle(self):
        """开始PVE战斗"""
        from ...pve.config import get_pve_initial_deck
        from ...pve.pve_game import PVEGame
        
        # 记录上一关剩余血量（第1关除外）
        prev_hp = None
        if self.pve_game and self.pve_level > 1:
            prev_hp = self.pve_game.player.hp
        
        if self.pve_level == 1:
            deck = get_pve_initial_deck()
        else:
            # 使用当前卡组（继承上一关的奖励牌）
            if self.pve_game:
                deck = self.pve_game.player.deck + self.pve_game.player.discard + self.pve_game.player.hand
            else:
                deck = get_pve_initial_deck()
        
        self.pve_game = PVEGame(self.pve_level, deck, self.pve_relic)
        
        # 继承血量（第2关起）
        if prev_hp is not None:
            self.pve_game.player.hp = prev_hp
        
        self.pve_scene = "battle"
        self.selected_card_idx = None
        self._set_message(f"第{self.pve_level}关：{self.pve_game.monster.name}")
    
    def _handle_pve_battle_events(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.scene = "menu"
            elif event.key == pygame.K_SPACE:
                # 跳过出牌（结束回合）
                if self.pve_game and not self.pve_game.game_over:
                    self.pve_game.end_turn()
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7):
                idx = event.key - pygame.K_1
                self._select_pve_card(idx)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.pve_game and not self.pve_game.game_over:
                self._handle_pve_mouse_click()
    
    def _select_pve_card(self, idx: int):
        if not self.pve_game or self.pve_game.game_over:
            return
        hand = self.pve_game.player.hand
        if idx < len(hand):
            if self.selected_card_idx == idx:
                # 再次点击 = 出牌
                result = self.pve_game.play_card(idx)
                self._set_message(result.get("msg", ""))
                self.selected_card_idx = None
                
                # 检查战斗结束
                if self.pve_game.game_over:
                    if self.pve_game.victory:
                        if self.pve_level >= self.pve_max_level:
                            self.pve_scene = "victory"
                            self._set_message("恭喜！通关全部5关！")
                        else:
                            self._show_pve_reward()
                    else:
                        self.pve_scene = "defeat"
                        self._set_message("你被击败了...")
            else:
                self.selected_card_idx = idx
    
    def _handle_pve_mouse_click(self):
        if not self.pve_game or self.pve_game.game_over:
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hand = self.pve_game.player.hand
        if not hand:
            return
        
        from .assets import CARD_WIDTH, CARD_MARGIN
        total_width = len(hand) * CARD_WIDTH + (len(hand) - 1) * CARD_MARGIN
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = Layout.HAND_Y
        
        for i in range(len(hand)):
            x = start_x + i * (CARD_WIDTH + CARD_MARGIN)
            rect = pygame.Rect(x, y - 10, CARD_WIDTH, 220)
            if rect.collidepoint(mouse_x, mouse_y):
                if self.selected_card_idx == i:
                    result = self.pve_game.play_card(i)
                    self._set_message(result.get("msg", ""))
                    self.selected_card_idx = None
                    
                    if self.pve_game.game_over:
                        if self.pve_game.victory:
                            if self.pve_level >= self.pve_max_level:
                                self.pve_scene = "victory"
                                self._set_message("恭喜！通关全部5关！")
                            else:
                                self._show_pve_reward()
                        else:
                            self.pve_scene = "defeat"
                            self._set_message("你被击败了...")
                else:
                    self.selected_card_idx = i
                return
        
        # 点击空白处取消选择
        self.selected_card_idx = None
    
    def _show_pve_reward(self):
        """显示过关奖励"""
        import random
        from ...pve.config import PVE_REWARD_POOL
        from ...cards.card_registry import get_card
        
        self.pve_reward_cards = []
        pool = PVE_REWARD_POOL[:]
        random.shuffle(pool)
        for card_id in pool[:3]:
            card = get_card(card_id)
            if card:
                self.pve_reward_cards.append(card)
        
        self.pve_reward_selected = 0
        self.pve_scene = "reward"
        self._set_message("选择一张牌加入卡组！")
    
    def _handle_pve_reward_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.pve_reward_selected = (self.pve_reward_selected - 1) % len(self.pve_reward_cards)
            elif event.key == pygame.K_RIGHT:
                self.pve_reward_selected = (self.pve_reward_selected + 1) % len(self.pve_reward_cards)
            elif event.key == pygame.K_RETURN:
                self._confirm_pve_reward()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x = pygame.mouse.get_pos()[0]
                from .assets import CARD_WIDTH, CARD_MARGIN
                total_width = len(self.pve_reward_cards) * (CARD_WIDTH + CARD_MARGIN * 2)
                start_x = (SCREEN_WIDTH - total_width) // 2
                for i in range(len(self.pve_reward_cards)):
                    x = start_x + i * (CARD_WIDTH + CARD_MARGIN * 2)
                    if x <= mouse_x <= x + CARD_WIDTH:
                        self.pve_reward_selected = i
                        self._confirm_pve_reward()
                        return
    
    def _calc_estimated_damage(self) -> int:
        """计算当前选中卡牌的预计伤害"""
        if not self.pve_game or self.selected_card_idx is None:
            return 0
        hand = self.pve_game.player.hand
        if self.selected_card_idx >= len(hand):
            return 0
        
        base = self.pve_game.player.lamps
        bonus = self.pve_game.player.statuses.get("this_turn_next_card", 0)
        
        # 遗物：连火之心（第2张牌）
        if self.pve_game.relic == "连火之心" and self.pve_game.player.cards_played_this_turn == 1:
            bonus += 1
        
        return max(0, base + bonus)

    def _confirm_pve_reward(self):
        """确认奖励选择"""
        selected_card = self.pve_reward_cards[self.pve_reward_selected]
        # 将奖励牌加入卡组
        if self.pve_game:
            self.pve_game.player.deck.append(selected_card)
        self.pve_level += 1
        self._start_pve_battle()
    
    def _update_pve(self, dt: float):
        """更新PVE状态"""
        self.animator.update(dt)
    
    def _draw_pve(self):
        """绘制PVE画面"""
        self.renderer.clear()
        
        if self.pve_scene == "relic_select":
            relics = ["连火之心", "余烬之握", "窥焰之眼"]
            self.renderer.draw_pve_relic_select(relics, self.pve_relic_selected)
        elif self.pve_scene == "battle" and self.pve_game:
            state = self.pve_game.get_state_dict()
            
            # 绘制怪物面板
            monster_data = {
                "name": state["monster_name"],
                "hp": state["monster_hp"],
                "max_hp": state["monster_max_hp"],
                "lamp_count": state["monster_lamps"],
                "intent": state["monster_intent"],
                "intent_value": state["monster_intent_value"],
                "shield": state["monster_shield"],
                "enraged": state["monster_enraged"],
            }
            self.renderer.draw_pve_monster_panel(monster_data)
            
            # 绘制玩家面板（复用现有P1面板逻辑）
            # 简化：直接绘制灯数和HP
            p1_panel = pygame.Rect(20, Layout.P1_PANEL_Y, SCREEN_WIDTH - 40, Layout.P1_PANEL_H)
            pygame.draw.rect(self.screen, Colors.BG_PANEL, p1_panel, border_radius=8)
            pygame.draw.rect(self.screen, Colors.BORDER_ACTIVE, p1_panel, 2, border_radius=8)
            
            name = self.renderer.font_large.render("玩家 (燃灯者)", True, Colors.TEXT)
            self.screen.blit(name, (35, Layout.P1_PANEL_Y + 15))
            
            # 灯数
            lamp = self.renderer.font_xl.render(str(state["player_lamps"]), True, Colors.LAMP_LIT)
            self.screen.blit(lamp, (35, Layout.P1_PANEL_Y + 50))
            lamp_lbl = self.renderer.font_small.render("灯数", True, Colors.TEXT_DIM)
            self.screen.blit(lamp_lbl, (35, Layout.P1_PANEL_Y + 95))
            
            # HP（放在灯数右边，避免被手牌遮挡）
            self.renderer.draw_pve_player_hp(state["player_hp"], state["player_max_hp"], 100, Layout.P1_PANEL_Y + 55)
            
            # 出牌次数
            play_text = self.renderer.font_medium.render(
                f"出牌: {state['cards_played']}/{state['max_cards']}", True, Colors.TEXT)
            self.screen.blit(play_text, (SCREEN_WIDTH - 200, Layout.P1_PANEL_Y + 20))
            
            # 绘制手牌
            hand = self.pve_game.player.hand
            
            # 预计伤害提示（选中卡牌时）
            if self.selected_card_idx is not None and self.selected_card_idx < len(hand):
                est = self._calc_estimated_damage()
                est_text = self.renderer.font_medium.render(f"预计伤害: {est}", True, Colors.TEXT_HIGHLIGHT)
                self.screen.blit(est_text, (SCREEN_WIDTH // 2 - 60, Layout.BATTLE_Y + 140))
            
            if hand:
                from .assets import CARD_WIDTH, CARD_MARGIN
                total_width = len(hand) * CARD_WIDTH + (len(hand) - 1) * CARD_MARGIN
                start_x = (SCREEN_WIDTH - total_width) // 2
                y = Layout.HAND_Y
                for i, card in enumerate(hand):
                    x = start_x + i * (CARD_WIDTH + CARD_MARGIN)
                    is_sel = (i == self.selected_card_idx)
                    is_hov = False
                    # 检查鼠标悬停
                    mx, my = pygame.mouse.get_pos()
                    if pygame.Rect(x, y - 10, CARD_WIDTH, 220).collidepoint(mx, my):
                        is_hov = True
                    self.renderer._draw_card(card, x, y, is_sel, is_hov)
            
            # 绘制状态
            if state.get("statuses"):
                self.renderer.draw_pve_statuses(state["statuses"])
            
            # 绘制选中卡牌详情
            if self.selected_card_idx is not None and self.selected_card_idx < len(hand):
                self.renderer.draw_card_detail(hand[self.selected_card_idx])
            
            # 绘制动画
            self.animator.draw(self.screen)
            
            # 绘制消息
            if self.message:
                self.renderer._draw_message(self.message)
            
            # 操作提示
            hint = self.renderer.font_small.render(
                "点击出牌 | 空格结束回合 | ESC菜单", True, Colors.TEXT_DIM)
            self.screen.blit(hint, (20, SCREEN_HEIGHT - 25))
            
        elif self.pve_scene == "reward":
            self.renderer.draw_pve_reward_screen(self.pve_reward_cards, self.pve_reward_selected)
        elif self.pve_scene == "victory":
            text = self.renderer.font_xl.render("🎉 通关成功！", True, Colors.GREEN)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)
        elif self.pve_scene == "defeat":
            text = self.renderer.font_xl.render("💀 你被击败了...", True, Colors.RED)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)
    
    # ============ 结算场景 ============
    
    def _handle_gameover_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.scene = "menu"
    
    def _draw_gameover(self):
        self.renderer.clear()
        
        g = self.game
        if g.winner_id:
            winner = g.players[g.winner_id]
            text = f"[VICTORY] {winner.name} 获胜！"
            color = Colors.GREEN
        else:
            text = "[TIMEOUT] 平局！"
            color = Colors.TEXT_DIM
        
        surf = self.renderer.font_xl.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(surf, rect)
        
        # 统计
        if g.players:
            for i, pid in enumerate(g.player_ids):
                p = g.players[pid]
                info = f"{p.name} [{p.class_type.value}] — 灯数: {p.lamp_system.get_lamp_count()}"
                info_surf = self.renderer.font_large.render(info, True, Colors.TEXT)
                info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, 350 + i * 50))
                self.screen.blit(info_surf, info_rect)
        
        hint = self.renderer.font_medium.render("按任意键返回菜单", True, Colors.TEXT_DIM)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, 500))
        self.screen.blit(hint, hint_rect)
