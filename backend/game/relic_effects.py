"""遗物效果触发系统 - 让遗物真正发挥作用"""
from typing import List, Dict, Tuple


def on_combat_start(player: dict, enemies: list) -> Tuple[dict, list, List[str]]:
    """战斗开始时触发的遗物效果"""
    logs = []
    relics = player.get('relics', [])
    relic_ids = {r['id'] for r in relics}

    if 'anchor' in relic_ids:
        player['block'] = player.get('block', 0) + 10
        logs.append('🔩 遗物【锚】：获得10点格挡')

    if 'bag_of_marbles' in relic_ids:
        for e in enemies:
            e['weak_turns'] = e.get('weak_turns', 0) + 1
        logs.append('🪨 遗物【弹珠袋】：所有敌人虚弱1回合')

    if 'ring_of_snake' in relic_ids:
        from .combat import draw_cards
        draw_cards(player, 2)
        logs.append('🐍 遗物【蛇之戒】：额外抽2张牌')

    if 'bag_of_preparation' in relic_ids:
        from .combat import draw_cards
        draw_cards(player, 2)
        logs.append('🎒 遗物【准备袋】：额外抽2张牌')

    if 'captain_wheel' in relic_ids:
        player['strength'] = player.get('strength', 0) + 3
        player['dexterity'] = player.get('dexterity', 0) + 3
        player['block'] = player.get('block', 0) + 3
        logs.append('⚓ 遗物【船长之轮】：力量+3, 敏捷+3, 格挡+3')

    if 'horn_cleat' in relic_ids:
        # 前两回合额外格挡，用 combat_turn_count 追踪
        player['_horn_cleat_active'] = True
        logs.append('📎 遗物【角钳】：前2回合额外获得14点格挡')

    if 'blood_vial' in relic_ids:
        player['hp'] = min(player['max_hp'], player['hp'] + 2)
        logs.append('🩸 遗物【血瓶】：恢复2点HP')

    if 'lantern' in relic_ids:
        player['_lantern_used'] = False  # 第一回合才生效

    return player, enemies, logs


def on_turn_start(player: dict, enemies: list, turn: int) -> Tuple[dict, list, List[str]]:
    """每回合开始时触发的遗物效果"""
    logs = []
    relic_ids = {r['id'] for r in player.get('relics', [])}

    # 灯笼：第一回合+1能量
    if 'lantern' in relic_ids and not player.get('_lantern_used', True):
        player['energy'] = player.get('energy', 0) + 1
        player['_lantern_used'] = True
        logs.append('🏮 遗物【灯笼】：第一回合能量+1')

    # 角钳：前两回合+14格挡
    if 'horn_cleat' in relic_ids and player.get('_horn_cleat_active') and turn <= 2:
        player['block'] = player.get('block', 0) + 14
        logs.append('📎 遗物【角钳】：格挡+14')
        if turn == 2:
            player['_horn_cleat_active'] = False

    # 快乐花：每3回合+1能量
    if 'happy_flower' in relic_ids:
        flower_count = player.get('_flower_count', 0) + 1
        player['_flower_count'] = flower_count
        if flower_count % 3 == 0:
            player['energy'] = player.get('energy', 0) + 1
            logs.append('🌸 遗物【快乐花】：能量+1')

    # 汞沙漏：每回合对所有敌人造成3点伤害
    if 'mercury_hourglass' in relic_ids:
        for e in enemies:
            if e.get('hp', 0) > 0:
                e['hp'] = max(0, e['hp'] - 3)
        logs.append('⏳ 遗物【汞沙漏】：对所有敌人造成3点伤害')

    return player, enemies, logs


