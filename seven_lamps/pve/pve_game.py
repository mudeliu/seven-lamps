# -*- coding: utf-8 -*-
"""
PVE游戏核心循环
"""
import random
import re
from typing import List, Dict, Optional, Tuple
from .monster import Monster, create_monster, IntentType


class PVEPlayerState:
    """PVE玩家状态（简化版，不依赖Player类）"""

    def __init__(self, deck: List, hp: int = 20, lamps: int = 1):
        self.hp = hp
        self.max_hp = hp
        self.lamps = lamps
        self.max_lamps = 7
        self.hand: List = []
        self.deck: List = deck[:]
        self.discard: List = []
        self.statuses: Dict[str, any] = {}
        self.cards_played_this_turn = 0
        self.max_cards_per_turn = 1  # 默认1张，根据关卡调整
        self.hand_limit = 7
        self.draw_count = 3
        self.con_flame_bonus = 0  # 凝焰延迟收益标记

    def shuffle_deck(self):
        """洗牌"""
        random.shuffle(self.deck)

    def draw(self, count: int) -> int:
        """抽指定数量的牌，返回实际抽到的数量"""
        drawn = 0
        for _ in range(count):
            if len(self.hand) >= self.hand_limit:
                break
            if not self.deck:
                # 牌库空了，弃牌堆洗牌
                if not self.discard:
                    break
                self.deck = self.discard[:]
                self.discard = []
                random.shuffle(self.deck)
            if self.deck:
                card = self.deck.pop(0)
                self.hand.append(card)
                drawn += 1
        return drawn

    def discard_hand(self):
        """回合结束弃掉所有手牌"""
        self.discard.extend(self.hand)
        self.hand = []

    def add_lamps(self, amount: int):
        """增加灯数"""
        self.lamps = min(self.max_lamps, self.lamps + amount)

    def reduce_lamps(self, amount: int):
        """减少灯数"""
        self.lamps = max(0, self.lamps - amount)

    def take_damage(self, damage: int) -> int:
        """受到伤害，返回实际伤害"""
        # 检查脆弱状态
        if self.statuses.get("vulnerable", 0) > 0:
            damage += self.statuses["vulnerable"]
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        return damage

    def heal(self, amount: int):
        """回复生命"""
        self.hp = min(self.max_hp, self.hp + amount)

    def is_alive(self) -> bool:
        return self.hp > 0


