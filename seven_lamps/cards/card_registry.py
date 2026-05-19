"""
Seven Lamps Card Game - Complete Card Registry
七灯卡牌对战系统 - 完整牌库注册表

共60张牌，3职业 × 20张 = 60张
"""
from typing import Dict, List
from .card_base import Card
from ..core.enums import ClassType, CardType, CardCategory

# ======== 辅助函数 ========
def _lamp_check(game_state, player, cond_str: str) -> bool:
    """解析门槛字符串并判断"""
    lamps = game_state.get_lamps(player)
    try:
        if cond_str.startswith("≥"):
            return lamps >= int(cond_str[1:])
        elif cond_str.startswith("≤"):
            return lamps <= int(cond_str[1:])
        elif cond_str.startswith("="):
            return lamps == int(cond_str[1:])
        elif cond_str.startswith(">"):
            return lamps > int(cond_str[1:])
        elif cond_str.startswith("<"):
            return lamps < int(cond_str[1:])
    except:
        pass
    return True


def _opp_lamp_check(game_state, player, cond_str: str) -> bool:
    """解析敌方门槛字符串"""
    opp = game_state.get_opponent(player)
    return _lamp_check(game_state, opp.player_id, cond_str.replace("敌方", ""))


def _relative_check(game_state, player, cond_str: str) -> bool:
    """解析相对条件（己方<敌方等）"""
    lamps = game_state.get_lamps(player)
    opp = game_state.get_opponent(player)
    opp_lamps = game_state.get_lamps(opp.player_id)
    if cond_str == "己方<敌方":
        return lamps < opp_lamps
    return True


