# -*- coding: utf-8 -*-
"""
PVE配置：初始卡组和奖励池
"""
from ..cards.card_registry import get_card, list_all_cards


def get_pve_initial_deck() -> list:
    """获取PVE初始卡组（10张）"""
    deck = []
    # 聚光×2
    deck.extend([get_card("LL_01"), get_card("LL_01")])
    # 凝焰×1
    deck.append(get_card("LL_02"))
    # 焰心×1
    deck.append(get_card("LL_06"))
    # 明灭×1
    deck.append(get_card("LL_09"))
    # 蓄火×1
    deck.append(get_card("LL_07"))
    # 连焰×1
    deck.append(get_card("LL_12"))
    # 焰舞×1
    deck.append(get_card("LL_13"))
    # 传火×1
    deck.append(get_card("LL_10"))
    # 借光×1
    deck.append(get_card("LL_05"))
    return deck


PVE_REWARD_POOL = [
    # 燃灯者牌（即时+特殊，不含响应牌）
    "LL_03",  # 炽明
    "LL_04",  # 辉耀
    "LL_08",  # 回焰
    "LL_11",  # 引火
    "LL_14",  # 燃魂
    "LL_19",  # 焚天
    "LL_20",  # 焰盾
    # 灭灯者牌（PVE中改造后可用，不含响应牌）
    "EX_02",  # 深幽
    "EX_03",  # 余波
    "EX_05",  # 全灭
    "EX_07",  # 缚光
    "EX_09",  # 延熄
    "EX_12",  # 灭魂
]

PVE_RELICS = [
    "连火之心",
    "余烬之握",
    "窥焰之眼",
]
