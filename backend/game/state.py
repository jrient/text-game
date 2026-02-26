"""游戏状态管理 - V3: 天赋难度系统 + 完整遗物集成"""
import copy
import random
import uuid
from typing import Dict, List, Optional

from .cards import get_starter_deck, get_card_rewards
from .relics import get_starter_relic, get_boss_relic_choices
from .map_gen import generate_map, get_next_available_nodes
from .enemies import create_enemy


CHARACTER_STATS = {
    'warrior': {
        'max_hp': 95, 'gold': 25, 'name': '战士', 'icon': '⚔️',
        'description': '铁壁战士，HP最高，防御极强，每回合获得5点被动护甲，攻击偏弱',
        'max_energy': 3, 'base_block': 5,
        'char_attack_bonus': -1,   # 攻击卡每次命中 -1 伤害
        'char_defense_bonus': 4,   # 格挡卡每次使用 +4 格挡
    },
    'mage': {
        'max_hp': 52, 'gold': 25, 'name': '法师', 'icon': '🔮',
        'description': '能量法师，HP最低，4点能量，攻击法术威力极强，防御薄弱',
        'max_energy': 4, 'base_block': 0,
        'char_attack_bonus': 3,    # 攻击卡每次命中 +3 伤害
        'char_defense_bonus': -1,  # 格挡卡每次使用 -1 格挡
    },
    'assassin': {
        'max_hp': 70, 'gold': 25, 'name': '刺客', 'icon': '🗡️',
        'description': '暗影刺客，攻击力强，擅长连击爆发，防御一般',
        'max_energy': 3, 'base_block': 0,
        'char_attack_bonus': 2,    # 攻击卡每次命中 +2 伤害
        'char_defense_bonus': 0,   # 格挡无加成
    },
}

# 天赋难度说明
ASCENSION_INFO = {
    0: {'name': '普通模式', 'description': '标准难度，适合新手'},
    1: {'name': '天赋1', 'description': '精英战斗更频繁'},
    2: {'name': '天赋2', 'description': '所有敌人HP+10%'},
    3: {'name': '天赋3', 'description': '敌人HP+15%，Boss HP+20%'},
    4: {'name': '天赋4', 'description': '敌人HP+20%，Boss HP+25%，敌人伤害+10%'},
    5: {'name': '天赋5', 'description': '极限挑战！敌人HP+30%，起手有1张伤口牌'},
}


def create_new_game(character: str, player_name: str = 'Hero', ascension: int = 0) -> Dict:
    """创建新游戏状态"""
    stats = CHARACTER_STATS.get(character, CHARACTER_STATS['warrior'])
    starter_deck = get_starter_deck(character)
    starter_relic = get_starter_relic(character)

    # 天赋5：起手加入1张伤口牌
    if ascension >= 5:
        wound_card = {
            'id': 'wound', 'name': '伤口', 'description': '无法打出。',
            'cost': 1, 'type': 'curse', 'character': 'common', 'rarity': 'curse',
            'damage': 0, 'block': 0, 'unplayable': True, 'exhaust': False,
        }
        starter_deck.append(wound_card)

    # 洗牌
    shuffled_deck = starter_deck[:]
    random.shuffle(shuffled_deck)

    player = {
        'id': str(uuid.uuid4()),
        'name': player_name,
        'character': character,
        'character_name': stats['name'],
        'character_icon': stats['icon'],

        # 生命值
        'hp': stats['max_hp'],
        'max_hp': stats['max_hp'],

        # 战斗属性
        'strength': 0,
        'dexterity': 0,
        'energy': stats.get('max_energy', 3),
        'max_energy': stats.get('max_energy', 3),
        'base_block': stats.get('base_block', 0),
        'char_attack_bonus': stats.get('char_attack_bonus', 0),   # 职业攻击修正（每次命中）
        'char_defense_bonus': stats.get('char_defense_bonus', 0), # 职业防御修正（每次格挡）

        # 状态效果（非战斗时为0）
        'block': 0,
        'weak_turns': 0,
        'vulnerable_turns': 0,
        'bonus_draw': 0,

        # 牌组
        'deck': starter_deck[:],
        'draw_pile': shuffled_deck,
        'hand': [],
        'discard_pile': [],
        'exhaust_pile': [],

        # 资源
        'gold': stats['gold'],
        'relics': [starter_relic],
        'potions': [],  # 药水槽（最多3个）

        # 进度
        'floor': 0,
        'act': 1,
        'kills': 0,
        'turns': 0,

        # 统计
        'damage_dealt': 0,
        'damage_taken': 0,
        'cards_played': 0,
        'gold_earned': stats['gold'],
    }

    # 生成第1幕地图
    map_data = generate_map(1)

    ascension_info = ASCENSION_INFO.get(ascension, ASCENSION_INFO[0])

    game_state = {
        'game_id': str(uuid.uuid4()),
        'phase': 'map',
        'player': player,
        'map': map_data,
        'combat': None,
        'shop': None,
        'event': None,
        'card_rewards': None,
        'boss_relic_choices': None,
        'combat_log': [],
        'message': f'欢迎，勇敢的{stats["name"]}！选择你的路线，挑战深渊！',
        'turn': 1,
        'ascension': ascension,
        'ascension_name': ascension_info['name'],
    }

    return game_state


