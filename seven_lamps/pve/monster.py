# -*- coding: utf-8 -*-
"""
PVE怪物系统
"""
from typing import Optional, Dict, List
from enum import Enum


class IntentType(Enum):
    """怪物意图类型"""
    ATTACK = "attack"
    CHARGE = "charge"
    SEAL = "seal"
    SHIELD = "shield"
    DISRUPT = "disrupt"


class Monster:
    """PVE怪物基类"""

    def __init__(self, name: str, max_hp: int, lamp_growth: int = 1,
                 script=None, special_rules=None):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.lamp_count = 0
        self.lamp_growth = lamp_growth  # 每回合灯数增长
        self.turn_count = 0
        self.intent: Optional[IntentType] = None
        self.intent_value = 0  # 意图参数（如攻击伤害值）
        self.is_enraged = False
        self.script = script or []
        self.special_rules = special_rules or {}
        self.shield = 0  # 护盾层数
        self.seal_type = None  # 封印类型
        self.stage = 1  # Boss多阶段

    def reset(self):
        """重置怪物状态"""
        self.hp = self.max_hp
        self.lamp_count = 0
        self.turn_count = 0
        self.intent = None
        self.intent_value = 0
        self.is_enraged = False
        self.shield = 0
        self.seal_type = None
        self.stage = 1

    def decide_intent(self, player_lamps: int, player_hand_size: int):
        """决定下回合意图"""
        self.turn_count += 1

        # 狂暴中：强制攻击，攻击力翻倍
        if self.is_enraged:
            self.intent = IntentType.ATTACK
            self.intent_value = self.lamp_count * 2
            return

        # 灯数<3：只能普通攻击
        if self.lamp_count < 3:
            self.intent = IntentType.ATTACK
            self.intent_value = self.lamp_count
            return

        # 使用脚本决定意图
        if self.script:
            entry = self.script[(self.turn_count - 1) % len(self.script)]
            self.intent = entry.get("intent", IntentType.ATTACK)
            self.intent_value = entry.get("value", self.lamp_count)
        else:
            self.intent = IntentType.ATTACK
            self.intent_value = self.lamp_count

    def execute_intent(self, player) -> Dict:
        """执行当前意图，返回结果描述"""
        result = {"intent": self.intent.value, "msg": ""}

        if self.intent == IntentType.ATTACK:
            # 攻击力随灯数递增：1~2=灯数，3~4=灯数+1，5~6=灯数+2，7=×2
            base = self.lamp_count
            if self.lamp_count >= 7:
                damage = base * 2
            elif self.lamp_count >= 5:
                damage = base + 2
            elif self.lamp_count >= 3:
                damage = base + 1
            else:
                damage = base
            actual = player.take_damage(damage)
            result["msg"] = f"{self.name}攻击，造成{actual}点伤害"
            result["damage"] = actual

        elif self.intent == IntentType.CHARGE:
            self.lamp_count += self.intent_value
            result["msg"] = f"{self.name}蓄力，灯数+{self.intent_value}"

        elif self.intent == IntentType.SHIELD:
            self.shield += 1
            result["msg"] = f"{self.name}获得护盾"

        elif self.intent == IntentType.SEAL:
            self.seal_type = "instant"  # 封印即时牌
            result["msg"] = f"{self.name}封印你下回合的即时牌"

        elif self.intent == IntentType.DISRUPT:
            result["msg"] = f"{self.name}试图干扰你的手牌"
            result["discard"] = 1

        # 狂暴结束后重置
        if self.is_enraged:
            self.is_enraged = False
            self.lamp_count = 3

        # 回合结束灯数增长
        if not self.is_enraged:
            self.lamp_count += self.lamp_growth

        # 检查是否达到7灯狂暴
        if self.lamp_count >= 7:
            self.is_enraged = True
            self.lamp_count = 7
            result["enrage"] = True
            result["msg"] += f" | {self.name}进入狂暴状态！"

        return result

    def take_damage(self, damage: int) -> int:
        """受到攻击，返回实际扣除的耐久"""
        # 先扣护盾
        if self.shield > 0:
            self.shield -= 1
            return 0  # 护盾抵消了伤害

        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        return damage

    def reduce_lamp(self, amount: int):
        """减少灯数（被玩家控制）"""
        self.lamp_count -= amount
        if self.lamp_count < 0:
            self.lamp_count = 0

    def is_dead(self) -> bool:
        return self.hp <= 0

    def __repr__(self):
        return f"Monster({self.name}, HP={self.hp}/{self.max_hp}, Lamp={self.lamp_count})"


# ====== 5关怪物定义 ======

def create_monster(level: int) -> Monster:
    """根据关卡创建怪物"""
    if level == 1:
        return Monster(
            name="灰烬幼灵",
            max_hp=20,
            lamp_growth=1,
            script=[
                {"intent": IntentType.ATTACK, "value": 1},
            ]
        )
    elif level == 2:
        return Monster(
            name="蚀光蝠",
            max_hp=30,
            lamp_growth=1,
            script=[
                {"intent": IntentType.ATTACK, "value": 1},
                {"intent": IntentType.ATTACK, "value": 1},
                {"intent": IntentType.CHARGE, "value": 1},
            ]
        )
    elif level == 3:
        return Monster(
            name="缚光守卫",
            max_hp=45,
            lamp_growth=1,
            script=[
                {"intent": IntentType.SHIELD},
                {"intent": IntentType.ATTACK, "value": 2},
                {"intent": IntentType.SHIELD},
                {"intent": IntentType.ATTACK, "value": 3},
            ]
        )
    elif level == 4:
        return Monster(
            name="延熄猎手",
            max_hp=60,
            lamp_growth=1,
            script=[
                {"intent": IntentType.ATTACK, "value": 2},
                {"intent": IntentType.CHARGE, "value": 1},
                {"intent": IntentType.SEAL},
                {"intent": IntentType.ATTACK, "value": 3},
            ]
        )
    elif level == 5:
        return Monster(
            name="灭灯之主",
            max_hp=80,
            lamp_growth=1,
            script=[
                {"intent": IntentType.ATTACK, "value": 2},
                {"intent": IntentType.CHARGE, "value": 1},
                {"intent": IntentType.ATTACK, "value": 3},
                {"intent": IntentType.SEAL},
                {"intent": IntentType.ATTACK, "value": 4},
            ]
        )
    else:
        raise ValueError(f"Unknown level: {level}")
