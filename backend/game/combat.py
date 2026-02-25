"""战斗逻辑系统 - V3: 集成遗物效果触发"""
import random
from typing import List, Dict, Optional, Tuple
from .cards import ALL_CARDS, Card
from .enemies import Enemy, EnemyIntent, create_enemy_from_dict


def apply_card_effect(card_data: dict, player: dict, enemies: List[dict],
                       target_idx: int = 0) -> Tuple[dict, List[dict], List[str]]:
    """
    执行卡牌效果
    返回: (更新后的player, 更新后的enemies列表, 战斗日志)
    """
    logs = []
    card = card_data

    # 消耗能量
    cost = card.get('cost', 0)
    if isinstance(cost, int):
        player['energy'] -= cost

    if card.get('unplayable'):
        return player, enemies, ['此牌无法打出！']

    # 追踪本回合出牌数量（用于遗物触发）
    card_type = card.get('type', '')
    player['_cards_this_turn'] = player.get('_cards_this_turn', 0) + 1
    if card_type == 'attack':
        player['_attacks_this_turn'] = player.get('_attacks_this_turn', 0) + 1
    elif card_type == 'skill':
        player['_skills_this_turn'] = player.get('_skills_this_turn', 0) + 1

    # 获取目标
    target_enemy = enemies[target_idx] if enemies and target_idx < len(enemies) else None

    # ---- 攻击效果 ----
    if card.get('damage', 0) > 0 and not card.get('apply_to_all'):
        if target_enemy:
            dmg = calculate_damage(card['damage'], card.get('hits', 1), player, target_enemy)
            actual_dmg, target_enemy = deal_damage(dmg, card.get('hits', 1), target_enemy, logs)
            player['damage_dealt'] = player.get('damage_dealt', 0) + actual_dmg
            logs.append(f"对 {target_enemy['name']} 造成 {actual_dmg} 点伤害")

    if card.get('damage', 0) > 0 and card.get('apply_to_all'):
        total = 0
        for i, enemy in enumerate(enemies):
            dmg = calculate_damage(card['damage'], card.get('hits', 1), player, enemy)
            actual_dmg, enemies[i] = deal_damage(dmg, card.get('hits', 1), enemy, logs)
            total += actual_dmg
        player['damage_dealt'] = player.get('damage_dealt', 0) + total
        logs.append(f"对所有敌人共造成 {total} 点伤害")

    # ---- 格挡效果 ----
    if card.get('block', 0) > 0:
        block_gain = calculate_block(card['block'], player)
        player['block'] = player.get('block', 0) + block_gain
        logs.append(f"获得 {block_gain} 点格挡")

    # ---- 抽牌 ----
    if card.get('draw', 0) > 0:
        drawn = draw_cards(player, card['draw'])
        logs.append(f"抽取 {drawn} 张牌")

    # ---- 毒素 ----
    if card.get('poison_stacks', 0) > 0 and target_enemy:
        target_enemy['poison'] = target_enemy.get('poison', 0) + card['poison_stacks']
        logs.append(f"对 {target_enemy['name']} 施加 {card['poison_stacks']} 层毒素")

    # ---- 虚弱 ----
    if card.get('weak_turns', 0) > 0 and target_enemy:
        target_enemy['weak_turns'] = target_enemy.get('weak_turns', 0) + card['weak_turns']
        logs.append(f"使 {target_enemy['name']} 虚弱 {card['weak_turns']} 回合")

    # ---- 易伤 ----
    if card.get('vulnerable_turns', 0) > 0 and target_enemy:
        target_enemy['vulnerable_turns'] = target_enemy.get('vulnerable_turns', 0) + card['vulnerable_turns']
        logs.append(f"使 {target_enemy['name']} 易伤 {card['vulnerable_turns']} 回合")

    # ---- 力量增益 ----
    if card.get('strength_gain', 0) > 0 and card_type != 'power':
        player['strength'] = player.get('strength', 0) + card['strength_gain']
        logs.append(f"力量 +{card['strength_gain']}")

    # ---- 能力牌（永久）----
    if card_type == 'power':
        if card.get('strength_gain', 0) > 0:
            player['strength'] = player.get('strength', 0) + card['strength_gain']
            logs.append(f"永久力量 +{card['strength_gain']}")
        if card.get('energy_gain', 0) > 0:
            player['max_energy'] = player.get('max_energy', 3) + card['energy_gain']
            logs.append(f"最大能量 +{card['energy_gain']}")
        if card.get('dexterity_gain', 0) > 0:
            player['dexterity'] = player.get('dexterity', 0) + card['dexterity_gain']
            logs.append(f"永久敏捷 +{card['dexterity_gain']}")

    # 处理exhaust
    if card.get('exhaust'):
        logs.append(f"【{card['name']}】已耗尽")

    # ---- 遗物触发：打出卡牌 ----
    try:
        from .relic_effects import on_card_played
        player, enemies, relic_logs = on_card_played(
            player, enemies, card,
            player.get('_attacks_this_turn', 0),
            player.get('_skills_this_turn', 0),
            player.get('_cards_this_turn', 0)
        )
        logs.extend(relic_logs)
    except Exception:
        pass

    return player, enemies, logs