def on_turn_end(player: dict, enemies: list) -> Tuple[dict, list, List[str]]:
    """每回合结束时触发的遗物效果"""
    logs = []
    relic_ids = {r['id'] for r in player.get('relics', [])}

    # 金属化（来自能力牌）
    if player.get('metallicize_stacks', 0) > 0:
        stacks = player['metallicize_stacks']
        player['block'] = player.get('block', 0) + stacks
        logs.append(f'⚙️ 金属化：回合结束获得{stacks}点格挡')

    # 冰淇淋：保留未使用能量
    if 'ice_cream' in relic_ids:
        # 能量已经在end_turn被处理，这里确保保留
        player['_saved_energy'] = player.get('energy', 0)
        if player.get('energy', 0) > 0:
            logs.append(f'🍦 遗物【冰淇淋】：保留{player["energy"]}点能量')

    # 卡尺：保留最多15点格挡（不超过当前格挡）
    if 'calipers' in relic_ids:
        current_block = player.get('block', 0)
        player['_calipers_block'] = min(15, current_block)

    # 叮钹：每次丢弃牌时伤害（在这里处理弃牌时的效果）
    return player, enemies, logs


def on_card_played(player: dict, enemies: list, card: dict,
                    attack_count: int, skill_count: int,
                    total_count: int) -> Tuple[dict, list, List[str]]:
    """打出卡牌时触发的遗物效果"""
    logs = []
    relic_ids = {r['id'] for r in player.get('relics', [])}
    card_type = card.get('type', '')

    # 双截棍：每打出10张攻击牌+1能量
    if 'nunchaku' in relic_ids and card_type == 'attack':
        player['_nunchaku_count'] = player.get('_nunchaku_count', 0) + 1
        if player['_nunchaku_count'] % 10 == 0:
            player['energy'] = player.get('energy', 0) + 1
            logs.append('🥊 遗物【双截棍】：能量+1')

    # 苦无：每打出3张攻击牌+1敏捷
    if 'kunai' in relic_ids and card_type == 'attack':
        if attack_count % 3 == 0:
            player['dexterity'] = player.get('dexterity', 0) + 1
            logs.append('🗡️ 遗物【苦无】：敏捷+1')

    # 飞镖星：每打出3张攻击牌+1力量
    if 'shuriken' in relic_ids and card_type == 'attack':
        if attack_count % 3 == 0:
            player['strength'] = player.get('strength', 0) + 1
            logs.append('⭐ 遗物【飞镖星】：力量+1')

    # 装饰扇：每打出3张攻击牌+4格挡
    if 'ornamental_fan' in relic_ids and card_type == 'attack':
        if attack_count % 3 == 0:
            from .combat import calculate_block
            block_gain = calculate_block(4, player)
            player['block'] = player.get('block', 0) + block_gain
            logs.append(f'🪭 遗物【装饰扇】：格挡+{block_gain}')

    # 拆信刀：每打出3张技能牌对所有敌人造成5点伤害
    if 'letter_opener' in relic_ids and card_type == 'skill':
        if skill_count % 3 == 0:
            for e in enemies:
                if e.get('hp', 0) > 0:
                    e['hp'] = max(0, e['hp'] - 5)
            logs.append('✉️ 遗物【拆信刀】：对所有敌人造成5点伤害')

    # 墨水瓶：每打出10张牌抽1张
    if 'ink_bottle' in relic_ids:
        player['_ink_count'] = player.get('_ink_count', 0) + 1
        if player['_ink_count'] % 10 == 0:
            from .combat import draw_cards
            draw_cards(player, 1)
            logs.append('🖊️ 遗物【墨水瓶】：抽1张牌')

    # 鸟脸瓮：打出能力牌恢复2点HP
    if 'bird_faced_urn' in relic_ids and card_type == 'power':
        player['hp'] = min(player['max_hp'], player['hp'] + 2)
        logs.append('🏺 遗物【鸟脸瓮】：恢复2点HP')

    # 木乃伊手：打出能力牌随机降低手牌费用1点
    if 'mummified_hand' in relic_ids and card_type == 'power':
        import random
        hand = player.get('hand', [])
        if hand:
            target = random.choice(hand)
            if isinstance(target.get('cost', 0), int) and target['cost'] > 0:
                target['cost'] -= 1
                logs.append(f'🤚 遗物【木乃伊手】：【{target["name"]}】费用-1')

    # 枯枝：耗尽牌时获得随机牌
    if 'dead_branch' in relic_ids and card.get('exhaust'):
        from .cards import get_card_rewards
        rewards = get_card_rewards(player.get('character', 'warrior'), player.get('floor', 1), 1)
        if rewards:
            player.get('hand', []).append(rewards[0])
            logs.append(f'🌿 遗物【枯枝】：获得【{rewards[0]["name"]}】')

    # 铜鳞（bronze_scales）在受到攻击时反弹，这里在打出攻击时不触发
    # 叮铛：每次丢弃牌时对随机敌人造成3点伤害（在弃牌时触发）

    return player, enemies, logs