def init_combat(game_state: Dict, node_type: str, floor: int) -> Dict:
    """初始化战斗"""
    from .enemies import create_enemy
    from .combat import start_player_turn

    player = game_state['player']
    ascension = game_state.get('ascension', 0)

    # 重置战斗状态
    player['block'] = 0
    player['_combat_turn'] = 1

    # 重置手牌：从 deck（权威牌组）重建抽牌堆，确保升级效果生效
    all_cards = copy.deepcopy(player['deck'])
    random.shuffle(all_cards)
    player['hand'] = []
    player['discard_pile'] = []
    player['draw_pile'] = all_cards
    player['exhaust_pile'] = []

    # 重置法球槽
    player['orbs'] = []
    player['orb_slots'] = player.get('orb_slots', 3)

    # 创建敌人
    enemies = []
    if node_type == 'boss':
        enemy = create_enemy('boss', floor)
        enemies.append(enemy.to_dict())
    elif node_type == 'elite':
        enemy = create_enemy('elite', floor)
        enemies.append(enemy.to_dict())
    else:
        # 天赋1+：更多可能出现2个敌人
        two_enemy_weight = 40 + ascension * 5
        num_enemies = random.choices([1, 2], weights=[100 - two_enemy_weight, two_enemy_weight])[0]
        for _ in range(num_enemies):
            enemy = create_enemy('normal', floor)
            enemies.append(enemy.to_dict())

    # 天赋难度：缩放敌人属性
    if ascension >= 2:
        hp_scale = 1.0
        dmg_scale = 1.0
        if ascension == 2:
            hp_scale = 1.10
        elif ascension == 3:
            hp_scale = 1.15 if not any(e.get('is_boss') for e in enemies) else 1.20
        elif ascension == 4:
            hp_scale = 1.20 if not any(e.get('is_boss') for e in enemies) else 1.25
            dmg_scale = 1.10
        elif ascension >= 5:
            hp_scale = 1.30
            dmg_scale = 1.15

        for enemy in enemies:
            if hp_scale > 1.0:
                new_hp = int(enemy['hp'] * hp_scale)
                enemy['hp'] = new_hp
                enemy['max_hp'] = new_hp
            if dmg_scale > 1.0 and enemy.get('intent', {}).get('value', 0) > 0:
                enemy['intent']['value'] = int(enemy['intent']['value'] * dmg_scale)

    combat = {
        'enemies': enemies,
        'turn': 1,
        'turn_phase': 'player',
        'node_type': node_type,
        'log': [f'⚔️ 战斗开始！'],
    }

    game_state['combat'] = combat
    game_state['phase'] = 'combat'

    # 遗物触发：战斗开始
    try:
        from .relic_effects import on_combat_start
        player, enemies, relic_logs = on_combat_start(player, enemies)
        combat['log'].extend(relic_logs)
    except Exception:
        pass

    # 开始第一回合（传入enemies以触发汞沙漏等遗物）
    player, enemies, start_logs = start_player_turn(player, enemies)
    combat['log'].extend(start_logs)
    combat['enemies'] = enemies

    game_state['player'] = player
    return game_state


