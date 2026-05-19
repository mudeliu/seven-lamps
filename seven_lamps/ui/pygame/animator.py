"""
Seven Lamps - Pygame Animator
七灯 pygame 动画系统

简单但够用的动画效果：卡牌飞行、数字闪烁、文字弹出
"""
import pygame
import math
from typing import List, Tuple, Optional
from .assets import Colors, get_font, SCREEN_WIDTH, SCREEN_HEIGHT


class Animation:
    """动画基类"""
    
    def __init__(self, duration: float = 0.5):
        self.duration = duration
        self.elapsed = 0.0
        self.done = False
    
    def update(self, dt: float):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.done = True
    
    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)
    
    @property
    def ease_out_quad(self) -> float:
        """缓出二次方"""
        t = self.progress
        return 1 - (1 - t) * (1 - t)
    
    @property
    def ease_out_back(self) -> float:
        """缓出回弹"""
        t = self.progress
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * math.pow(t - 1, 3) + c1 * math.pow(t - 1, 2)
    
    def draw(self, screen: pygame.Surface):
        pass


class CardFlyAnimation(Animation):
    """卡牌飞行动画（从手牌位置飞到中央）"""
    
    def __init__(self, card_name: str, card_color: Tuple, 
                 start_pos: Tuple[int, int], end_pos: Tuple[int, int],
                 duration: float = 0.4):
        super().__init__(duration)
        self.card_name = card_name
        self.card_color = card_color
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.font = get_font(20)
    
    def draw(self, screen: pygame.Surface):
        t = self.ease_out_quad
        
        # 位置插值
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
        
        # 缩放：先放大后恢复
        scale = 1.0 + 0.2 * math.sin(t * math.pi)
        
        # 透明度：后期淡出
        alpha = int(255 * (1 - t * 0.5))
        
        w, h = int(140 * scale), int(200 * scale)
        
        # 创建临时surface支持透明度
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # 卡牌背景
        pygame.draw.rect(surf, (45, 52, 75, alpha), (0, 0, w, h), border_radius=8)
        pygame.draw.rect(surf, (*self.card_color, alpha), (0, 0, w, h), 2, border_radius=8)
        
        # 名称
        name_surf = self.font.render(self.card_name, True, (220, 220, 230))
        name_surf.set_alpha(alpha)
        surf.blit(name_surf, (10, 10))
        
        rect = surf.get_rect(center=(int(x), int(y)))
        screen.blit(surf, rect)


