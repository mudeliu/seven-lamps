"""
Seven Lamps Card Game - Win Condition Checker
七灯卡牌对战系统 - 胜负判定系统
"""
from typing import Dict, Optional
from ..core.enums import ClassType
from ..core.constants import (
    MAX_LAMPS, EXTINGUISHER_WIN_CONSECUTIVE, FATIGUE_LAMP_BONUS
)


class WinChecker:
    """
    胜负判定器：检查是否满足胜利条件
    
    三职业胜利条件：
    - 燃灯者：灯数 = 7
    - 守夜人：奇数位(1/3/5/7)全部亮起
    - 灭灯者：敌方连续2回合结束时灯数 ≤ 2
    """
    
    def __init__(self):
        pass
    
    def check_victory(self, game_state, player_id: str) -> Dict:
        """
        检查指定玩家是否获胜
        返回 {"won": bool, "reason": str, "by_class": ClassType}
        """
        player = game_state.players[player_id]
        class_type = player.class_type
        
        if class_type == ClassType.LAMPLIGHTER:
            return self._check_lamplighter(game_state, player_id)
        elif class_type == ClassType.NIGHTWATCH:
            return self._check_nightwatch(game_state, player_id)
        elif class_type == ClassType.EXTINGUISHER:
            return self._check_extinguisher(game_state, player_id)
        
        return {"won": False, "reason": "", "by_class": None}
    
    def _check_lamplighter(self, game_state, player_id: str) -> Dict:
        """燃灯者：灯数 = 7"""
        lamps = game_state.get_lamps(player_id)
        if lamps >= MAX_LAMPS:
            return {
                "won": True,
                "reason": f"燃灯者 [{game_state.players[player_id].name}] 灯数达到 {MAX_LAMPS}！",
                "by_class": ClassType.LAMPLIGHTER
            }
        return {"won": False, "reason": "", "by_class": None}
    
    def _check_nightwatch(self, game_state, player_id: str) -> Dict:
        """守夜人：奇数位全部亮起"""
        lamp_sys = game_state.players[player_id].lamp_system
        if lamp_sys.all_odd_lit():
            return {
                "won": True,
                "reason": f"守夜人 [{game_state.players[player_id].name}] 奇数位(1/3/5/7)全部亮起！",
                "by_class": ClassType.NIGHTWATCH
            }
        return {"won": False, "reason": "", "by_class": None}
    
    def _check_extinguisher(self, game_state, player_id: str) -> Dict:
        """
        灭灯者：敌方连续2回合结束时灯数 ≤ 2
        计数逻辑：在回合结束时检查敌方灯数
        """
        opponent = game_state.get_opponent(player_id)
        opp_id = opponent.player_id
        
        # 获取灭灯者对敌方的连续压制计数
        consecutive_count = game_state.extinguisher_counters.get(opp_id, 0)
        
        if consecutive_count >= EXTINGUISHER_WIN_CONSECUTIVE:
            return {
                "won": True,
                "reason": f"灭灯者 [{game_state.players[player_id].name}] 成功压制敌方连续 {consecutive_count} 回合灯数≤2！",
                "by_class": ClassType.EXTINGUISHER
            }
        return {"won": False, "reason": "", "by_class": None}
    
    def check_draw(self, game_state) -> bool:
        """检查是否平局（双方同时满足条件，后手胜）"""
        # 实际上规则说后手胜，所以不算真正的平局
        # 这里只是检查是否同时触发
        p1, p2 = game_state.player_ids
        r1 = self.check_victory(game_state, p1)
        r2 = self.check_victory(game_state, p2)
        return r1["won"] and r2["won"]
    
    def resolve_winner(self, game_state) -> Optional[str]:
        """
        判定最终获胜者
        若双方同时满足，后手方获胜
        返回玩家ID或None
        """
        p1, p2 = game_state.player_ids
        
        # 先手检查
        r1 = self.check_victory(game_state, p1)
        if r1["won"] and not self.check_victory(game_state, p2)["won"]:
            return p1
        
        # 后手检查（后手同时满足也胜）
        r2 = self.check_victory(game_state, p2)
        if r2["won"]:
            return p2
        
        return None
    
    def update_extinguisher_counter(self, game_state, player_id: str):
        """
        更新灭灯者胜利计数（在回合结束时调用）
        如果敌方灯数 ≤ 2，计数+1；否则清零
        """
        opponent = game_state.get_opponent(player_id)
        opp_id = opponent.player_id
        opp_lamps = game_state.get_lamps(opp_id)
        
        # 只有灭灯者需要更新计数
        if game_state.players[player_id].class_type != ClassType.EXTINGUISHER:
            return
        
        if opp_lamps <= 2:
            game_state.extinguisher_counters[opp_id] = \
                game_state.extinguisher_counters.get(opp_id, 0) + 1
        else:
            game_state.extinguisher_counters[opp_id] = 0
    
    def apply_fatigue(self, game_state) -> Dict:
        """
        应用疲劳规则：第7回合结束未分胜负，双方各+2灯
        """
        result = {"applied": True, "changes": []}
        for pid in game_state.player_ids:
            old = game_state.get_lamps(pid)
            game_state.players[pid].lamp_system.add_lamps(FATIGUE_LAMP_BONUS)
            new = game_state.get_lamps(pid)
            result["changes"].append({
                "player": pid,
                "old": old,
                "new": new,
                "msg": f"疲劳：灯数 {old} → {new}"
            })
        return result