# ======== 燃灯者 - 20张 ========
def make_lamplighter_cards() -> List[Card]:
    """燃灯者牌库：积累6 + 反击4 + 组合4 + 奥秘4 + 特殊2"""
    cards = []
    
    # ---- 积累牌（6张）----
    cards.append(Card(
        id="LL_01", name="聚光", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.ACCUMULATION,
        threshold_desc="≥1", effect_desc="自己+1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥1"),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 1),  # 基础积累牌，门槛最低，+1
        tags=["基础", "积累"]
    ))
    cards.append(Card(
        id="LL_02", name="凝焰", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.ACCUMULATION,
        threshold_desc="≥2", effect_desc="自己+1；若下回合结束时灯数≥本回合开始，再+1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 1), **{"next_turn_bonus": True, "bonus_lamps": 1}},
        tags=["积累", "延迟收益"]
    ))
    cards.append(Card(
        id="LL_03", name="炽明", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.ACCUMULATION,
        threshold_desc="≥4", effect_desc="自己+3",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥4"),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 3),
        tags=["积累", "核心", "中期"]
    ))
    cards.append(Card(
        id="LL_04", name="辉耀", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.ACCUMULATION,
        threshold_desc="=6", effect_desc="自己+1（6→7斩杀）",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "=6"),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 1),
        tags=["斩杀", "积累"]
    ))
    cards.append(Card(
        id="LL_05", name="借光", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.ACCUMULATION,
        threshold_desc="≥3", effect_desc="双方各+1，自己再+1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥3"),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 2, from_borrow=True),  # 双方+1，自己再+1
        tags=["积累", "双方收益"]
    ))
    cards.append(Card(
        id="LL_06", name="焰心", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.ACCUMULATION,
        threshold_desc="≥2", effect_desc="自己+1，抽1张",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 1), **gs.draw_cards(c, 1)},
        tags=["积累", "过牌"]
    ))
    
    # ---- 反击牌（4张）----
    cards.append(Card(
        id="LL_07", name="蓄火", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.COUNTER,
        threshold_desc="≤2", effect_desc="自己+3",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≤2"),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 3),
        tags=["绝境", "反击"]
    ))
    cards.append(Card(
        id="LL_08", name="回焰", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.COUNTER,
        threshold_desc="≤2", effect_desc="自己+1；若本回合被减过灯，再+2",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≤2"),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 3 if gs.was_reduced_this_turn(c) else 1),
        tags=["绝境", "报复"]
    ))
    cards.append(Card(
        id="LL_09", name="明灭", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.COUNTER,
        threshold_desc="≥1", effect_desc="选择：自己+1 或 敌方-1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥1"),
        effect_fn=lambda gs, c, t: gs.resolve_choice(c, "ming_mie"),  # UI选择
        tags=["灵活", "反击"]
    ))
    cards.append(Card(
        id="LL_10", name="传火", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.COUNTER,
        threshold_desc="己方<敌方", effect_desc="自己+2；若己方<敌方，额外+1",
        threshold_fn=lambda gs, p: _relative_check(gs, p, "己方<敌方"),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 3),
        tags=["追赶", "反击"]
    ))
    
    # ---- 组合牌（4张）----
    cards.append(Card(
        id="LL_11", name="引火", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.COMBO,
        threshold_desc="≥3", effect_desc="复制上回合打出的牌的效果",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥3"),
        effect_fn=lambda gs, c, t: gs.copy_last_turn_effect(c),
        tags=["组合", "核心", "复制"]
    ))
    cards.append(Card(
        id="LL_12", name="连焰", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.COMBO,
        threshold_desc="≥2", effect_desc="自己+1；若上回合也出了增灯牌，再+1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 2 if gs.played_lamp_increase_last_turn(c) else 1),
        tags=["组合", "连续奖励"]
    ))
    cards.append(Card(
        id="LL_13", name="焰舞", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.COMBO,
        threshold_desc="=3", effect_desc="自己+1；下回合第一张牌效果+1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "=3"),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 1), "next_first_card_bonus": 1},
        tags=["组合", "铺垫"]
    ))
    cards.append(Card(
        id="LL_14", name="燃魂", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.INSTANT, category=CardCategory.COMBO,
        threshold_desc="=5", effect_desc="自己+3；下回合只能出1张",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "=5"),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 3), "next_turn_card_limit": 1},
        tags=["高风险", "爆发"]
    ))
    
    # ---- 奥秘/响应牌（4张）----
    cards.append(Card(
        id="LL_15", name="护焰", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方打出减少你灯数的牌时", effect_desc="取消效果，你+1",
        trigger_fn=lambda gs, owner, action, card: card is not None and any(kw in card.effect_desc for kw in ["敌方", "对手"]) and any(kw in card.effect_desc for kw in ["-1", "-2", "-3", "减", "熄"]),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 1),
        tags=["防御", "奥秘", "核心"]
    ))
    cards.append(Card(
        id="LL_16", name="反噬", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方打出减少你灯数的牌时", effect_desc="效果反转：敌方自己承受减灯效果",
        trigger_fn=lambda gs, owner, action, card: card is not None and any(kw in card.effect_desc for kw in ["敌方", "对手"]) and any(kw in card.effect_desc for kw in ["-1", "-2", "-3", "减", "熄"]),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 1), **gs.reduce_lamps(t, 1)},  # 简化：owner+1抵消减灯, opponent-1
        tags=["防御", "奥秘", "威慑"]
    ))
    cards.append(Card(
        id="LL_17", name="夺光", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方打出增加自身灯数的牌时", effect_desc="效果改为你获得",
        trigger_fn=lambda gs, owner, action, card: card is not None and any(kw in card.effect_desc for kw in ["自己+", "自己 +"]),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 1), **gs.reduce_lamps(t, 1)},  # 简化：owner+1, opponent-1
        tags=["进攻", "奥秘", "截胡"]
    ))
    cards.append(Card(
        id="LL_18", name="预警", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方灯数达到5时", effect_desc="敌方本回合不能打出增加灯数的牌",
        trigger_fn=lambda gs, owner, action, card: card is not None and any(kw in card.effect_desc for kw in ["自己+", "自己 +"]),
        effect_fn=lambda gs, c, t: {"lock_lamp_increase": True},
        tags=["封锁", "奥秘"]
    ))
    
    # ---- 特殊牌（2张）----
    cards.append(Card(
        id="LL_19", name="焚天", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="=6", effect_desc="自己+1；若因此=7直接获胜（跳过敌方响应）",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "=6"),
        effect_fn=lambda gs, c, t: gs.add_lamps(c, 1),
        is_breakthrough=True,
        tags=["斩杀", "无敌", "特殊"]
    ))
    cards.append(Card(
        id="LL_20", name="焰盾", class_type=ClassType.LAMPLIGHTER,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="≥2", effect_desc="自己+1；下回合免疫敌方减灯",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 1), "immune_reduce_next_turn": True},
        tags=["防御", "特殊"]
    ))
    
    return cards