def calculate_damage(base_dmg: int, hits: int, player: dict, enemy: dict) -> int:
    """计算实际伤害（含力量、职业攻击加成、虚弱、易伤等修正）"""
    strength = player.get('strength', 0)
    char_attack = player.get('char_attack_bonus', 0)
    per_hit = max(0, base_dmg + strength + char_attack)
    total = per_hit * hits

    # 虚弱减伤25%
    if player.get('weak_turns', 0) > 0:
        total = int(total * 0.75)

    # 易伤增伤50%
    if enemy.get('vulnerable_turns', 0) > 0:
        total = int(total * 1.5)

    return max(0, total)


def calculate_block(base_block: int, player: dict) -> int:
    """计算实际格挡（含敏捷、职业防御加成修正）"""
    dexterity = player.get('dexterity', 0)
    char_defense = player.get('char_defense_bonus', 0)
    block = base_block + dexterity + char_defense

    # 虚弱减少格挡25%
    if player.get('weak_turns', 0) > 0:
        block = int(block * 0.75)

    return max(0, block)


def deal_damage(damage: int, hits: int, enemy: dict, logs: List[str]) -> Tuple[int, dict]:
    """对敌人造成伤害，处理格挡"""
    total_dmg = 0
    for _ in range(hits):
        if damage <= 0:
            continue
        current_block = enemy.get('block', 0)
        if current_block > 0:
            if damage >= current_block:
                dmg_through = damage - current_block
                enemy['block'] = 0
                enemy['hp'] -= dmg_through
                total_dmg += dmg_through
            else:
                enemy['block'] -= damage
        else:
            enemy['hp'] -= damage
            total_dmg += damage

    enemy['hp'] = max(0, enemy['hp'])
    return total_dmg, enemy


def deal_damage_to_player(damage: int, player: dict, logs: List[str]) -> Tuple[dict, int]:
    """对玩家造成伤害，格挡作为护甲减免伤害（不消耗）"""
    block = player.get('block', 0)
    actual_dmg = max(0, damage - block)
    if actual_dmg > 0:
        player['hp'] -= actual_dmg
        if block > 0:
            logs.append(f"护甲减免 {damage - actual_dmg} 点，你受到 {actual_dmg} 点伤害")
        else:
            logs.append(f"你受到 {actual_dmg} 点伤害")
    else:
        logs.append(f"护甲完全抵消了 {damage} 点伤害")

    player['hp'] = max(0, player['hp'])
    return player, actual_dmg


def draw_cards(player: dict, count: int) -> int:
    """抽牌：从抽牌堆移到手牌"""
    drawn = 0
    for _ in range(count):
        if not player['draw_pile']:
            # 洗牌：将弃牌堆变成抽牌堆
            if player['discard_pile']:
                player['draw_pile'] = player['discard_pile'][:]
                random.shuffle(player['draw_pile'])
                player['discard_pile'] = []
            else:
                break
        if player['draw_pile']:
            card = player['draw_pile'].pop()
            player['hand'].append(card)
            drawn += 1
    return drawn


