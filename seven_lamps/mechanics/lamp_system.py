"""
Seven Lamps Card Game - Lamp & Position System
七灯卡牌对战系统 - 灯与位置系统
"""
from typing import Dict, List, Optional
from ..core.enums import PositionState
from ..core.constants import (
    MAX_LAMPS, MIN_LAMPS, POSITION_COUNT,
    ODD_POSITIONS, EVEN_POSITIONS
)


class LampSystem:
    """
    灯系统：管理玩家的灯数（燃灯者/灭灯者）和位置（守夜人）
    
    对燃灯者和灭灯者：只有简单的 lamp_count
    对守夜人：有 position_states[1-7] 每个位置亮/灭
    """
    
    def __init__(self):
        self.lamp_count: int = 0
        # 位置系统（仅守夜人使用，其他职业也能用但不影响胜负）
        self.position_states: Dict[int, PositionState] = {
            i: PositionState.EMPTY for i in range(1, POSITION_COUNT + 1)
        }
        # 记录亮起顺序（用于"最后亮起的奇数位"）
        self.light_order: List[int] = []
    
    # ============ 灯数操作 ============
    def set_lamps(self, value: int) -> int:
        """设置灯数（受上下限保护）"""
        old = self.lamp_count
        self.lamp_count = max(MIN_LAMPS, min(MAX_LAMPS, value))
        return self.lamp_count
    
    def add_lamps(self, amount: int) -> Dict:
        """增加灯数，返回操作日志"""
        old = self.lamp_count
        self.lamp_count = min(MAX_LAMPS, self.lamp_count + amount)
        gained = self.lamp_count - old
        return {
            "success": True,
            "old": old,
            "new": self.lamp_count,
            "gained": gained,
            "msg": f"灯数 {old} → {self.lamp_count} (+{gained})"
        }
    
    def reduce_lamps(self, amount: int) -> Dict:
        """减少灯数，返回操作日志"""
        old = self.lamp_count
        self.lamp_count = max(MIN_LAMPS, self.lamp_count - amount)
        lost = old - self.lamp_count
        return {
            "success": True,
            "old": old,
            "new": self.lamp_count,
            "lost": lost,
            "msg": f"灯数 {old} → {self.lamp_count} (-{lost})"
        }
    
    def get_lamp_count(self) -> int:
        return self.lamp_count
    
    # ============ 位置操作（守夜人） ============
    def light_position(self, pos: int) -> bool:
        """亮起指定位置，返回是否成功"""
        if pos < 1 or pos > POSITION_COUNT:
            return False
        if self.position_states[pos] == PositionState.LIT:
            return False  # 已有灯
        self.position_states[pos] = PositionState.LIT
        if pos not in self.light_order:
            self.light_order.append(pos)
        return True
    
    def extinguish_position(self, pos: int) -> bool:
        """熄灭指定位置"""
        if pos < 1 or pos > POSITION_COUNT:
            return False
        if self.position_states[pos] == PositionState.EMPTY:
            return False
        self.position_states[pos] = PositionState.EMPTY
        if pos in self.light_order:
            self.light_order.remove(pos)
        return True
    
    def move_position(self, from_pos: int, to_pos: int) -> bool:
        """移动灯位置"""
        if (self.position_states.get(from_pos) != PositionState.LIT or
            self.position_states.get(to_pos) != PositionState.EMPTY):
            return False
        self.extinguish_position(from_pos)
        self.light_position(to_pos)
        return True
    
    def swap_positions(self, pos1: int, pos2: int) -> bool:
        """交换两个位置状态"""
        if pos1 < 1 or pos1 > POSITION_COUNT or pos2 < 1 or pos2 > POSITION_COUNT:
            return False
        s1, s2 = self.position_states[pos1], self.position_states[pos2]
        self.position_states[pos1] = s2
        self.position_states[pos2] = s1
        # 更新亮起顺序
        if s1 == PositionState.LIT and pos2 not in self.light_order:
            self.light_order.append(pos2)
        if s2 == PositionState.LIT and pos1 not in self.light_order:
            self.light_order.append(pos1)
        return True
    
    def get_last_lit_odd(self) -> Optional[int]:
        """获取最后亮起的奇数位"""
        for pos in reversed(self.light_order):
            if pos in ODD_POSITIONS:
                return pos
        return None
    
    def count_odd_lit(self) -> int:
        """亮起奇数位的数量"""
        return sum(1 for p in ODD_POSITIONS if self.position_states[p] == PositionState.LIT)
    
    def count_even_lit(self) -> int:
        """亮起偶数位的数量"""
        return sum(1 for p in EVEN_POSITIONS if self.position_states[p] == PositionState.LIT)
    
    def count_total_lit(self) -> int:
        """总亮起位置数"""
        return sum(1 for p in range(1, POSITION_COUNT + 1) 
                   if self.position_states[p] == PositionState.LIT)
    
    def all_odd_lit(self) -> bool:
        """所有奇数位是否全亮（守夜人胜利条件）"""
        return all(self.position_states[p] == PositionState.LIT for p in ODD_POSITIONS)
    
    def get_empty_odd_positions(self) -> List[int]:
        """获取空的奇数位"""
        return [p for p in ODD_POSITIONS if self.position_states[p] == PositionState.EMPTY]
    
    def get_lit_even_positions(self) -> List[int]:
        """获取亮起的偶数位"""
        return [p for p in EVEN_POSITIONS if self.position_states[p] == PositionState.LIT]
    
    def to_dict(self) -> Dict:
        """序列化"""
        return {
            "lamp_count": self.lamp_count,
            "positions": {str(k): v.name for k, v in self.position_states.items()},
            "light_order": self.light_order,
            "odd_lit": self.count_odd_lit(),
            "even_lit": self.count_even_lit(),
        }