# ======== 守夜人 - 20张 ========
def make_nightwatch_cards() -> List[Card]:
    """守夜人牌库：填充6 + 操控6 + 奥秘4 + 特殊4"""
    cards = []
    
    # ---- 填充牌（6张）----
    cards.append(Card(
        id="NW_01", name="守灯", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.FILL,
        threshold_desc="≥1", effect_desc="亮起编号最低的空奇数位；若无空位，+1灯",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥1"),
        effect_fn=lambda gs, c, t: gs.light_lowest_empty_odd(c),
        tags=["填充", "基础"]
    ))
    cards.append(Card(
        id="NW_02", name="固位", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.FILL,
        threshold_desc="≥2", effect_desc="亮起一个指定奇数位",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: gs.resolve_choice(c, "gu_wei"),
        tags=["填充", "精准"]
    ))
    cards.append(Card(
        id="NW_03", name="双守", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.FILL,
        threshold_desc="=3", effect_desc="亮起两个奇数位（优先编号最低）",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "=3"),
        effect_fn=lambda gs, c, t: gs.light_two_odd(c),
        tags=["填充", "高效"]
    ))
    cards.append(Card(
        id="NW_04", name="全明", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.FILL,
        threshold_desc="≥5", effect_desc="亮起所有空奇数位",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥5"),
        effect_fn=lambda gs, c, t: gs.light_all_empty_odd(c),
        tags=["填充", "爆发", "后期"]
    ))
    cards.append(Card(
        id="NW_05", name="补暗", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.FILL,
        threshold_desc="≥1", effect_desc="将一盏偶数位的灯移到最近的空奇数位",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥1"),
        effect_fn=lambda gs, c, t: gs.move_even_to_odd(c),
        tags=["填充", "转化"]
    ))
    cards.append(Card(
        id="NW_06", name="连灯", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.FILL,
        threshold_desc="≥2", effect_desc="亮起一个奇数位；若相邻奇位已亮则再亮一个",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: gs.light_odd_with_chain(c),
        tags=["填充", "连续"]
    ))
    
    # ---- 操控牌（6张）----
    cards.append(Card(
        id="NW_07", name="熄位", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.MANIPULATE,
        threshold_desc="≥2", effect_desc="熄灭敌方一个指定位置的灯",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: gs.resolve_choice(c, "xi_wei"),
        tags=["操控", "干扰"]
    ))
    cards.append(Card(
        id="NW_08", name="换位", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.MANIPULATE,
        threshold_desc="≥2", effect_desc="交换两个指定位置的状态",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: gs.resolve_choice(c, "huan_wei"),
        tags=["操控", "灵活"]
    ))
    cards.append(Card(
        id="NW_09", name="转位", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.MANIPULATE,
        threshold_desc="≥3", effect_desc="将敌方一盏灯移到编号±1的位置",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥3"),
        effect_fn=lambda gs, c, t: gs.resolve_choice(c, "zhuan_wei"),
        tags=["操控", "打乱"]
    ))
    cards.append(Card(
        id="NW_10", name="移灯", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.MANIPULATE,
        threshold_desc="≥2", effect_desc="将自己的一盏灯移到另一空位置",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: gs.resolve_choice(c, "yi_deng"),
        tags=["操控", "调整"]
    ))
    cards.append(Card(
        id="NW_11", name="散位", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.MANIPULATE,
        threshold_desc="≥3", effect_desc="将敌方一盏灯从奇数位移到偶数位",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥3"),
        effect_fn=lambda gs, c, t: gs.resolve_choice(c, "san_wei"),
        tags=["操控", "降级", "核心干扰"]
    ))
    cards.append(Card(
        id="NW_12", name="晦位", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.INSTANT, category=CardCategory.MANIPULATE,
        threshold_desc="≥2", effect_desc="熄灭敌方最后亮起的一个奇数位的灯",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: gs.extinguish_last_odd(c),
        tags=["操控", "精准"]
    ))
    
    # ---- 奥秘/响应牌（4张）----
    cards.append(Card(
        id="NW_13", name="守影", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方熄灭你的灯时", effect_desc="熄灭无效，且该位置亮起",
        trigger_fn=lambda gs, owner, action, card: card is not None and "熄" in card.effect_desc,
        effect_fn=lambda gs, c, t: gs.cancel_and_light(c),
        tags=["防御", "奥秘", "核心"]
    ))
    cards.append(Card(
        id="NW_14", name="引晦", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方亮起灯时", effect_desc="改为熄灭该位置的灯",
        trigger_fn=lambda gs, owner, action, card: card is not None and ("亮" in card.effect_desc or "亮起" in card.effect_desc),
        effect_fn=lambda gs, c, t: gs.reverse_to_extinguish(c),
        tags=["操控", "奥秘", "反制"]
    ))
    cards.append(Card(
        id="NW_15", name="护位", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方试图改变你的奇数位状态时", effect_desc="取消该效果",
        trigger_fn=lambda gs, owner, action, card: card is not None and any(kw in card.effect_desc for kw in ["位", "位置", "奇位", "偶位"]),
        effect_fn=lambda gs, c, t: {"cancel": True},
        tags=["防御", "奥秘"]
    ))
    cards.append(Card(
        id="NW_16", name="晦影", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方打出影响位置的牌时", effect_desc="该牌改为你亮起一个奇数位",
        trigger_fn=lambda gs, owner, action, card: card is not None and any(kw in card.effect_desc for kw in ["位", "位置", "奇位", "偶位"]),
        effect_fn=lambda gs, c, t: gs.light_lowest_empty_odd(c),
        tags=["转化", "奥秘", "化敌为友"]
    ))
    
    # ---- 特殊牌（4张）----
    cards.append(Card(
        id="NW_17", name="隐位", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="≤2", effect_desc="熄灭自己所有偶数位的灯；每熄一个亮一个奇位",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≤2"),
        effect_fn=lambda gs, c, t: gs.sacrifice_even_for_odd(c),
        tags=["特殊", "逆转", "绝境"]
    ))
    cards.append(Card(
        id="NW_18", name="位换", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="≥3", effect_desc="交换双方奇数位亮灯的数量",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥3"),
        effect_fn=lambda gs, c, t: gs.swap_odd_count(c),
        tags=["特殊", "逆转", "翻盘"]
    ))
    cards.append(Card(
        id="NW_19", name="定阵", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="≥4", effect_desc="①敌方奇位灯全移偶位 ②双方所有灯移奇位",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥4"),
        effect_fn=lambda gs, c, t: gs.resolve_choice(c, "ding_zhen"),
        tags=["特殊", "破坏", "加速"]
    ))
    cards.append(Card(
        id="NW_20", name="幻灯", class_type=ClassType.NIGHTWATCH,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="=4", effect_desc="复制敌方上回合打出的牌的效果",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "=4"),
        effect_fn=lambda gs, c, t: gs.copy_opponent_last_effect(c),
        tags=["特殊", "复制", "学习"]
    ))
    
    return cards