def enemy_turn(player: dict, enemies: List[dict]) -> Tuple[dict, List[dict], List[str]]:
    """执行敌人回合"""
    logs = []
    alive_enemies = [e for e in enemies if e.get('hp', 0) > 0]
    total_damage_taken = 0

    for enemy in alive_enemies:
        # 处理毒素伤害
        if enemy.get('poison', 0) > 0:
            poison_dmg = enemy['poison']
            enemy['hp'] = max(0, enemy['hp'] - poison_dmg)
            enemy['poison'] -= 1
            logs.append(f"{enemy['name']} 受到 {poison_dmg} 点毒素伤害")

        if enemy['hp'] <= 0:
            logs.append(f"{enemy['name']} 因毒素死亡！")
            continue

        intent = enemy.get('intent', {})
        if not intent:
            continue

        action = intent.get('action', 'attack')
        value = intent.get('value', 0)
        times = intent.get('times', 1)

        if action == 'attack':
            # 计算敌人伤害（含力量）
            strength = enemy.get('strength', 0)
            total_dmg = (value + strength) * times

            # 敌人虚弱减伤25%
            if enemy.get('weak_turns', 0) > 0:
                total_dmg = int(total_dmg * 0.75)

            # 玩家易伤增伤
            if player.get('vulnerable_turns', 0) > 0:
                total_dmg = int(total_dmg * 1.5)

            player, actual_dmg = deal_damage_to_player(total_dmg, player, logs)
            total_damage_taken += actual_dmg
            logs.append(f"{enemy['name']} 攻击：{intent.get('description', f'{total_dmg}伤害')}")

            # 遗物触发：受到伤害时
            if actual_dmg > 0:
                try:
                    from .relic_effects import on_player_take_damage
                    player, alive_enemies, relic_logs = on_player_take_damage(player, alive_enemies, actual_dmg)
                    logs.extend(relic_logs)
                except Exception:
                    pass

        elif action == 'block':
            block_gain = value + enemy.get('dexterity', 0)
            enemy['block'] = enemy.get('block', 0) + block_gain
            if block_gain > 0:
                logs.append(f"{enemy['name']} 获得 {block_gain} 点格挡")
            if intent.get('description'):
                logs.append(f"{enemy['name']}：{intent['description']}")

        elif action == 'buff':
            enemy['strength'] = enemy.get('strength', 0) + value
            if value > 0:
                logs.append(f"{enemy['name']} 力量 +{value}")
            if intent.get('description'):
                logs.append(f"{enemy['name']}：{intent['description']}")

        elif action == 'special':
            logs.append(f"{enemy['name']}：{intent.get('description', '特殊行动')}")

        # 更新敌人虚弱/易伤回合
        if enemy.get('weak_turns', 0) > 0:
            enemy['weak_turns'] -= 1
        if enemy.get('vulnerable_turns', 0) > 0:
            enemy['vulnerable_turns'] -= 1

        # 更新下一回合意图
        enemy['move_history'] = enemy.get('move_history', [])
        enemy['move_history'].append(action)
        enemy['intent'] = _generate_next_intent(enemy)

    # 统计伤害
    player['damage_taken'] = player.get('damage_taken', 0) + total_damage_taken

    return player, enemies, logs


