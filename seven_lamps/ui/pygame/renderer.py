"""
Seven Lamps - Pygame Renderer
七灯 pygame 渲染器

负责绘制所有游戏元素：玩家面板、手牌、灯系统、日志等
"""
import pygame
from typing import List, Optional, Dict, Any

from .assets import Colors, Layout, CARD_WIDTH, CARD_HEIGHT, CARD_MARGIN, get_font
from ...core.enums import ClassType, CardType, PositionState
from ...core.game_state import GameState, Player


class Renderer:
    """游戏渲染器"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_small = get_font(14)
        self.font_medium = get_font(18)
        self.font_large = get_font(24)
        self.font_xl = get_font(36)
        
    def clear(self):
        """清空屏幕"""
        self.screen.fill(Colors.BG)
    
    def draw_game(self, game: GameState, selected_card_idx: Optional[int] = None,
                  hover_card_idx: Optional[int] = None, message: str = "",
                  show_response_button: bool = False, response_button_hovered: bool = False,
                  response_mode: Optional[str] = None, replace_hover_idx: Optional[int] = None,
                  action_history=None):
        """绘制完整游戏画面"""
        self.clear()
        
        if game is None or not game.players:
            return
        
        # 绘制两个玩家面板
        p1 = game.players.get(game.player_ids[0])
        p2 = game.players.get(game.player_ids[1])
        
        if p1 and p2:
            is_p1_active = game.active_player_id == p1.player_id
            is_p2_active = game.active_player_id == p2.player_id
            
            self._draw_player_panel(p2, Layout.P2_PANEL_Y, is_p2_active, is_top=True)
            self._draw_player_panel(p1, Layout.P1_PANEL_Y, is_p1_active, is_top=False)
            
            # 绘制中间区域
            self._draw_battle_area(game, p1, p2, action_history)
            
            # 绘制手牌（仅当前活跃玩家的手牌）
            active_p = game.players.get(game.active_player_id)
            if active_p:
                self._draw_hand(active_p.hand, selected_card_idx, hover_card_idx, 
                               active_p.player_id == p1.player_id)
                
                # 绘制响应区槽位（当前玩家）
                is_bottom = active_p.player_id == p1.player_id
                self._draw_response_slots(active_p, is_bottom, 
                                         response_mode == "selecting_replace", replace_hover_idx)
                
                # 绘制"暗置"按钮
                if show_response_button and is_bottom:
                    self._draw_response_button(response_button_hovered)
        
        # 绘制替换提示
        if response_mode == "selecting_replace":
            self._draw_replace_prompt()
        
        # 绘制底部消息
        if message:
            self._draw_message(message)
    
    def _draw_player_panel(self, player: Player, y: int, is_active: bool, is_top: bool):
        """绘制玩家信息面板"""
        panel_h = Layout.P2_PANEL_H
        margin = 20
        
        # 面板背景
        panel_rect = pygame.Rect(margin, y, SCREEN_WIDTH - margin * 2, panel_h - 10)
        color = Colors.BORDER_ACTIVE if is_active else Colors.BORDER
        pygame.draw.rect(self.screen, Colors.BG_PANEL, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, color, panel_rect, 2, border_radius=8)
        
        # 玩家名和职业
        name_text = self.font_large.render(
            f"{player.name} [{player.class_type.value}]", True, Colors.TEXT
        )
        self.screen.blit(name_text, (margin + 15, y + 15))
        
        # 灯数（大号）
        lamp_num = self.font_xl.render(str(player.lamp_system.get_lamp_count()), True, Colors.LAMP_LIT)
        self.screen.blit(lamp_num, (margin + 20, y + 55))
        lamp_label = self.font_small.render("灯数", True, Colors.TEXT_DIM)
        self.screen.blit(lamp_label, (margin + 20, y + 100))
        
        # 守夜人位置显示
        if player.class_type == ClassType.NIGHTWATCH:
            self._draw_positions(player, margin + 100, y + 55)
        
        # 牌库/手牌/弃牌统计
        stats_x = margin + 320
        stats = [
            ("手牌", len(player.hand)),
            ("牌库", len(player.deck)),
            ("弃牌", len(player.discard)),
            ("奥秘", len(player.response_zone.cards)),
        ]
        for i, (label, count) in enumerate(stats):
            sx = stats_x + i * 90
            num = self.font_medium.render(str(count), True, Colors.TEXT)
            self.screen.blit(num, (sx, y + 55))
            lbl = self.font_small.render(label, True, Colors.TEXT_DIM)
            self.screen.blit(lbl, (sx, y + 80))
        
        # 响应区（奥秘）简述（仅对手显示，自己的响应区用槽位显示）
        if not is_active and player.response_zone.cards:
            resp_text = self.font_small.render(
                f"奥秘: {len(player.response_zone.cards)}张", True, Colors.CARD_RESPONSE
            )
            self.screen.blit(resp_text, (stats_x, y + 110))
    
    def _draw_action_history(self, history, x: int, y: int):
        """绘制行动历史区（左侧）"""
        if not history:
            return
        
        panel_w = 240
        line_h = 20
        max_items = 4
        items = history[-max_items:]
        panel_h = 30 + len(items) * line_h
        
        # 面板背景
        panel_rect = pygame.Rect(x, y, panel_w, panel_h)
        pygame.draw.rect(self.screen, (20, 26, 45), panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, Colors.BORDER, panel_rect, 1, border_radius=8)
        
        # 标题
        title = self.font_small.render("行动历史", True, Colors.TEXT_DIM)
        self.screen.blit(title, (x + 10, y + 6))
        
        cy = y + 26
        for item in items:
            turn = item.get("turn", "?")
            name = item.get("player_name", "?")
            card = item.get("card_name", "?")
            effect = item.get("effect_desc", "")
            is_enemy = item.get("is_enemy", False)
            
            # 颜色：敌方红色，己方绿色
            name_color = Colors.RED if is_enemy else Colors.GREEN
            
            # 回合号
            turn_surf = self.font_small.render(f"T{turn}", True, Colors.TEXT_DIM)
            self.screen.blit(turn_surf, (x + 8, cy))
            
            # 玩家名（截断）
            display_name = name[:3] + "…" if len(name) > 3 else name
            name_surf = self.font_small.render(display_name, True, name_color)
            self.screen.blit(name_surf, (x + 32, cy))
            
            # 卡牌名
            card_surf = self.font_small.render(card, True, Colors.TEXT)
            self.screen.blit(card_surf, (x + 72, cy))
            
            # 效果（截断）
            if effect:
                ef_text = effect[:8] + "…" if len(effect) > 8 else effect
                ef_surf = self.font_small.render(ef_text, True, Colors.TEXT_DIM)
                self.screen.blit(ef_surf, (x + 130, cy))
            
            cy += line_h
    
    def _draw_positions(self, player: Player, x: int, y: int):
        """绘制守夜人的1-7号位置"""
        radius = 18
        spacing = 45
        for i in range(1, 8):
            px = x + (i - 1) * spacing
            is_lit = player.lamp_system.position_states[i] == PositionState.LIT
            color = Colors.LAMP_LIT if is_lit else Colors.LAMP_EMPTY
            
            # 奇数位高亮边框
            if i in [1, 3, 5, 7]:
                pygame.draw.circle(self.screen, Colors.TEXT_DIM, (px, y + radius), radius + 2, 1)
            
            pygame.draw.circle(self.screen, color, (px, y + radius), radius)
            
            # 编号
            num = self.font_small.render(str(i), True, Colors.BG if is_lit else Colors.TEXT_DIM)
            num_rect = num.get_rect(center=(px, y + radius))
            self.screen.blit(num, num_rect)
    
    def _draw_battle_area(self, game: GameState, p1: Player, p2: Player, action_history=None):
        """绘制中间战场区域"""
        y = Layout.BATTLE_Y
        h = Layout.BATTLE_H
        
        # 回合信息
        turn_text = self.font_large.render(f"第 {game.turn} 回合", True, Colors.TEXT_HIGHLIGHT)
        turn_rect = turn_text.get_rect(center=(SCREEN_WIDTH // 2, y + 40))
        self.screen.blit(turn_text, turn_rect)
        
        # 当前玩家提示
        active_name = game.players[game.active_player_id].name
        active_text = self.font_medium.render(f"当前行动: {active_name}", True, Colors.BLUE)
        active_rect = active_text.get_rect(center=(SCREEN_WIDTH // 2, y + 80))
        self.screen.blit(active_text, active_rect)
        
        # 最近日志（显示最近3条）
        log_y = y + 120
        recent_logs = game.logs[-5:] if game.logs else []
        for log in recent_logs:
            log_surf = self.font_small.render(log, True, Colors.TEXT_DIM)
            log_rect = log_surf.get_rect(center=(SCREEN_WIDTH // 2, log_y))
            self.screen.blit(log_surf, log_rect)
            log_y += 22
        
        # 行动历史区（左侧）
        if action_history:
            self._draw_action_history(action_history, 20, y + 160)
    
    def _draw_hand(self, cards: List, selected_idx: Optional[int], 
                   hover_idx: Optional[int], is_bottom: bool):
        """绘制手牌"""
        if not cards:
            return
        
        total_width = len(cards) * CARD_WIDTH + (len(cards) - 1) * CARD_MARGIN
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = Layout.HAND_Y if is_bottom else Layout.P2_PANEL_Y + 80
        
        for i, card in enumerate(cards):
            x = start_x + i * (CARD_WIDTH + CARD_MARGIN)
            is_selected = (i == selected_idx)
            is_hovered = (i == hover_idx)
            self._draw_card(card, x, y, is_selected, is_hovered)
    
    def _draw_card(self, card, x: int, y: int, selected: bool = False, hovered: bool = False):
        """绘制单张卡牌"""
        # 颜色根据卡牌类型
        if card.card_type == CardType.RESPONSE:
            base_color = Colors.CARD_RESPONSE
        elif card.card_type == CardType.SPECIAL:
            base_color = Colors.CARD_SPECIAL
        else:
            base_color = Colors.CARD_INSTANT
        
        # 悬停/选中偏移
        offset_y = -10 if (hovered or selected) else 0
        
        card_rect = pygame.Rect(x, y + offset_y, CARD_WIDTH, CARD_HEIGHT)
        
        # 阴影
        shadow_rect = card_rect.copy()
        shadow_rect.move_ip(3, 3)
        pygame.draw.rect(self.screen, (10, 12, 20), shadow_rect, border_radius=6)
        
        # 卡牌主体
        pygame.draw.rect(self.screen, Colors.BG_CARD, card_rect, border_radius=6)
        pygame.draw.rect(self.screen, base_color, card_rect, 2, border_radius=6)
        
        if selected:
            pygame.draw.rect(self.screen, Colors.TEXT_HIGHLIGHT, card_rect, 3, border_radius=6)
        
        # 卡牌名称
        name = self.font_medium.render(card.name, True, Colors.TEXT)
        self.screen.blit(name, (x + 10, y + offset_y + 10))
        
        # 类型标签
        type_text = self.font_small.render(card.card_type.value, True, base_color)
        self.screen.blit(type_text, (x + 10, y + offset_y + 38))
        
        # 门槛
        if card.threshold_desc:
            th_text = self.font_small.render(f"门槛: {card.threshold_desc}", True, Colors.TEXT_DIM)
            self.screen.blit(th_text, (x + 10, y + offset_y + 58))
        
        # 效果描述（双行简化版）
        effect = card.effect_desc
        max_chars = 16
        if len(effect) <= max_chars:
            ef_text = self.font_small.render(effect, True, Colors.TEXT)
            self.screen.blit(ef_text, (x + 10, y + offset_y + 85))
        elif len(effect) <= max_chars * 2:
            line1 = effect[:max_chars]
            line2 = effect[max_chars:]
            ef1 = self.font_small.render(line1, True, Colors.TEXT)
            ef2 = self.font_small.render(line2, True, Colors.TEXT)
            self.screen.blit(ef1, (x + 10, y + offset_y + 85))
            self.screen.blit(ef2, (x + 10, y + offset_y + 105))
        else:
            line1 = effect[:max_chars]
            line2 = effect[max_chars:max_chars*2-1] + "..."
            ef1 = self.font_small.render(line1, True, Colors.TEXT)
            ef2 = self.font_small.render(line2, True, Colors.TEXT)
            self.screen.blit(ef1, (x + 10, y + offset_y + 85))
            self.screen.blit(ef2, (x + 10, y + offset_y + 105))
        
        # 标签（简化：只显示普通/奥秘）
        if card.tags:
            tag_label = "奥秘" if card.card_type.value == "响应" else "普通"
            tag_text = self.font_small.render(tag_label, True, Colors.TEXT_HIGHLIGHT)
            tag_y = y + offset_y + 130 if len(card.effect_desc) > 16 else y + offset_y + 115
            self.screen.blit(tag_text, (x + 10, tag_y))
    
    def draw_card_detail(self, card):
        """绘制右侧卡牌详情面板"""
        panel_x = 1040
        panel_y = 220
        panel_w = 220
        line_h = 22
        padding = 14
        
        # 计算面板高度
        content_lines = 7  # 名称, ID, 分隔, 类型, 类别, 分隔, 门槛
        effect_lines = self._wrap_text_lines(card.effect_desc, 18)  # 每行18个字符
        content_lines += len(effect_lines) + 1  # +1 for separator
        if card.tags:
            content_lines += 2  # separator + tags
        
        panel_h = padding * 2 + content_lines * line_h
        
        # 面板背景
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, Colors.BG_PANEL, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, Colors.TEXT_HIGHLIGHT, panel_rect, 2, border_radius=10)
        
        # 类型色条
        if card.card_type == CardType.RESPONSE:
            bar_color = Colors.CARD_RESPONSE
        elif card.card_type == CardType.SPECIAL:
            bar_color = Colors.CARD_SPECIAL
        else:
            bar_color = Colors.CARD_INSTANT
        bar_rect = pygame.Rect(panel_x, panel_y, 6, panel_h)
        pygame.draw.rect(self.screen, bar_color, bar_rect, border_radius=3)
        
        cx = panel_x + padding + 6
        cy = panel_y + padding
        
        # 名称
        name = self.font_large.render(card.name, True, Colors.TEXT_HIGHLIGHT)
        self.screen.blit(name, (cx, cy))
        cy += line_h + 4
        
        # ID + 职业
        info = self.font_small.render(f"{card.id} | {card.class_type.value}", True, Colors.TEXT_DIM)
        self.screen.blit(info, (cx, cy))
        cy += line_h + 8
        
        # 分隔线
        pygame.draw.line(self.screen, Colors.BORDER, (cx, cy), (panel_x + panel_w - padding, cy), 1)
        cy += 10
        
        # 类型
        type_txt = self.font_small.render(f"类型: {card.card_type.value}", True, Colors.TEXT)
        self.screen.blit(type_txt, (cx, cy))
        cy += line_h
        
        # 类别
        cat_txt = self.font_small.render(f"类别: {card.category.value if hasattr(card.category, 'value') else str(card.category)}", True, Colors.TEXT)
        self.screen.blit(cat_txt, (cx, cy))
        cy += line_h + 8
        
        # 分隔线
        pygame.draw.line(self.screen, Colors.BORDER, (cx, cy), (panel_x + panel_w - padding, cy), 1)
        cy += 10
        
        # 门槛
        th_txt = self.font_small.render(f"门槛: {card.threshold_desc}", True, bar_color)
        self.screen.blit(th_txt, (cx, cy))
        cy += line_h + 8
        
        # 分隔线
        pygame.draw.line(self.screen, Colors.BORDER, (cx, cy), (panel_x + panel_w - padding, cy), 1)
        cy += 10
        
        # 效果（多行）
        for line in effect_lines:
            ef = self.font_small.render(line, True, Colors.TEXT)
            self.screen.blit(ef, (cx, cy))
            cy += line_h
        cy += 8
        
        # 标签
        if card.tags:
            pygame.draw.line(self.screen, Colors.BORDER, (cx, cy), (panel_x + panel_w - padding, cy), 1)
            cy += 10
            tags_str = "  ".join([f"[{t}]" for t in card.tags])
            tag = self.font_small.render(tags_str, True, Colors.TEXT_HIGHLIGHT)
            self.screen.blit(tag, (cx, cy))
    
    def _wrap_text_lines(self, text: str, max_chars: int) -> List[str]:
        """将文本按字符数自动换行"""
        if not text:
            return [""]
        lines = []
        current = ""
        for char in text:
            current += char
            if len(current) >= max_chars:
                lines.append(current)
                current = ""
        if current:
            lines.append(current)
        return lines if lines else [""]
    
    def _draw_response_slots(self, player: Player, is_bottom: bool, 
                             selecting: bool = False, hover_idx: Optional[int] = None):
        """绘制响应区槽位（两个奥秘位置）"""
        from ...core.constants import RESPONSE_ZONE_LIMIT
        
        slot_w, slot_h = 100, 40
        margin = 20
        
        if is_bottom:
            y = Layout.HAND_Y - 55
        else:
            y = Layout.P2_PANEL_Y + Layout.P2_PANEL_H - 50
        
        x = SCREEN_WIDTH - margin - RESPONSE_ZONE_LIMIT * (slot_w + 10) + 10
        
        # 标题
        title = self.font_small.render("响应区", True, Colors.CARD_RESPONSE)
        self.screen.blit(title, (x, y - 20))
        
        for i in range(RESPONSE_ZONE_LIMIT):
            slot_x = x + i * (slot_w + 10)
            slot_rect = pygame.Rect(slot_x, y, slot_w, slot_h)
            
            # 槽位背景
            has_card = i < len(player.response_zone.cards)
            if has_card:
                bg_color = Colors.CARD_RESPONSE
                border_color = Colors.TEXT_HIGHLIGHT if (selecting and hover_idx == i) else Colors.BORDER
                border_width = 3 if (selecting and hover_idx == i) else 1
            else:
                bg_color = Colors.BG
                border_color = Colors.BORDER
                border_width = 1
            
            pygame.draw.rect(self.screen, bg_color, slot_rect, border_radius=6)
            pygame.draw.rect(self.screen, border_color, slot_rect, border_width, border_radius=6)
            
            # 内容
            if has_card:
                card = player.response_zone.cards[i]
                name_text = self.font_small.render(card.name, True, Colors.TEXT)
                self.screen.blit(name_text, (slot_x + 8, y + 10))
            else:
                empty_text = self.font_small.render("空", True, Colors.TEXT_DIM)
                empty_rect = empty_text.get_rect(center=slot_rect.center)
                self.screen.blit(empty_text, empty_rect)
    
    def _draw_response_button(self, hovered: bool = False):
        """绘制'暗置'按钮"""
        btn_w, btn_h = 100, 36
        x = (SCREEN_WIDTH - btn_w) // 2
        y = Layout.HAND_Y - 55
        
        rect = pygame.Rect(x, y, btn_w, btn_h)
        color = Colors.BUTTON_HOVER if hovered else Colors.BUTTON
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, Colors.CARD_RESPONSE, rect, 2, border_radius=6)
        
        text = self.font_medium.render("暗置(R)", True, Colors.TEXT)
        text_rect = text.get_rect(center=rect.center)
        self.screen.blit(text, text_rect)
    
    def _draw_replace_prompt(self):
        """绘制替换选择提示"""
        prompt = self.font_medium.render("点击响应区槽位，选择要替换的奥秘", True, Colors.RED)
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, Layout.HAND_Y - 80))
        
        bar_rect = prompt_rect.inflate(30, 10)
        pygame.draw.rect(self.screen, Colors.BG_PANEL, bar_rect, border_radius=6)
        pygame.draw.rect(self.screen, Colors.RED, bar_rect, 2, border_radius=6)
        
        self.screen.blit(prompt, prompt_rect)
    
    def get_response_button_rect(self) -> Optional[pygame.Rect]:
        """获取响应按钮的rect供碰撞检测"""
        btn_w, btn_h = 100, 36
        x = (SCREEN_WIDTH - btn_w) // 2
        y = Layout.HAND_Y - 55
        return pygame.Rect(x, y, btn_w, btn_h)
    
    def get_response_slot_rects(self, is_bottom: bool) -> List[pygame.Rect]:
        """获取响应区槽位的rect列表"""
        from ...core.constants import RESPONSE_ZONE_LIMIT
        slot_w, slot_h = 100, 40
        margin = 20
        
        if is_bottom:
            y = Layout.HAND_Y - 55
        else:
            y = Layout.P2_PANEL_Y + Layout.P2_PANEL_H - 50
        
        x = SCREEN_WIDTH - margin - RESPONSE_ZONE_LIMIT * (slot_w + 10) + 10
        
        rects = []
        for i in range(RESPONSE_ZONE_LIMIT):
            slot_x = x + i * (slot_w + 10)
            rects.append(pygame.Rect(slot_x, y, slot_w, slot_h))
        return rects
    
    def _draw_message(self, message: str):
        """绘制底部提示消息"""
        msg = self.font_medium.render(message, True, Colors.TEXT_HIGHLIGHT)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        
        # 背景条
        bar_rect = msg_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, Colors.BG_PANEL, bar_rect, border_radius=4)
        pygame.draw.rect(self.screen, Colors.BORDER, bar_rect, 1, border_radius=4)
        
        self.screen.blit(msg, msg_rect)
    
    def draw_menu(self, title: str, options: List[str], selected: int = 0):
        """绘制菜单界面"""
        self.clear()
        
        # 标题
        title_surf = self.font_xl.render(title, True, Colors.TEXT_HIGHLIGHT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title_surf, title_rect)
        
        # 选项
        for i, option in enumerate(options):
            color = Colors.TEXT_HIGHLIGHT if i == selected else Colors.TEXT
            opt_surf = self.font_large.render(option, True, color)
            opt_rect = opt_surf.get_rect(center=(SCREEN_WIDTH // 2, 320 + i * 60))
            self.screen.blit(opt_surf, opt_rect)
    
    def draw_button(self, text: str, rect: pygame.Rect, hovered: bool = False) -> pygame.Rect:
        """绘制按钮，返回rect供碰撞检测"""
        color = Colors.BUTTON_HOVER if hovered else Colors.BUTTON
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, Colors.BORDER, rect, 1, border_radius=6)
        
        text_surf = self.font_medium.render(text, True, Colors.TEXT)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
        return rect
    
    def draw_choice_popup(self, title: str, options: List[str], selected: int = 0):
        """绘制选择弹窗"""
        # 半透明背景遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 弹窗面板
        popup_w = 400
        popup_h = 200 + len(options) * 60
        popup_x = (SCREEN_WIDTH - popup_w) // 2
        popup_y = (SCREEN_HEIGHT - popup_h) // 2
        popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
        
        pygame.draw.rect(self.screen, Colors.BG_PANEL, popup_rect, border_radius=12)
        pygame.draw.rect(self.screen, Colors.BORDER_ACTIVE, popup_rect, 3, border_radius=12)
        
        # 标题
        title_surf = self.font_large.render(title, True, Colors.TEXT_HIGHLIGHT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, popup_y + 40))
        self.screen.blit(title_surf, title_rect)
        
        # 选项按钮
        for i, option in enumerate(options):
            btn_y = popup_y + 90 + i * 60
            btn_rect = pygame.Rect(popup_x + 50, btn_y, popup_w - 100, 50)
            
            is_selected = (i == selected)
            color = Colors.BUTTON_HOVER if is_selected else Colors.BUTTON
            border_color = Colors.TEXT_HIGHLIGHT if is_selected else Colors.BORDER
            border_width = 3 if is_selected else 1
            
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=8)
            pygame.draw.rect(self.screen, border_color, btn_rect, border_width, border_radius=8)
            
            opt_surf = self.font_medium.render(option, True, Colors.TEXT)
            opt_rect = opt_surf.get_rect(center=btn_rect.center)
            self.screen.blit(opt_surf, opt_rect)
        
        # 提示
        hint = self.font_small.render("↑↓选择 / Enter确认 / 鼠标点击", True, Colors.TEXT_DIM)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, popup_y + popup_h - 30))
        self.screen.blit(hint, hint_rect)
    
    def get_choice_button_rects(self, option_count: int) -> List[pygame.Rect]:
        """获取选择弹窗按钮的rect列表，供碰撞检测"""
        popup_w = 400
        popup_h = 200 + option_count * 60
        popup_x = (SCREEN_WIDTH - popup_w) // 2
        popup_y = (SCREEN_HEIGHT - popup_h) // 2
        
        rects = []
        for i in range(option_count):
            btn_y = popup_y + 90 + i * 60
            btn_rect = pygame.Rect(popup_x + 50, btn_y, popup_w - 100, 50)
            rects.append(btn_rect)
        return rects


    # ========== PVE渲染方法 ==========

    def draw_pve_monster_panel(self, monster_data: dict):
        """绘制PVE怪物面板（顶部）"""
        y = Layout.P2_PANEL_Y
        panel_h = Layout.P2_PANEL_H
        margin = 20

        panel_rect = pygame.Rect(margin, y, SCREEN_WIDTH - margin * 2, panel_h - 10)
        color = Colors.RED if monster_data.get("enraged") else Colors.BORDER
        pygame.draw.rect(self.screen, (35, 20, 25), panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, color, panel_rect, 2, border_radius=8)

        # 怪物名
        name_text = self.font_large.render(
            f"{monster_data['name']} {'[狂暴!]' if monster_data.get('enraged') else ''}",
            True, Colors.RED if monster_data.get("enraged") else Colors.TEXT
        )
        self.screen.blit(name_text, (margin + 15, y + 10))

        # 核心耐久条
        hp_current = monster_data.get("hp", 0)
        hp_max = monster_data.get("max_hp", 1)
        bar_w = 300
        bar_h = 20
        bar_x = margin + 15
        bar_y = y + 50
        hp_ratio = hp_current / hp_max if hp_max > 0 else 0

        pygame.draw.rect(self.screen, (60, 30, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, Colors.RED, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h), border_radius=4)
        hp_text = self.font_small.render(f"核心耐久: {hp_current}/{hp_max}", True, Colors.TEXT)
        self.screen.blit(hp_text, (bar_x, bar_y + 25))

        # 灯数
        lamp_num = self.font_xl.render(str(monster_data.get("lamp_count", 0)), True, Colors.LAMP_LIT)
        self.screen.blit(lamp_num, (margin + 350, y + 45))
        lamp_label = self.font_small.render("灯数", True, Colors.TEXT_DIM)
        self.screen.blit(lamp_label, (margin + 350, y + 90))

        # 护盾
        shield = monster_data.get("shield", 0)
        if shield > 0:
            shield_text = self.font_medium.render(f"护盾:{shield}", True, Colors.CARD_RESPONSE)
            self.screen.blit(shield_text, (margin + 420, y + 55))

        # 意图
        intent = monster_data.get("intent", "")
        intent_val = monster_data.get("intent_value", 0)
        intent_map = {
            "attack": ("🗡️ 攻击", f"造成{intent_val}伤害"),
            "charge": ("⚡ 蓄力", f"灯数+{intent_val}"),
            "seal": ("🔒 封印", "下回合封印即时牌"),
            "shield": ("🛡️ 护盾", "获得1层护盾"),
            "disrupt": ("👁️ 干扰", "弃掉你1张手牌"),
        }
        if intent in intent_map:
            icon, desc = intent_map[intent]
            intent_text = self.font_medium.render(f"下回合意图: {icon} {desc}", True, Colors.TEXT_HIGHLIGHT)
            self.screen.blit(intent_text, (margin + 15, y + 105))

    def draw_pve_player_hp(self, hp: int, max_hp: int, x: int, y: int):
        """在玩家面板绘制生命条"""
        bar_w = 120
        bar_h = 14
        hp_ratio = hp / max_hp if max_hp > 0 else 0

        pygame.draw.rect(self.screen, (60, 30, 30), (x, y, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, Colors.GREEN, (x, y, int(bar_w * hp_ratio), bar_h), border_radius=4)
        hp_text = self.font_small.render(f"生命 {hp}/{max_hp}", True, Colors.TEXT)
        self.screen.blit(hp_text, (x, y + 16))

    def draw_pve_statuses(self, statuses: dict):
        """绘制玩家状态buff"""
        if not statuses:
            return
        x = 1040
        y = 180
        panel_w = 220
        line_h = 20
        panel_h = 30 + len(statuses) * line_h

        panel_rect = pygame.Rect(x, y, panel_w, panel_h)
        pygame.draw.rect(self.screen, (25, 32, 55), panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, Colors.BORDER, panel_rect, 1, border_radius=8)

        title = self.font_small.render("状态", True, Colors.TEXT_DIM)
        self.screen.blit(title, (x + 10, y + 6))

        cy = y + 26
        status_names = {
            "next_turn_damage": "下回合伤害+{}",
            "this_turn_next_card": "本回合下张+{}",
            "next_turn_draw": "下回合抽牌+{}",
            "monster_growth_reduction": "怪物增长-{}",
            "monster_dot": "怪物灼烧({}t)",
            "seal_monster": "封印怪物",
            "vulnerable": "脆弱+{}",
            "block_next": "格挡下次伤害",
        }
        for key, val in statuses.items():
            name_template = status_names.get(key, key)
            text = name_template.format(val) if isinstance(val, int) else name_template
            surf = self.font_small.render(text, True, Colors.TEXT_HIGHLIGHT)
            self.screen.blit(surf, (x + 10, cy))
            cy += line_h

    def draw_pve_reward_screen(self, reward_cards: list, selected: int = 0):
        """绘制PVE奖励选择界面"""
        self.clear()
        title = self.font_xl.render("过关奖励 — 选择一张牌加入卡组", True, Colors.TEXT_HIGHLIGHT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        total_width = len(reward_cards) * (CARD_WIDTH + CARD_MARGIN * 2)
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = 250

        for i, card in enumerate(reward_cards):
            x = start_x + i * (CARD_WIDTH + CARD_MARGIN * 2)
            is_selected = (i == selected)
            self._draw_card(card, x, y, selected=is_selected, hovered=False)
            if is_selected:
                sel_text = self.font_medium.render("← 已选择", True, Colors.TEXT_HIGHLIGHT)
                self.screen.blit(sel_text, (x + CARD_WIDTH + 10, y + 80))

        hint = self.font_small.render("↑↓选择 / Enter确认", True, Colors.TEXT_DIM)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 100))

    def draw_pve_relic_select(self, relics: list, selected: int = 0):
        """绘制遗物选择界面"""
        self.clear()
        title = self.font_xl.render("选择你的遗物", True, Colors.TEXT_HIGHLIGHT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)

        for i, relic in enumerate(relics):
            y = 300 + i * 80
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, y, 400, 60)
            is_selected = (i == selected)
            color = Colors.BUTTON_HOVER if is_selected else Colors.BUTTON
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, Colors.TEXT_HIGHLIGHT if is_selected else Colors.BORDER,
                           rect, 2 if is_selected else 1, border_radius=8)

            name = self.font_large.render(relic, True, Colors.TEXT)
            self.screen.blit(name, (rect.x + 20, rect.y + 15))

        desc_map = {
            "连火之心": "每回合第2张出牌伤害+1",
            "余烬之握": "生命≤3时，每回合开始+1灯",
            "窥焰之眼": "每回合抽牌数+1",
        }
        if relics[selected] in desc_map:
            desc = self.font_small.render(desc_map[relics[selected]], True, Colors.TEXT_DIM)
            self.screen.blit(desc, (SCREEN_WIDTH // 2 - 150, 300 + len(relics) * 80 + 20))

        hint = self.font_small.render("↑↓选择 / Enter确认", True, Colors.TEXT_DIM)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 80))


# 为了renderer能正常引用
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