def on_discard(player: dict, enemies: list, discarded_count: int) -> Tuple[dict, list, List[str]]:
    """弃牌时触发的遗物效果"""
    logs = []
    relic_ids = {r['id'] for r in player.get('relics', [])}
    import random

    # 叮钹：每次丢弃牌对随机敌人造成3点伤害
    if 'tingsha' in relic_ids and discarded_count > 0:
        alive = [e for e in enemies if e.get('hp', 0) > 0]
        if alive:
            target = random.choice(alive)
            target['hp'] = max(0, target['hp'] - 3 * discarded_count)
            logs.append(f'🔔 遗物【叮钹】：对{target["name"]}造成{3*discarded_count}点伤害')

    # 坚韧绷带：每次丢弃牌时+3格挡
    if 'tough_bandages' in relic_ids and discarded_count > 0:
        block_gain = 3 * discarded_count
        player['block'] = player.get('block', 0) + block_gain
        logs.append(f'🩹 遗物【坚韧绷带】：格挡+{block_gain}')

    return player, enemies, logs


def on_combat_end(player: dict, is_victory: bool) -> Tuple[dict, List[str]]:
    """战斗结束时触发的遗物效果"""
    logs = []
    relic_ids = {r['id'] for r in player.get('relics', [])}

    if is_victory:
        # 燃烧之血：战斗胜利恢复6点HP
        if 'burning_blood' in relic_ids:
            player['hp'] = min(player['max_hp'], player['hp'] + 6)
            logs.append('🔥 遗物【燃烧之血】：恢复6点HP')

        # 黑血：战斗胜利恢复12点HP（升级版）
        if 'black_blood' in relic_ids:
            player['hp'] = min(player['max_hp'], player['hp'] + 12)
            logs.append('🖤 遗物【黑血】：恢复12点HP')

        # 餐券：进入商店恢复15HP（在进入商店时处理）
        # 肉在骨头上：HP低于50%时恢复12HP
        if 'meat_on_the_bone' in relic_ids:
            if player['hp'] <= player['max_hp'] * 0.5:
                player['hp'] = min(player['max_hp'], player['hp'] + 12)
                logs.append('🍖 遗物【骨头上的肉】：HP低，恢复12点HP')

    # 清理战斗临时状态
    for key in ['_lantern_used', '_horn_cleat_active', '_calipers_block', '_flower_count']:
        player.pop(key, None)

    return player, logs


def on_player_take_damage(player: dict, enemies: list, damage: int) -> Tuple[dict, list, List[str]]:
    """玩家受到伤害时触发"""
    logs = []
    relic_ids = {r['id'] for r in player.get('relics', [])}

    # 铜鳞：受到攻击时反弹3点伤害
    if 'bronze_scales' in relic_ids and damage > 0:
        for e in enemies:
            if e.get('hp', 0) > 0:
                e['hp'] = max(0, e['hp'] - 3)
                break
        logs.append('🐉 遗物【铜鳞】：反弹3点伤害')

    # 百年谜题：第一次每回合受伤时抽3张牌
    if 'centennial_puzzle' in relic_ids and not player.get('_puzzle_triggered'):
        player['_puzzle_triggered'] = True
        from .combat import draw_cards
        draw_cards(player, 3)
        logs.append('🧩 遗物【百年谜题】：受伤，抽3张牌')

    return player, enemies, logs
