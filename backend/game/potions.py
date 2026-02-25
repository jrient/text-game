"""药水系统"""
import random
from typing import List, Dict


POTIONS = [
    {
        'id': 'health_potion',
        'name': '治愈药水',
        'description': '恢复50%最大HP',
        'icon': '🧪',
        'rarity': 'common',
        'effect': 'heal_percent',
        'value': 50,
    },
    {
        'id': 'strength_potion',
        'name': '力量药水',
        'description': '本次战斗力量+5',
        'icon': '💪',
        'rarity': 'common',
        'effect': 'strength',
        'value': 5,
    },
    {
        'id': 'swift_potion',
        'name': '迅捷药水',
        'description': '立即抽3张牌',
        'icon': '💨',
        'rarity': 'common',
        'effect': 'draw',
        'value': 3,
    },
    {
        'id': 'block_potion',
        'name': '护盾药水',
        'description': '获得12点格挡',
        'icon': '🛡️',
        'rarity': 'common',
        'effect': 'block',
        'value': 12,
    },
    {
        'id': 'energy_potion',
        'name': '能量药水',
        'description': '立即获得2点能量',
        'icon': '⚡',
        'rarity': 'uncommon',
        'effect': 'energy',
        'value': 2,
    },
    {
        'id': 'poison_potion',
        'name': '毒素药水',
        'description': '对目标施加6层毒素',
        'icon': '☠️',
        'rarity': 'uncommon',
        'effect': 'poison',
        'value': 6,
    },
    {
        'id': 'fire_potion',
        'name': '火焰药水',
        'description': '对所有敌人造成20点伤害',
        'icon': '🔥',
        'rarity': 'uncommon',
        'effect': 'fire_damage',
        'value': 20,
    },
    {
        'id': 'ancient_potion',
        'name': '古代药水',
        'description': '随机获得1个遗物',
        'icon': '🏺',
        'rarity': 'rare',
        'effect': 'relic',
        'value': 0,
    },
    {
        'id': 'gamblers_brew',
        'name': '赌徒之酿',
        'description': '弃掉所有手牌，重新抽等量的牌',
        'icon': '🎲',
        'rarity': 'uncommon',
        'effect': 'gamble',
        'value': 0,
    },
    {
        'id': 'dexterity_potion',
        'name': '敏捷药水',
        'description': '本次战斗敏捷+3',
        'icon': '🤸',
        'rarity': 'common',
        'effect': 'dexterity',
        'value': 3,
    },
]

POTION_DICT = {p['id']: p for p in POTIONS}


def get_random_potion(rarity: str = None) -> Dict:
    if rarity:
        pool = [p for p in POTIONS if p['rarity'] == rarity]
    else:
        pool = POTIONS
    return random.choice(pool).copy() if pool else None


def use_potion(potion: dict, player: dict, enemies: list, target_idx: int = 0) -> tuple:
    """使用药水，返回(更新后player, 更新后enemies, 日志)"""
    logs = []
    effect = potion.get('effect', '')
    value = potion.get('value', 0)

    if effect == 'heal_percent':
        heal = int(player['max_hp'] * value / 100)
        player['hp'] = min(player['max_hp'], player['hp'] + heal)
        logs.append(f"🧪 使用{potion['name']}：恢复 {heal} HP")

    elif effect == 'strength':
        player['strength'] = player.get('strength', 0) + value
        logs.append(f"💪 使用{potion['name']}：力量 +{value}")

    elif effect == 'draw':
        from .combat import draw_cards
        drawn = draw_cards(player, value)
        logs.append(f"💨 使用{potion['name']}：抽取 {drawn} 张牌")

    elif effect == 'block':
        player['block'] = player.get('block', 0) + value
        logs.append(f"🛡️ 使用{potion['name']}：获得 {value} 点格挡")

    elif effect == 'energy':
        player['energy'] = player.get('energy', 0) + value
        logs.append(f"⚡ 使用{potion['name']}：能量 +{value}")

    elif effect == 'poison':
        alive = [e for e in enemies if e.get('hp', 0) > 0]
        if alive and target_idx < len(alive):
            alive[target_idx]['poison'] = alive[target_idx].get('poison', 0) + value
            logs.append(f"☠️ 使用{potion['name']}：对 {alive[target_idx]['name']} 施加 {value} 层毒素")

    elif effect == 'fire_damage':
        alive = [e for e in enemies if e.get('hp', 0) > 0]
        for i, enemy in enumerate(alive):
            dmg = max(0, value - enemy.get('block', 0))
            enemy['block'] = max(0, enemy.get('block', 0) - value)
            enemy['hp'] = max(0, enemy['hp'] - dmg)
        logs.append(f"🔥 使用{potion['name']}：对所有敌人造成 {value} 点伤害")

    elif effect == 'relic':
        from .relics import get_random_relic
        relic = get_random_relic('uncommon')
        if relic:
            player.setdefault('relics', []).append(relic)
            logs.append(f"🏺 使用{potion['name']}：获得遗物 {relic['name']}")

    elif effect == 'gamble':
        hand_size = len(player.get('hand', []))
        for card in player.get('hand', []):
            player['discard_pile'].append(card)
        player['hand'] = []
        from .combat import draw_cards
        drawn = draw_cards(player, hand_size)
        logs.append(f"🎲 使用{potion['name']}：重新抽取 {drawn} 张牌")

    elif effect == 'dexterity':
        player['dexterity'] = player.get('dexterity', 0) + value
        logs.append(f"🤸 使用{potion['name']}：敏捷 +{value}")

    return player, enemies, logs


def get_shop_potions(count: int = 3) -> List[dict]:
    selected = random.sample(POTIONS, min(count, len(POTIONS)))
    prices = {'common': 50, 'uncommon': 75, 'rare': 120}
    result = []
    for p in selected:
        potion = p.copy()
        potion['price'] = prices.get(p['rarity'], 60)
        result.append(potion)
    return result