# ======== 灭灯者 - 20张 ========
def make_extinguisher_cards() -> List[Card]:
    """灭灯者牌库：减灯6 + 封锁6 + 奥秘4 + 特殊4"""
    cards = []
    
    # ---- 减灯牌（6张）----
    cards.append(Card(
        id="EX_01", name="幽焰", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.REDUCE,
        threshold_desc="≥1", effect_desc="敌方-1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥1"),
        effect_fn=lambda gs, c, t: gs.reduce_lamps(t, 2),
        tags=["减灯", "基础"]
    ))
    cards.append(Card(
        id="EX_02", name="深幽", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.REDUCE,
        threshold_desc="敌方≥3", effect_desc="敌方-2",
        threshold_fn=lambda gs, p: _opp_lamp_check(gs, p, "敌方≥3"),
        effect_fn=lambda gs, c, t: gs.reduce_lamps(t, 2),
        tags=["减灯", "避免马太", "核心"]
    ))
    cards.append(Card(
        id="EX_03", name="余波", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.REDUCE,
        threshold_desc="≥2", effect_desc="敌方-1；下回合开始时敌方再-1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: {**gs.reduce_lamps(t, 1), "next_turn_reduce": 1},
        tags=["减灯", "DOT", "跨回合"]
    ))
    cards.append(Card(
        id="EX_04", name="噬光", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.REDUCE,
        threshold_desc="=5", effect_desc="敌方-2，自己-1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "=5"),
        effect_fn=lambda gs, c, t: {**gs.reduce_lamps(t, 2), **gs.reduce_lamps(c, 1)},
        tags=["减灯", "双刃剑"]
    ))
    cards.append(Card(
        id="EX_05", name="全灭", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.REDUCE,
        threshold_desc="≥6", effect_desc="敌方-2",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥6"),
        effect_fn=lambda gs, c, t: gs.reduce_lamps(t, 2),
        tags=["减灯", "爆发"]
    ))
    cards.append(Card(
        id="EX_06", name="暗涌", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.REDUCE,
        threshold_desc="≤2", effect_desc="自己+1，敌方-1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≤2"),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 1), **gs.reduce_lamps(t, 1)},
        tags=["减灯", "绝境", "反击"]
    ))
    
    # ---- 封锁牌（6张）----
    cards.append(Card(
        id="EX_07", name="缚光", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.LOCK,
        threshold_desc="≥2", effect_desc="敌方下回合第一张牌效果减半",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: {"next_first_card_halved": True},
        tags=["封锁", "软控制"]
    ))
    cards.append(Card(
        id="EX_08", name="晦影", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.LOCK,
        threshold_desc="≥3", effect_desc="敌方-1；若敌方响应区有牌，弃置一张",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥3"),
        effect_fn=lambda gs, c, t: gs.reduce_lamps_and_destroy_response(t, 1),
        tags=["封锁", "破坏奥秘", "核心"]
    ))
    cards.append(Card(
        id="EX_09", name="延熄", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.LOCK,
        threshold_desc="≥2", effect_desc="敌方本回合不能打出增加自身灯数的牌",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥2"),
        effect_fn=lambda gs, c, t: {"lock_lamp_increase_this_turn": True},
        tags=["封锁", "核心"]
    ))
    cards.append(Card(
        id="EX_10", name="缚魂", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.LOCK,
        threshold_desc="=3", effect_desc="敌方-1；下回合敌方不能放入响应区",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "=3"),
        effect_fn=lambda gs, c, t: {**gs.reduce_lamps(t, 1), "lock_response_next_turn": True},
        tags=["封锁", "阻止奥秘"]
    ))
    cards.append(Card(
        id="EX_11", name="晦明", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.LOCK,
        threshold_desc="≤2", effect_desc="敌方-1；若敌方灯数≤1，下回合不能抽牌",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≤2"),
        effect_fn=lambda gs, c, t: gs.reduce_and_deny_draw(t, 1),
        tags=["封锁", "极端压制"]
    ))
    cards.append(Card(
        id="EX_12", name="灭魂", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.INSTANT, category=CardCategory.LOCK,
        threshold_desc="≥4", effect_desc="敌方-1；若敌方本回合已出过牌，再-1",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥4"),
        effect_fn=lambda gs, c, t: gs.reduce_lamps(t, 2 if gs.opponent_played_this_turn(t) else 1),
        tags=["封锁", "连锁压制"]
    ))
    
    # ---- 奥秘/响应牌（4张）----
    cards.append(Card(
        id="EX_13", name="蚀光", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方打出增加自身灯数的牌时", effect_desc="敌方-2，你+1",
        trigger_fn=lambda gs, owner, action, card: card is not None and any(kw in card.effect_desc for kw in ["自己+", "自己 +"]),
        effect_fn=lambda gs, c, t: {**gs.reduce_lamps(t, 2), **gs.add_lamps(c, 1)},
        tags=["进攻", "奥秘", "威慑", "核心"]
    ))
    cards.append(Card(
        id="EX_14", name="噬影", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方灯数达到5时", effect_desc="敌方-2",
        trigger_fn=lambda gs, owner, action, card: card is not None and any(kw in card.effect_desc for kw in ["自己+", "自己 +"]),
        effect_fn=lambda gs, c, t: gs.reduce_lamps(t, 2),
        tags=["进攻", "奥秘", "阻止冲刺"]
    ))
    cards.append(Card(
        id="EX_15", name="暗盾", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方打出减少你灯数的牌时", effect_desc="取消效果，敌方-1",
        trigger_fn=lambda gs, owner, action, card: card is not None and any(kw in card.effect_desc for kw in ["敌方", "对手"]) and any(kw in card.effect_desc for kw in ["-1", "-2", "-3", "减", "熄"]),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 1), **gs.reduce_lamps(t, 1)},  # 简化：owner+1抵消减灯, opponent-1
        tags=["防御", "奥秘", "反击"]
    ))
    cards.append(Card(
        id="EX_16", name="晦盾", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.RESPONSE, category=CardCategory.RESPONSE,
        trigger_desc="敌方跳过出牌时", effect_desc="敌方下回合抽牌数-1",
        trigger_fn=lambda gs, owner, action, card: "跳过出牌" in action,
        effect_fn=lambda gs, c, t: {"reduce_draw_next_turn": 1},
        tags=["封锁", "奥秘", "惩罚"]
    ))
    
    # ---- 特殊牌（4张）----
    cards.append(Card(
        id="EX_17", name="暗噬", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="敌方≤3", effect_desc="敌方-1，自己+1",
        threshold_fn=lambda gs, p: _opp_lamp_check(gs, p, "敌方≤3"),
        effect_fn=lambda gs, c, t: {**gs.reduce_lamps(t, 1), **gs.add_lamps(c, 1)},
        tags=["特殊", "此消彼长"]
    ))
    cards.append(Card(
        id="EX_18", name="熄灯", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="敌方≥5", effect_desc="敌方灯数变为当前灯数-3",
        threshold_fn=lambda gs, p: _opp_lamp_check(gs, p, "敌方≥5"),
        effect_fn=lambda gs, c, t: gs.set_lamps(t, gs.get_lamps(t) - 3),
        tags=["特殊", "百分比斩杀", "核心"]
    ))
    cards.append(Card(
        id="EX_19", name="回光", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="己方<敌方", effect_desc="自己+1，敌方-1；若己方<敌方额外敌方-1",
        threshold_fn=lambda gs, p: _relative_check(gs, p, "己方<敌方"),
        effect_fn=lambda gs, c, t: {**gs.add_lamps(c, 1), **gs.reduce_lamps(t, 2)},
        tags=["特殊", "翻盘", "攻守兼备"]
    ))
    cards.append(Card(
        id="EX_20", name="暗雾", class_type=ClassType.EXTINGUISHER,
        card_type=CardType.SPECIAL, category=CardCategory.SPECIAL,
        threshold_desc="≥3", effect_desc="双方各-1；若敌方因此≤2，标记计数生效",
        threshold_fn=lambda gs, p: _lamp_check(gs, p, "≥3"),
        effect_fn=lambda gs, c, t: gs.reduce_both_and_check_win(c, t, 1),
        tags=["特殊", "献祭", "接近胜利"]
    ))
    
    return cards


# ======== 牌库注册表 ========
ALL_CARDS: Dict[str, Card] = {}
CLASS_POOLS: Dict[ClassType, List[Card]] = {}


def _init_registry():
    """初始化全局牌库注册表"""
    global ALL_CARDS, CLASS_POOLS
    
    ll_cards = make_lamplighter_cards()
    nw_cards = make_nightwatch_cards()
    ex_cards = make_extinguisher_cards()
    
    CLASS_POOLS = {
        ClassType.LAMPLIGHTER: ll_cards,
        ClassType.NIGHTWATCH: nw_cards,
        ClassType.EXTINGUISHER: ex_cards,
    }
    
    for card in ll_cards + nw_cards + ex_cards:
        ALL_CARDS[card.id] = card


# 自动初始化
_init_registry()


def get_card(card_id: str) -> Card:
    """通过ID获取卡牌"""
    return ALL_CARDS.get(card_id)


def get_pool(class_type: ClassType) -> List[Card]:
    """获取某职业的完整牌池（20张）"""
    return CLASS_POOLS.get(class_type, [])


def list_all_cards() -> List[Card]:
    """列出所有60张牌"""
    return list(ALL_CARDS.values())