class PVEGame:
    """PVE推关游戏主类"""

    def __init__(self, level: int, deck: List, relic: Optional[str] = None):
        self.level = level
        self.monster = create_monster(level)
        self.player = PVEPlayerState(deck)
        self.player.max_cards_per_turn = 2 if level >= 3 else 1  # 1~2关1张，3关起2张
        self.relic = relic
        self.turn = 1
        self.game_over = False
        self.victory = False
        self.message = ""
        self.action_history: List[str] = []
        self.last_played_card = None  # 用于引火复制

        # 初始抽牌
        self.player.shuffle_deck()
        self._start_new_turn()

    # ========== 回合流程 ==========

    def _start_new_turn(self):
        """开始新回合"""
        self.player.cards_played_this_turn = 0
        self.message = f"第 {self.turn} 回合"

        # 应用玩家状态：下回合抽牌加成
        bonus_draw = self.player.statuses.pop("next_turn_draw", 0)
        draw_count = self.player.draw_count + bonus_draw

        # 应用遗物：窥焰之眼
        if self.relic == "窥焰之眼":
            draw_count += 1

        # 抽牌
        drawn = self.player.draw(draw_count)
        if drawn > 0:
            self.message += f" | 抽了 {drawn} 张牌"

        # 应用怪物DOT
        dot = self.player.statuses.pop("monster_dot", (0, 0))
        if dot[1] > 0:  # (伤害值, 剩余回合)
            self.monster.reduce_lamp(dot[0])
            self.monster.take_damage(dot[0])  # DOT同时扣耐久
            dot = (dot[0], dot[1] - 1)
            if dot[1] > 0:
                self.player.statuses["monster_dot"] = dot
            self.message += f" | 怪物受到{dot[0]}点持续伤害"

        # 应用凝焰延迟收益
        if self.player.con_flame_bonus > 0:
            # 检查灯数是否>=上回合开始时的灯数
            # 简化：只要灯数>0就给+1
            self.player.add_lamps(1)
            self.player.con_flame_bonus = 0
            self.message += " | 凝焰延迟收益+1灯"

        # 怪物决定意图
        self.monster.decide_intent(self.player.lamps, len(self.player.hand))

        # 检查封印：如果玩家有seal_monster状态，怪物意图改为攻击
        if self.player.statuses.pop("seal_monster", False):
            self.monster.intent = IntentType.ATTACK
            self.monster.intent_value = self.monster.lamp_count

    def play_card(self, card_idx: int) -> Dict:
        """玩家出牌，返回结果"""
        result = {"success": False, "msg": "", "ouch_damage": 0, "enrage": False}

        if self.game_over:
            result["msg"] = "游戏已结束"
            return result

        if self.player.cards_played_this_turn >= self.player.max_cards_per_turn:
            result["msg"] = "本回合已用完出牌次数"
            return result

        if card_idx < 0 or card_idx >= len(self.player.hand):
            result["msg"] = "无效手牌索引"
            return result

        card = self.player.hand[card_idx]

        # 检查门槛
        if not self._check_threshold(card):
            result["msg"] = f"不满足门槛: {card.threshold_desc}"
            return result

        # 检查封印
        if self.monster.seal_type == "instant" and card.card_type.value == "即时":
            result["msg"] = "本回合即时牌被封印"
            return result

        # 执行卡牌效果
        self._execute_card_effect(card)

        # 计算对怪物的基础伤害 = 玩家当前灯数
        base_damage = self.player.lamps

        # 状态加成
        bonus = self.player.statuses.pop("this_turn_next_card", 0)
        bonus += self.player.statuses.get("next_turn_damage", 0)  # 下回合加成不在本回合用

        # 遗物加成：连火之心（第2张牌）
        if self.relic == "连火之心" and self.player.cards_played_this_turn == 1:
            bonus += 1

        # 燃魂脆弱
        vuln = self.player.statuses.get("vulnerable", 0)

        total_damage = base_damage + bonus

        # 对怪物造成伤害
        actual_dmg = self.monster.take_damage(total_damage)

        # 深幽额外减怪物灯数（已在_execute_card_effect中处理）
        # 但深幽的状态（下回合怪物增长-1）需要记录
        if card.id == "EX_02":
            self.player.statuses["monster_growth_reduction"] = \
                self.player.statuses.get("monster_growth_reduction", 0) + 1

        # 记录出牌
        self.player.cards_played_this_turn += 1
        self.player.discard.append(card)
        self.player.hand.pop(card_idx)
        self.last_played_card = card

        # 消息
        result["msg"] = f"打出 [{card.name}]，对{self.monster.name}造成{actual_dmg}伤害"
        if bonus > 0:
            result["msg"] += f"(含状态加成{bonus})"
        if vuln > 0:
            result["msg"] += f"[脆弱]下回合受到伤害+{vuln}"

        # 检查7灯奥义
        if self.player.lamps >= 7:
            ouch_bonus = 10
            # 辉耀加成
            if card.id == "LL_04":
                ouch_bonus += 3
            ouch_dmg = self.monster.take_damage(ouch_bonus)
            self.player.lamps = 3
            result["ouch_damage"] = ouch_dmg
            result["msg"] += f" | ★七灯奥义！额外{ouch_dmg}伤害！"
            result["enrage"] = True

        # 检查怪物死亡
        if self.monster.is_dead():
            self.game_over = True
            self.victory = True
            result["msg"] += f" | {self.monster.name}被击败！"
            return result

        # 检查是否出完2张牌，是则自动结束回合
        if self.player.cards_played_this_turn >= self.player.max_cards_per_turn:
            self._end_turn()
            # 回合结束后检查玩家死亡
            if self.game_over:
                result["msg"] += " | 你被击败了..."
            return result

        result["success"] = True
        return result

    def _execute_card_effect(self, card):
        """执行卡牌效果（简化版，基于effect_desc解析）"""
        desc = card.effect_desc

        # 自己+灯
        match = re.search(r'自己\+(\d+)', desc)
        if match:
            self.player.add_lamps(int(match.group(1)))

        # 怪物-灯
        match = re.search(r'(?:敌方|怪物)-(\d+)', desc)
        if match:
            self.monster.reduce_lamp(int(match.group(1)))

        # 抽牌
        match = re.search(r'抽(\d+)张?', desc)
        if match:
            self.player.draw(int(match.group(1)))

        # 特殊牌处理
        if card.id == "LL_02":  # 凝焰
            self.player.con_flame_bonus = 1  # 标记延迟收益

        if card.id == "LL_05":  # 借光：PVE中无副作用，自己+2
            self.player.add_lamps(2)

        if card.id == "LL_06":  # 焰心
            self.player.statuses["next_turn_draw"] = \
                self.player.statuses.get("next_turn_draw", 0) + 1

        if card.id == "LL_07":  # 蓄火
            self.player.statuses["next_turn_damage"] = \
                self.player.statuses.get("next_turn_damage", 0) + 2

        if card.id == "LL_09":  # 明灭：AI自动选择自己+1
            self.player.add_lamps(1)

        if card.id == "LL_11":  # 引火：复制上回合牌的状态
            if self.last_played_card:
                self._copy_status(self.last_played_card)

        if card.id == "LL_12":  # 连焰
            self.player.statuses["next_turn_damage"] = \
                self.player.statuses.get("next_turn_damage", 0) + 1

        if card.id == "LL_13":  # 焰舞
            self.player.statuses["this_turn_next_card"] = \
                self.player.statuses.get("this_turn_next_card", 0) + 2

        if card.id == "LL_14":  # 燃魂
            self.player.statuses["next_turn_damage"] = \
                self.player.statuses.get("next_turn_damage", 0) + 3
            self.player.statuses["vulnerable"] = \
                self.player.statuses.get("vulnerable", 0) + 1

        if card.id == "LL_15":  # 护焰：PVE中抵消下一次伤害
            self.player.statuses["block_next"] = 1

        if card.id == "EX_02":  # 深幽
            self.player.statuses["monster_growth_reduction"] = \
                self.player.statuses.get("monster_growth_reduction", 0) + 1

        if card.id == "EX_03":  # 余波
            self.player.statuses["monster_dot"] = (1, 2)  # (伤害, 回合)

        if card.id == "EX_09":  # 延熄
            self.player.statuses["seal_monster"] = True

        if card.id == "EX_11":  # 晦明
            self.player.statuses["seal_monster"] = True

    def _copy_status(self, card):
        """引火：复制上回合牌的状态效果"""
        status_map = {
            "LL_01": ("next_turn_damage", 1),
            "LL_03": ("next_turn_damage", 2),
            "LL_07": ("next_turn_damage", 2),
            "LL_12": ("next_turn_damage", 1),
            "LL_13": ("this_turn_next_card", 2),
            "LL_14": ("next_turn_damage", 3),
        }
        if card.id in status_map:
            key, val = status_map[card.id]
            self.player.statuses[key] = self.player.statuses.get(key, 0) + val

    def _check_threshold(self, card) -> bool:
        """检查门槛"""
        desc = card.threshold_desc
        lamps = self.player.lamps

        if not desc or desc == "—":
            return True

        # ≥X
        match = re.search(r'≥(\d+)', desc)
        if match:
            return lamps >= int(match.group(1))

        # ≤X
        match = re.search(r'≤(\d+)', desc)
        if match:
            return lamps <= int(match.group(1))

        # =X
        match = re.search(r'=(\d+)', desc)
        if match:
            return lamps == int(match.group(1))

        # 己方<敌方 / 己方灯数<怪物灯数
        if "己方" in desc and "敌方" in desc or "怪物" in desc:
            return lamps < self.monster.lamp_count

        return True

    def end_turn(self):
        """玩家主动结束回合"""
        if self.game_over:
            return
        self._end_turn()

    def _end_turn(self):
        """结束回合，怪物行动"""
        # 怪物执行意图
        result = self.monster.execute_intent(self.player)
        self.message = result.get("msg", "")

        # 处理延熄封印：怪物下回合封印在execute_intent中已清除
        self.monster.seal_type = None

        # 处理玩家block_next（护焰）
        if self.player.statuses.get("block_next", 0) > 0:
            if result.get("damage", 0) > 0:
                self.player.statuses["block_next"] = 0
                self.message += " | 护焰抵消了伤害！"

        # 检查玩家死亡
        if not self.player.is_alive():
            self.game_over = True
            self.victory = False
            self.message += " | 你被击败了..."
            return

        # 进入下一回合
        self.turn += 1

        # 清理本回合状态
        self.player.statuses.pop("this_turn_next_card", 0)
        self.player.statuses.pop("vulnerable", 0)

        # 回合结束弃掉所有手牌（杀戮尖塔式）
        self.player.discard_hand()

        self._start_new_turn()

    def get_state_dict(self) -> Dict:
        """获取游戏状态字典（供UI使用）"""
        return {
            "turn": self.turn,
            "player_hp": self.player.hp,
            "player_max_hp": self.player.max_hp,
            "player_lamps": self.player.lamps,
            "hand_size": len(self.player.hand),
            "deck_size": len(self.player.deck),
            "discard_size": len(self.player.discard),
            "cards_played": self.player.cards_played_this_turn,
            "max_cards": self.player.max_cards_per_turn,
            "monster_name": self.monster.name,
            "monster_hp": self.monster.hp,
            "monster_max_hp": self.monster.max_hp,
            "monster_lamps": self.monster.lamp_count,
            "monster_intent": self.monster.intent.value if self.monster.intent else "",
            "monster_intent_value": self.monster.intent_value,
            "monster_shield": self.monster.shield,
            "monster_enraged": self.monster.is_enraged,
            "game_over": self.game_over,
            "victory": self.victory,
            "message": self.message,
            "statuses": dict(self.player.statuses),
        }