def end_combat_victory(game_state: Dict) -> Dict:
    """战斗胜利后的处理"""
    player = game_state['player']
    combat = game_state['combat']
    node_type = combat.get('node_type', 'monster')

    # 经验和击杀
    player['kills'] += len(combat['enemies'])

    # 金币奖励
    ascension = game_state.get('ascension', 0)
    base_gold = {
        'monster': random.randint(10, 20),
        'elite': random.randint(25, 35),
        'boss': random.randint(95, 105),
    }.get(node_type, 10)

    # 天赋模式略微降低金币
    if ascension >= 3:
        base_gold = int(base_gold * 0.9)

    # 大颌银行：每场战斗额外+12金币，直到第一次访问商店
    relic_ids = {r['id'] for r in player.get('relics', [])}
    if 'maw_bank' in relic_ids and not player.get('_maw_bank_spent', False):
        base_gold += 12

    player['gold'] += base_gold
    player['gold_earned'] = player.get('gold_earned', 0) + base_gold

    # 遗物触发：战斗结束
    try:
        from .relic_effects import on_combat_end
        player, relic_logs = on_combat_end(player, is_victory=True)
        # 日志会在下一次响应中显示
    except Exception:
        pass

    # 地图楼层推进
    player['floor'] += 1

    # Boss胜利：进入下一幕
    if node_type == 'boss':
        current_act = game_state['map']['act']
        if current_act >= 3:
            game_state['phase'] = 'victory'
            game_state['message'] = f'🏆 恭喜！你击败了腐化之心，拯救了世界！'
            # 记录胜利统计
            game_state['victory_stats'] = _build_final_stats(player, game_state)
            return game_state

        game_state['boss_relic_choices'] = get_boss_relic_choices(3)
        game_state['phase'] = 'boss_relic'
        game_state['message'] = f'✨ 你击败了Boss！选择一件强大的遗物...'
        game_state['next_act'] = current_act + 1
    elif node_type == 'elite':
        from .relics import get_random_relic
        relic = get_random_relic()
        if relic:
            player['relics'].append(relic)
            game_state['message'] = f'💀 精英战胜利！获得遗物: {relic["name"]}'
        reward_count = 4 if any(r.get('id') == 'question_card' for r in player.get('relics', [])) else 3
        game_state['card_rewards'] = get_card_rewards(player['character'], player['floor'], reward_count)
        game_state['phase'] = 'card_reward'
    else:
        reward_count = 4 if any(r.get('id') == 'question_card' for r in player.get('relics', [])) else 3
        game_state['card_rewards'] = get_card_rewards(player['character'], player['floor'], reward_count)
        game_state['phase'] = 'card_reward'
        game_state['message'] = f'⚔️ 战斗胜利！获得 {base_gold} 金币。选择一张奖励卡牌...'

    game_state['player'] = player
    game_state['combat'] = None
    return game_state


def _build_final_stats(player: dict, game_state: dict) -> dict:
    """构建最终统计数据"""
    return {
        'floor': player.get('floor', 0),
        'kills': player.get('kills', 0),
        'turns': player.get('turns', 0),
        'cards_played': player.get('cards_played', 0),
        'damage_dealt': player.get('damage_dealt', 0),
        'damage_taken': player.get('damage_taken', 0),
        'gold_earned': player.get('gold_earned', 0),
        'relics_count': len(player.get('relics', [])),
        'deck_size': len(player.get('deck', [])),
        'ascension': game_state.get('ascension', 0),
        'character': player.get('character_name', ''),
    }


def select_boss_relic(game_state: Dict, relic_id: str) -> Dict:
    """选择Boss遗物"""
    from .relics import ALL_RELICS_DICT
    player = game_state['player']

    relic = ALL_RELICS_DICT.get(relic_id)
    if relic:
        player['relics'].append(relic.to_dict())

    # 生成下一幕地图
    next_act = game_state.get('next_act', 2)
    game_state['map'] = generate_map(next_act)
    game_state['phase'] = 'map'
    game_state['boss_relic_choices'] = None
    game_state['message'] = f'🗺️ 进入第{next_act}幕！继续你的征途...'
    game_state['player'] = player
    return game_state


def get_shop_inventory(game_state: Dict) -> Dict:
    """生成商店库存"""
    from .cards import get_shop_cards
    from .relics import get_shop_relics

    player = game_state['player']
    character = player['character']
    floor = player.get('floor', 1)

    cards = get_shop_cards(character)
    relics = get_shop_relics(2)

    # 快递员遗物：商店打折
    discount = 0.8 if any(r['id'] == 'the_courier' for r in player.get('relics', [])) else 1.0

    card_prices = {}
    for card in cards:
        base = {'common': 75, 'uncommon': 150, 'rare': 200}.get(card['rarity'], 100)
        card_prices[card['id']] = int(base * discount)

    relic_prices = {}
    for relic in relics:
        base = {'common': 150, 'uncommon': 250, 'rare': 300}.get(relic['rarity'], 200)
        relic_prices[relic['id']] = int(base * discount)

    from .potions import get_shop_potions
    potions = get_shop_potions(3)

    shop = {
        'cards': cards,
        'relics': relics,
        'potions': potions,
        'card_prices': card_prices,
        'relic_prices': relic_prices,
        'remove_price': int(75 * discount),
        'heal_price': int(30 * discount),
        'heal_amount': max(10, player['max_hp'] // 4),
    }

    return shop


def apply_relic_start_of_combat(player: dict, relics: list) -> dict:
    """应用战斗开始遗物效果（兼容旧代码）"""
    for relic in relics:
        rid = relic.get('id', '')
        if rid == 'captain_wheel':
            player['strength'] = player.get('strength', 0) + 3
            player['dexterity'] = player.get('dexterity', 0) + 3
            player['block'] = player.get('block', 0) + 3
    return player