def _generate_next_intent(enemy: dict) -> dict:
    """为敌人生成下一回合意图（简化AI）"""
    eid = enemy.get('id', '')
    move_count = len(enemy.get('move_history', []))

    # Boss意图逻辑
    if enemy.get('is_boss'):
        if 'guardian' in eid:
            patterns = [
                {'action': 'attack', 'value': 18, 'times': 1, 'description': '重击 18'},
                {'action': 'block', 'value': 0, 'times': 1, 'description': '充能模式'},
                {'action': 'attack', 'value': 9, 'times': 2, 'description': '扫击 2x9'},
                {'action': 'attack', 'value': 7, 'times': 3, 'description': '角刺 3x7'},
            ]
            return patterns[move_count % len(patterns)]
        elif 'hexa' in eid:
            if move_count % 7 == 0:
                return {'action': 'special', 'value': 0, 'times': 1, 'description': '召唤灼伤'}
            elif move_count % 7 < 3:
                v = 6 + enemy.get('strength', 0)
                return {'action': 'attack', 'value': v, 'times': 1, 'description': f'折磨 {v}'}
            elif move_count % 7 == 3:
                return {'action': 'buff', 'value': 3, 'times': 1, 'description': '仪式 力量+3'}
            else:
                v = 14 + enemy.get('strength', 0)
                return {'action': 'attack', 'value': v, 'times': 1, 'description': f'能量爆发 {v}'}
        elif 'corrupt' in eid:
            if move_count < 4:
                return {'action': 'special', 'value': 0, 'times': 1, 'description': f'调试模式（{4-move_count}回合后可伤）'}
            patterns = [
                {'action': 'attack', 'value': 12, 'times': 3, 'description': '橙色光束 3x12'},
                {'action': 'buff', 'value': 0, 'times': 1, 'description': '回血100HP'},
                {'action': 'special', 'value': 0, 'times': 1, 'description': '诅咒（+10张诅咒）'},
            ]
            return patterns[move_count % len(patterns)]

    # 精英意图
    if enemy.get('is_elite'):
        if 'gremlin_nob' in eid:
            if move_count == 0:
                return {'action': 'buff', 'value': 2, 'times': 1, 'description': '愤怒'}
            r = random.random()
            if r < 0.33:
                return {'action': 'attack', 'value': 14, 'times': 1, 'description': '冲撞 14'}
            return {'action': 'attack', 'value': 6, 'times': 2, 'description': '斩击 2x6'}
        elif 'lagavulin' in eid:
            if move_count < 3:
                return {'action': 'special', 'value': 0, 'times': 1, 'description': f'沉睡中...'}
            elif move_count == 3:
                return {'action': 'buff', 'value': 0, 'times': 1, 'description': '觉醒！'}
            r = random.random()
            if r < 0.45:
                return {'action': 'attack', 'value': 18, 'times': 1, 'description': '黏液袭击 18'}
            return {'action': 'buff', 'value': 0, 'times': 1, 'description': '虹吸'}
        elif 'sentry' in eid:
            if move_count % 3 == 0:
                return {'action': 'block', 'value': 0, 'times': 1, 'description': '射击（眩晕）'}
            return {'action': 'attack', 'value': 9, 'times': 1, 'description': '激光束 9'}

    # 普通敌人意图
    if 'cultist' in eid:
        if move_count == 0:
            return {'action': 'buff', 'value': 3, 'times': 1, 'description': '召唤仪式 力量+3'}
        v = 6 + enemy.get('strength', 0)
        return {'action': 'attack', 'value': v, 'times': 1, 'description': f'攻击 {v}'}
    elif 'jaw_worm' in eid:
        r = random.random()
        if r < 0.45:
            return {'action': 'attack', 'value': 11, 'times': 1, 'description': '撕咬 11'}
        elif r < 0.75:
            return {'action': 'block', 'value': 6, 'times': 1, 'description': '蜷缩 格挡6'}
        return {'action': 'attack', 'value': 7, 'times': 1, 'description': '嘶鸣 7'}
    elif 'louse' in eid:
        r = random.random()
        if r < 0.25:
            return {'action': 'buff', 'value': 3, 'times': 1, 'description': '自噬 力量+3'}
        v = random.randint(5, 7)
        return {'action': 'attack', 'value': v, 'times': 1, 'description': f'撕咬 {v}'}
    elif 'slime' in eid:
        r = random.random()
        if r < 0.3:
            return {'action': 'attack', 'value': 7, 'times': 2, 'description': '吐酸 2x7'}
        return {'action': 'special', 'value': 0, 'times': 1, 'description': '腐蚀 虚弱2回合'}

    # 默认
    v = random.randint(6, 12)
    return {'action': 'attack', 'value': v, 'times': 1, 'description': f'攻击 {v}'}


