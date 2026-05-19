"""
Seven Lamps - Pygame Audio
七灯 pygame 音效系统

使用numpy生成简单合成音效，零外部音频文件依赖。
支持：出牌、抽牌、加灯、减灯、奥秘触发、胜利
"""
import math
import numpy as np
import pygame
from typing import Optional


class AudioManager:
    """音效管理器"""
    
    def __init__(self, enabled: bool = True, master_volume: float = 0.4):
        self.enabled = enabled
        self.master_volume = master_volume
        
        # 尝试初始化mixer
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.mixer_available = True
        except Exception as e:
            print(f"[Audio] Mixer初始化失败: {e}")
            self.mixer_available = False
            self.enabled = False
        
        self.sounds = {}
        if self.enabled:
            self._generate_sounds()
    
    def _generate_tone(self, freq: float, duration: float, 
                       vol: float = 0.3, fade_out: bool = True,
                       waveform: str = "sine") -> Optional[pygame.mixer.Sound]:
        """生成单音调音效"""
        if not self.mixer_available:
            return None
        
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        
        t = np.linspace(0, duration, n_samples, endpoint=False)
        
        if waveform == "sine":
            wave = np.sin(2 * np.pi * freq * t)
        elif waveform == "square":
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif waveform == "sawtooth":
            wave = 2 * (t * freq - np.floor(t * freq + 0.5))
        else:
            wave = np.sin(2 * np.pi * freq * t)
        
        # 包络：快速attack，可选fade out
        envelope = np.ones_like(t)
        attack = int(0.01 * sample_rate)
        envelope[:attack] = np.linspace(0, 1, attack)
        if fade_out:
            fade = int(0.1 * sample_rate)
            if n_samples > fade:
                envelope[-fade:] = np.linspace(1, 0, fade)
        
        wave = wave * envelope * vol
        
        # 转16位PCM stereo
        audio = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((audio, audio))
        
        try:
            sound = pygame.mixer.Sound(buffer=stereo.tobytes())
            return sound
        except Exception as e:
            print(f"[Audio] 生成音效失败: {e}")
            return None
    
    def _generate_chord(self, freqs: list, duration: float, 
                        vol: float = 0.25) -> Optional[pygame.mixer.Sound]:
        """生成和弦音效"""
        if not self.mixer_available:
            return None
        
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        
        wave = np.zeros_like(t)
        for freq in freqs:
            wave += np.sin(2 * np.pi * freq * t)
        wave /= len(freqs)
        
        # 包络
        envelope = np.ones_like(t)
        attack = int(0.02 * sample_rate)
        envelope[:attack] = np.linspace(0, 1, attack)
        fade = int(0.15 * sample_rate)
        if n_samples > fade:
            envelope[-fade:] = np.linspace(1, 0, fade)
        
        wave = wave * envelope * vol
        audio = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((audio, audio))
        
        try:
            return pygame.mixer.Sound(buffer=stereo.tobytes())
        except Exception as e:
            return None
    
    def _generate_sounds(self):
        """预生成所有游戏音效"""
        print("[Audio] 正在生成音效...")
        
        # 出牌：清脆短音
        self.sounds["play_card"] = self._generate_tone(660, 0.12, 0.25, waveform="square")
        
        # 抽牌：滑动音
        self.sounds["draw"] = self._generate_tone(440, 0.08, 0.2)
        
        # 加灯：上升音
        self.sounds["lamp_up"] = self._generate_tone(523, 0.15, 0.3)
        # 备用：用和弦做更丰富的加灯效果
        self.sounds["lamp_up_alt"] = self._generate_chord([523, 659], 0.2, 0.25)
        
        # 减灯：下降低音
        self.sounds["lamp_down"] = self._generate_tone(330, 0.18, 0.3, waveform="sawtooth")
        
        # 奥秘触发：神秘颤音
        self.sounds["mystery"] = self._generate_chord([440, 554, 659], 0.3, 0.25)
        
        # 胜利：和弦上行
        self.sounds["victory"] = self._generate_chord([523, 659, 784], 0.6, 0.3)
        
        # 放入响应区：低沉确认音
        self.sounds["response_place"] = self._generate_tone(392, 0.15, 0.25)
        
        # 回合开始：提示音
        self.sounds["turn_start"] = self._generate_tone(880, 0.06, 0.15)
        
        # 按钮悬停：微弱tick
        self.sounds["hover"] = self._generate_tone(2000, 0.03, 0.08)
        
        # 错误/无效操作：低沉嘟
        self.sounds["error"] = self._generate_tone(150, 0.2, 0.25, waveform="square")
        
        count = sum(1 for v in self.sounds.values() if v is not None)
        print(f"[Audio] 音效生成完成: {count}/{len(self.sounds)}")
    
    def play(self, sound_name: str):
        """播放指定音效"""
        if not self.enabled or not self.mixer_available:
            return
        
        sound = self.sounds.get(sound_name)
        if sound:
            try:
                sound.set_volume(self.master_volume)
                sound.play()
            except Exception as e:
                print(f"[Audio] 播放失败 {sound_name}: {e}")
    
    def set_volume(self, volume: float):
        """设置主音量 0.0~1.0"""
        self.master_volume = max(0.0, min(1.0, volume))
    
    def toggle(self) -> bool:
        """开关音效，返回当前状态"""
        self.enabled = not self.enabled
        return self.enabled
    
    def stop_all(self):
        """停止所有音效"""
        if self.mixer_available:
            pygame.mixer.stop()