class LampFlashAnimation(Animation):
    """灯数变化闪烁动画"""
    
    def __init__(self, value: int, pos: Tuple[int, int], 
                 is_gain: bool = True, duration: float = 0.8):
        super().__init__(duration)
        self.value = value
        self.pos = pos
        self.is_gain = is_gain
        self.color = Colors.GREEN if is_gain else Colors.RED
        self.font = get_font(48)
        self.small_font = get_font(20)
    
    def draw(self, screen: pygame.Surface):
        t = self.progress
        
        # 缩放：从大到小
        scale = 1.5 - 0.5 * t
        
        # 透明度：快速出现，缓慢淡出
        if t < 0.3:
            alpha = int(255 * (t / 0.3))
        else:
            alpha = int(255 * (1 - (t - 0.3) / 0.7))
        
        # 向上飘动
        y_offset = -30 * t
        
        text = f"+{self.value}" if self.is_gain else f"-{self.value}"
        
        # 发光效果（多层）
        for offset in [4, 2, 0]:
            glow_surf = self.font.render(text, True, self.color)
            glow_surf.set_alpha(alpha // (offset + 1) if offset > 0 else alpha)
            glow_rect = glow_surf.get_rect(center=(
                self.pos[0], int(self.pos[1] + y_offset)
            ))
            if offset > 0:
                glow_rect.inflate_ip(offset * 2, offset * 2)
            screen.blit(glow_surf, glow_rect)
        
        # 标签
        label = "加灯" if self.is_gain else "减灯"
        label_surf = self.small_font.render(label, True, self.color)
        label_surf.set_alpha(alpha)
        label_rect = label_surf.get_rect(center=(
            self.pos[0], int(self.pos[1] + y_offset + 35)
        ))
        screen.blit(label_surf, label_rect)


class TextPopupAnimation(Animation):
    """文字弹出动画（效果提示）"""
    
    def __init__(self, text: str, pos: Tuple[int, int] = None,
                 color: Tuple = Colors.TEXT_HIGHLIGHT, duration: float = 1.2):
        super().__init__(duration)
        self.text = text
        self.pos = pos or (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        self.color = color
        self.font = get_font(22)
    
    def draw(self, screen: pygame.Surface):
        t = self.progress
        
        # 向上飘动
        y = self.pos[1] - 40 * t
        
        # 透明度
        if t < 0.2:
            alpha = int(255 * (t / 0.2))
        elif t > 0.6:
            alpha = int(255 * (1 - (t - 0.6) / 0.4))
        else:
            alpha = 255
        
        # 绘制背景条
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        text_rect = text_surf.get_rect(center=(self.pos[0], int(y)))
        
        # 背景
        bg_rect = text_rect.inflate(20, 8)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (15, 20, 35, int(alpha * 0.8)), bg_surf.get_rect(), border_radius=4)
        
        screen.blit(bg_surf, bg_rect)
        screen.blit(text_surf, text_rect)


class ParticleBurstAnimation(Animation):
    """简单的粒子爆发效果（用于胜利/关键效果）"""
    
    def __init__(self, pos: Tuple[int, int], color: Tuple = Colors.LAMP_LIT,
                 count: int = 12, duration: float = 0.6):
        super().__init__(duration)
        self.pos = pos
        self.color = color
        self.particles = []
        for i in range(count):
            angle = (2 * math.pi * i) / count + (random.random() - 0.5) * 0.3
            speed = 80 + random.random() * 120
            self.particles.append({
                "angle": angle,
                "speed": speed,
                "size": 3 + random.random() * 4,
            })
    
    def draw(self, screen: pygame.Surface):
        t = self.progress
        alpha = 1.0 - t
        
        for p in self.particles:
            dist = p["speed"] * t
            x = self.pos[0] + math.cos(p["angle"]) * dist
            y = self.pos[1] + math.sin(p["angle"]) * dist
            size = int(p["size"] * (1 - t * 0.5))
            
            color = (
                int(self.color[0] * alpha),
                int(self.color[1] * alpha),
                int(self.color[2] * alpha),
            )
            pygame.draw.circle(screen, color, (int(x), int(y)), max(1, size))


class ShakeAnimation(Animation):
    """屏幕/元素震动效果"""
    
    def __init__(self, target_rect: pygame.Rect, intensity: int = 5, duration: float = 0.3):
        super().__init__(duration)
        self.target_rect = target_rect
        self.intensity = intensity
        self.original_pos = target_rect.topleft
    
    def draw_offset(self) -> Tuple[int, int]:
        if self.done:
            return (0, 0)
        t = 1.0 - self.progress
        dx = int((random.random() - 0.5) * 2 * self.intensity * t)
        dy = int((random.random() - 0.5) * 2 * self.intensity * t)
        return (dx, dy)


# 需要random，延迟导入避免循环
import random


class Animator:
    """动画管理器"""
    
    def __init__(self):
        self.animations: List[Animation] = []
    
    def add(self, anim: Animation):
        self.animations.append(anim)
    
    def update(self, dt: float):
        for anim in self.animations:
            anim.update(dt)
        self.animations = [a for a in self.animations if not a.done]
    
    def draw(self, screen: pygame.Surface):
        for anim in self.animations:
            anim.draw(screen)
    
    def clear(self):
        self.animations.clear()
    
    def is_busy(self) -> bool:
        return len(self.animations) > 0
    
    # ============ 便捷工厂方法 ============
    
    def play_card_fly(self, card_name: str, card_color: Tuple,
                      start_pos: Tuple[int, int]):
        """卡牌打出飞行动画"""
        end_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.add(CardFlyAnimation(card_name, card_color, start_pos, end_pos, 0.4))
    
    def play_lamp_change(self, value: int, pos: Tuple[int, int], is_gain: bool = True):
        """灯数变化动画"""
        self.add(LampFlashAnimation(value, pos, is_gain, 0.8))
    
    def play_text_popup(self, text: str, pos: Tuple[int, int] = None,
                        color: Tuple = Colors.TEXT_HIGHLIGHT):
        """文字弹出动画"""
        self.add(TextPopupAnimation(text, pos, color, 1.2))
    
    def play_particle_burst(self, pos: Tuple[int, int], 
                            color: Tuple = Colors.LAMP_LIT, count: int = 12):
        """粒子爆发"""
        self.add(ParticleBurstAnimation(pos, color, count, 0.6))
    
    def play_victory(self, pos: Tuple[int, int]):
        """胜利特效组合"""
        self.add(ParticleBurstAnimation(pos, Colors.LAMP_LIT, 24, 1.0))
        self.add(ParticleBurstAnimation(pos, Colors.TEXT_HIGHLIGHT, 16, 0.8))
        self.add(TextPopupAnimation("🏆 胜利！", pos, Colors.GREEN, 2.0))