def start_player_turn(player: dict, enemies: List[dict] = None) -> Tuple[dict, List[dict], List[str]]:
    """开始玩家回合：恢复能量，弃置手牌，抽新牌"""
    logs = []
    if enemies is None:
        enemies = []

    # 弃置上回合手牌（除非有retain）
    for card in player.get('hand', []):
        if not card.get('retain'):
            player['discard_pile'].append(card)
    player['hand'] = []

    # 重置本回合计数器
    player['_cards_this_turn'] = 0
    player['_attacks_this_turn'] = 0
    player['_skills_this_turn'] = 0
    player['_puzzle_triggered'] = False  # 百年谜题每回合重置

    # 冰淇淋遗物：保留上回合未用能量
    saved_energy = player.pop('_saved_energy', 0)

    # 恢复能量（含卡尺保留格挡逻辑已在end_turn处理）
    player['energy'] = player.get('max_energy', 3) + saved_energy

    # 战士被动护甲：每回合开始自动叠加
    base_block = player.get('base_block', 0)
    if base_block > 0:
        player['block'] = player.get('block', 0) + base_block
        logs.append(f"🛡️ 战士护甲：获得 {base_block} 点格挡（当前格挡 {player['block']}）")

    # 抽5张牌
    hand_size = 5 + player.get('bonus_draw', 0)
    drawn = draw_cards(player, hand_size)
    logs.append(f"回合开始：恢复 {player['energy']} 点能量，抽取 {drawn} 张牌")

    # 减少虚弱/易伤回合（玩家的）
    if player.get('weak_turns', 0) > 0:
        player['weak_turns'] -= 1
    if player.get('vulnerable_turns', 0) > 0:
        player['vulnerable_turns'] -= 1

    # 遗物触发：回合开始
    combat_turn = player.get('_combat_turn', 1)
    try:
        from .relic_effects import on_turn_start
        player, enemies, relic_logs = on_turn_start(player, enemies, combat_turn)
        logs.extend(relic_logs)
    except Exception:
        pass

    player['_combat_turn'] = combat_turn + 1

    return player, enemies, logs


def end_player_turn(player: dict, enemies: List[dict]) -> Tuple[dict, List[dict], List[str]]:
    """结束玩家回合：处理手牌，执行敌人回合"""
    logs = ['--- 敌人回合 ---']

    # 计算弃牌数量（用于叮钹/坚韧绷带遗物触发）
    discarded_count = sum(
        1 for card in player.get('hand', [])
        if not card.get('retain') and not card.get('ethereal')
    )

    # 遗物触发：回合结束（在弃牌前）
    try:
        from .relic_effects import on_turn_end
        player, enemies, relic_logs = on_turn_end(player, enemies)
        logs.extend(relic_logs)
    except Exception:
        pass

    # 弃置手牌
    for card in player.get('hand', []):
        if card.get('ethereal'):
            logs.append(f"【{card['name']}】以太消失")
        elif not card.get('retain'):
            player['discard_pile'].append(card)
    player['hand'] = []

    # 遗物触发：弃牌
    if discarded_count > 0:
        try:
            from .relic_effects import on_discard
            player, enemies, relic_logs = on_discard(player, enemies, discarded_count)
            logs.extend(relic_logs)
        except Exception:
            pass

    # 格挡在战斗内持续有效，不在回合结束时重置
    player.pop('_calipers_block', None)  # 清除已无用的卡尺缓存

    # 执行敌人回合
    player, enemies, enemy_logs = enemy_turn(player, enemies)
    logs.extend(enemy_logs)

    return player, enemies, logs


def check_combat_end(player: dict, enemies: List[dict]) -> Optional[str]:
    """检查战斗结束条件"""
    if player.get('hp', 0) <= 0:
        return 'defeat'

    all_dead = all(e.get('hp', 0) <= 0 for e in enemies)
    if all_dead:
        return 'victory'

    return None
