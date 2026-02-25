"""文字肉鸽游戏 - Flask主应用"""
import json
import os
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from game.map_gen import get_next_available_nodes

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# SQLite 持久化存储（支持多人游玩、服务器重启恢复）
from game.db import get_game, save_game, record_run, get_leaderboard, get_stats_summary, cleanup_old_games

# 每100次新游戏清理一次旧数据
_new_game_count = 0


# ===== 静态文件服务 =====
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)


# ===== API: 游戏管理 =====
@app.route('/api/characters', methods=['GET'])
def get_characters():
    """获取可选职业列表"""
    from game.state import CHARACTER_STATS
    chars = []
    for cid, stats in CHARACTER_STATS.items():
        chars.append({
            'id': cid,
            'name': stats['name'],
            'icon': stats['icon'],
            'description': stats['description'],
            'max_hp': stats['max_hp'],
            'max_energy': stats.get('max_energy', 3),
            'base_block': stats.get('base_block', 0),
            'char_attack_bonus': stats.get('char_attack_bonus', 0),
            'char_defense_bonus': stats.get('char_defense_bonus', 0),
        })
    return jsonify({'characters': chars})


@app.route('/api/new_game', methods=['POST'])
def new_game():
    """开始新游戏"""
    data = request.json or {}
    character = data.get('character', 'warrior')
    player_name = data.get('name', '英雄')

    ascension = data.get('ascension', 0)
    from game.state import create_new_game
    state = create_new_game(character, player_name, ascension)
    game_id = state['game_id']
    save_game(game_id, state)

    # 每50局清理一次超过2小时未活动的旧游戏
    global _new_game_count
    _new_game_count += 1
    if _new_game_count % 50 == 0:
        removed = cleanup_old_games(hours=2)
        if removed > 0:
            app.logger.info(f'清理了 {removed} 个旧游戏会话')

    return jsonify({
        'game_id': game_id,
        'message': state['message'],
        'player': _safe_player(state['player']),
        'phase': state['phase'],
    })


@app.route('/api/state', methods=['GET'])
def get_state():
    """获取完整游戏状态"""
    game_id = request.args.get('game_id')
    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404

    return jsonify(_build_response(state))


# ===== API: 地图 =====
@app.route('/api/map', methods=['GET'])
def get_map():
    """获取当前地图"""
    game_id = request.args.get('game_id')
    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404

    return jsonify({
        'map': state['map'],
        'phase': state['phase'],
        'player': _safe_player(state['player']),
    })


@app.route('/api/select_node', methods=['POST'])
def select_node():
    """选择地图节点"""
    data = request.json or {}
    game_id = data.get('game_id')
    node_id = data.get('node_id')

    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404

    if state['phase'] != 'map':
        return jsonify({'error': '当前不在地图阶段'}), 400

    map_data = state['map']
    node = map_data['nodes'].get(node_id)
    if not node:
        return jsonify({'error': '节点不存在'}), 400

    if node_id not in map_data.get('available_nodes', []):
        return jsonify({'error': '该节点不可访问'}), 400

    # 更新地图可用节点
    get_next_available_nodes(map_data, node_id)
    state['map'] = map_data

    node_type = node['type']
    player = state['player']
    player['floor'] = node.get('floor', player.get('floor', 0)) + 1

    if node_type in ('monster', 'elite', 'boss'):
        from game.state import init_combat
        state = init_combat(state, node_type, player['floor'])
        state['message'] = f'⚔️ 进入战斗！'

    elif node_type == 'rest':
        state['phase'] = 'rest'
        state['message'] = '🔥 你找到了一处篝火。在此休息或升级卡牌？'

    elif node_type == 'shop':
        from game.state import get_shop_inventory
        state['shop'] = get_shop_inventory(state)
        state['phase'] = 'shop'
        state['message'] = '🛒 欢迎光临！有什么需要的吗？'

    elif node_type == 'event':
        from game.events import get_random_event
        state['event'] = get_random_event()
        state['phase'] = 'event'
        state['message'] = f'❓ {state["event"]["title"]}'

    elif node_type == 'treasure':
        from game.relics import get_random_relic
        relic = get_random_relic()
        if relic:
            player['relics'].append(relic)
            state['message'] = f'📦 你打开了宝箱！获得遗物: {relic["name"]}'
        gold = random.randint(20, 50)
        player['gold'] += gold
        state['message'] += f' 和 {gold} 金币'
        state['phase'] = 'map'

    state['player'] = player
    save_game(game_id, state)
    return jsonify(_build_response(state))


# ===== API: 战斗 =====
@app.route('/api/combat/play_card', methods=['POST'])
def play_card():
    """打出卡牌"""
    data = request.json or {}
    game_id = data.get('game_id')
    card_index = data.get('card_index', 0)
    target_index = data.get('target_index', 0)

    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404
    if state['phase'] != 'combat':
        return jsonify({'error': '当前不在战斗阶段'}), 400

    player = state['player']
    combat = state['combat']
    enemies = combat['enemies']

    # 获取手牌中的卡
    hand = player.get('hand', [])
    if card_index >= len(hand):
        return jsonify({'error': '无效的牌索引'}), 400

    card = hand[card_index]

    # 检查能量
    cost = card.get('cost', 0)
    if isinstance(cost, int) and player.get('energy', 0) < cost:
        return jsonify({'error': '能量不足', 'energy': player['energy'], 'cost': cost}), 400

    if card.get('unplayable'):
        return jsonify({'error': '此牌无法打出'}), 400

    # 过滤存活敌人
    alive_enemies = [e for e in enemies if e.get('hp', 0) > 0]
    if not alive_enemies:
        return jsonify({'error': '没有存活的敌人'}), 400

    # 确保target_index有效
    target_index = min(target_index, len(alive_enemies) - 1)

    # 执行卡牌效果
    from game.combat import apply_card_effect, check_combat_end
    player, alive_enemies, logs = apply_card_effect(card, player, alive_enemies, target_index)

    # 统计
    player['cards_played'] = player.get('cards_played', 0) + 1

    # 从手牌移除（exhaust -> exhaust_pile, 否则 -> discard_pile）
    hand.pop(card_index)
    if card.get('exhaust'):
        player['exhaust_pile'] = player.get('exhaust_pile', []) + [card]
    else:
        player['discard_pile'].append(card)

    player['hand'] = hand

    # 更新敌人列表（保留死亡敌人以显示）
    for enemy in alive_enemies:
        for i, orig_enemy in enumerate(enemies):
            if orig_enemy['id'] == enemy['id'] or orig_enemy['name'] == enemy['name']:
                enemies[i] = enemy
                break

    combat['log'] = logs
    combat['enemies'] = enemies

    # 检查战斗结束
    result = check_combat_end(player, alive_enemies)

    if result == 'victory':
        from game.state import end_combat_victory
        state['player'] = player
        state['combat'] = combat
        state = end_combat_victory(state)
        if state['phase'] == 'victory':  # 最终胜利
            record_run(state['player'], 'victory', state.get('ascension', 0))
        save_game(game_id, state)
        return jsonify({**_build_response(state), 'combat_result': 'victory', 'log': logs})

    elif result == 'defeat':
        state['phase'] = 'game_over'
        state['message'] = '💀 你已倒下！游戏结束。'
        state['player'] = player
        state['combat'] = combat
        record_run(player, 'defeat', state.get('ascension', 0))
        save_game(game_id, state)
        return jsonify({**_build_response(state), 'combat_result': 'defeat', 'log': logs})

    state['player'] = player
    state['combat'] = combat
    save_game(game_id, state)

    return jsonify({
        **_build_response(state),
        'log': logs,
    })


@app.route('/api/combat/end_turn', methods=['POST'])
def end_turn():
    """结束玩家回合"""
    data = request.json or {}
    game_id = data.get('game_id')

    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404
    if state['phase'] != 'combat':
        return jsonify({'error': '当前不在战斗阶段'}), 400

    player = state['player']
    combat = state['combat']
    enemies = combat['enemies']
    alive_enemies = [e for e in enemies if e.get('hp', 0) > 0]

    from game.combat import end_player_turn, start_player_turn, check_combat_end

    # 敌人回合
    player, alive_enemies, enemy_logs = end_player_turn(player, alive_enemies)

    # 检查死亡
    result = check_combat_end(player, alive_enemies)

    # 更新敌人列表
    for ae in alive_enemies:
        for i, e in enumerate(enemies):
            if e['name'] == ae['name']:
                enemies[i] = ae
                break

    if result == 'defeat':
        state['phase'] = 'game_over'
        state['message'] = '💀 你已倒下！游戏结束。'
        state['player'] = player
        state['combat'] = combat
        record_run(player, 'defeat', state.get('ascension', 0))
        save_game(game_id, state)
        return jsonify({**_build_response(state), 'combat_result': 'defeat', 'log': enemy_logs})

    if result == 'victory':
        from game.state import end_combat_victory
        state['player'] = player
        state['combat'] = combat
        state = end_combat_victory(state)
        if state['phase'] == 'victory':  # 最终胜利
            record_run(state['player'], 'victory', state.get('ascension', 0))
        save_game(game_id, state)
        return jsonify({**_build_response(state), 'combat_result': 'victory', 'log': enemy_logs})

    # 开始新的玩家回合（传入enemies，遗物效果在start_player_turn内统一处理）
    combat['turn'] += 1
    player['turns'] = player.get('turns', 0) + 1
    player, alive_enemies, start_logs = start_player_turn(player, alive_enemies)
    all_logs = enemy_logs + ['--- 玩家回合 ---'] + start_logs

    combat['enemies'] = enemies
    combat['log'] = all_logs
    state['player'] = player
    state['combat'] = combat
    save_game(game_id, state)

    return jsonify({**_build_response(state), 'log': all_logs})


# ===== API: 卡牌奖励 =====
@app.route('/api/pick_card', methods=['POST'])
def pick_card():
    """选择奖励卡牌"""
    data = request.json or {}
    game_id = data.get('game_id')
    card_id = data.get('card_id')
    skip = data.get('skip', False)

    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404

    if not skip and card_id:
        from game.cards import ALL_CARDS
        card_data = None
        for reward in (state.get('card_rewards') or []):
            if reward['id'] == card_id:
                card_data = reward
                break
        if card_data:
            state['player']['deck'].append(card_data)
            state['player']['discard_pile'].append(card_data)

    state['card_rewards'] = None
    state['phase'] = 'map'
    state['message'] = '🗺️ 选择下一个目的地...'
    save_game(game_id, state)
    return jsonify(_build_response(state))


# ===== API: Boss遗物 =====
@app.route('/api/pick_relic', methods=['POST'])
def pick_relic():
    """选择Boss遗物"""
    data = request.json or {}
    game_id = data.get('game_id')
    relic_id = data.get('relic_id')

    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404

    from game.state import select_boss_relic
    state = select_boss_relic(state, relic_id)
    save_game(game_id, state)
    return jsonify(_build_response(state))


# ===== API: 休息点 =====
@app.route('/api/rest', methods=['POST'])
def rest():
    """在休息点休息或升级"""
    data = request.json or {}
    game_id = data.get('game_id')
    action = data.get('action', 'heal')  # heal / upgrade
    card_id = data.get('card_id')

    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404
    if state['phase'] != 'rest':
        return jsonify({'error': '当前不在休息阶段'}), 400

    player = state['player']

    if action == 'heal':
        heal_amount = max(15, player['max_hp'] // 3)
        player['hp'] = min(player['max_hp'], player['hp'] + heal_amount)
        state['message'] = f'🔥 休息恢复了 {heal_amount} 点HP！'

    elif action == 'upgrade' and card_id:
        # 升级指定卡牌
        for card in player['deck']:
            if card['id'] == card_id and not card.get('upgraded'):
                card['upgraded'] = True
                card['name'] = card['name'] + '+'
                # 升级效果
                if card.get('damage'):
                    card['damage'] = int(card['damage'] * 1.3) + 2
                if card.get('block'):
                    card['block'] = int(card['block'] * 1.3) + 2
                if card.get('cost', 1) > 0:
                    card['cost'] = max(0, card['cost'] - 1)
                # 升级后更新描述中的数值
                import re
                desc = card.get('description', '')
                if card.get('damage', 0) > 0 and '伤害' in desc:
                    desc = re.sub(r'\d+(?=点伤害)', str(card['damage']), desc, count=1)
                if card.get('block', 0) > 0 and '格挡' in desc:
                    desc = re.sub(r'\d+(?=点格挡)', str(card['block']), desc, count=1)
                card['description'] = desc
                state['message'] = f'✨ 卡牌【{card["name"]}】已升级！'
                break

    state['phase'] = 'map'
    state['player'] = player
    save_game(game_id, state)
    return jsonify(_build_response(state))


# ===== API: 商店 =====
@app.route('/api/shop/buy_card', methods=['POST'])
def shop_buy_card():
    """购买卡牌"""
    data = request.json or {}
    game_id = data.get('game_id')
    card_id = data.get('card_id')

    state = get_game(game_id)
    if not state or state['phase'] != 'shop':
        return jsonify({'error': '不在商店'}), 400

    shop = state['shop']
    player = state['player']
    price = shop['card_prices'].get(card_id, 999)

    if player.get('gold', 0) < price:
        return jsonify({'error': f'金币不足！需要 {price} 金币', 'gold': player['gold']}), 400

    card = next((c for c in shop['cards'] if c['id'] == card_id), None)
    if not card:
        return jsonify({'error': '商品已售出'}), 400

    player['gold'] -= price
    player['deck'].append(card)
    player['discard_pile'].append(card)
    shop['cards'] = [c for c in shop['cards'] if c['id'] != card_id]
    del shop['card_prices'][card_id]

    state['message'] = f'💰 购买了【{card["name"]}】(-{price} 金币)'
    state['player'] = player
    state['shop'] = shop
    save_game(game_id, state)
    return jsonify(_build_response(state))


@app.route('/api/shop/buy_relic', methods=['POST'])
def shop_buy_relic():
    """购买遗物"""
    data = request.json or {}
    game_id = data.get('game_id')
    relic_id = data.get('relic_id')

    state = get_game(game_id)
    if not state or state['phase'] != 'shop':
        return jsonify({'error': '不在商店'}), 400

    shop = state['shop']
    player = state['player']
    price = shop['relic_prices'].get(relic_id, 999)

    if player.get('gold', 0) < price:
        return jsonify({'error': f'金币不足！需要 {price} 金币', 'gold': player['gold']}), 400

    relic = next((r for r in shop['relics'] if r['id'] == relic_id), None)
    if not relic:
        return jsonify({'error': '商品已售出'}), 400

    player['gold'] -= price
    player['relics'].append(relic)
    shop['relics'] = [r for r in shop['relics'] if r['id'] != relic_id]
    del shop['relic_prices'][relic_id]

    state['message'] = f'💰 购买了遗物【{relic["name"]}】(-{price} 金币)'
    state['player'] = player
    state['shop'] = shop
    save_game(game_id, state)
    return jsonify(_build_response(state))


@app.route('/api/shop/remove_card', methods=['POST'])
def shop_remove_card():
    """商店移除牌"""
    data = request.json or {}
    game_id = data.get('game_id')
    card_id = data.get('card_id')

    state = get_game(game_id)
    if not state or state['phase'] != 'shop':
        return jsonify({'error': '不在商店'}), 400

    shop = state['shop']
    player = state['player']
    price = shop.get('remove_price', 75)

    if player.get('gold', 0) < price:
        return jsonify({'error': f'金币不足！需要 {price} 金币'}), 400

    original_len = len(player['deck'])
    player['deck'] = [c for c in player['deck'] if c['id'] != card_id]

    if len(player['deck']) < original_len:
        player['gold'] -= price
        state['message'] = f'🗑️ 已从牌组中移除一张牌 (-{price} 金币)'
    else:
        return jsonify({'error': '牌不在牌组中'}), 400

    state['player'] = player
    save_game(game_id, state)
    return jsonify(_build_response(state))


@app.route('/api/shop/heal', methods=['POST'])
def shop_heal():
    """商店治疗"""
    data = request.json or {}
    game_id = data.get('game_id')

    state = get_game(game_id)
    if not state or state['phase'] != 'shop':
        return jsonify({'error': '不在商店'}), 400

    shop = state['shop']
    player = state['player']
    price = shop.get('heal_price', 30)
    heal_amount = shop.get('heal_amount', 20)

    if player.get('gold', 0) < price:
        return jsonify({'error': f'金币不足！需要 {price} 金币'}), 400

    player['gold'] -= price
    player['hp'] = min(player['max_hp'], player['hp'] + heal_amount)
    state['message'] = f'💊 恢复了 {heal_amount} 点HP (-{price} 金币)'
    state['player'] = player
    save_game(game_id, state)
    return jsonify(_build_response(state))


@app.route('/api/shop/leave', methods=['POST'])
def shop_leave():
    """离开商店"""
    data = request.json or {}
    game_id = data.get('game_id')

    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404

    state['phase'] = 'map'
    state['shop'] = None
    state['message'] = '🗺️ 选择下一个目的地...'
    save_game(game_id, state)
    return jsonify(_build_response(state))


# ===== API: 事件 =====
@app.route('/api/event/choose', methods=['POST'])
def event_choose():
    """选择事件选项"""
    data = request.json or {}
    game_id = data.get('game_id')
    choice_index = data.get('choice_index', 0)

    state = get_game(game_id)
    if not state or state['phase'] != 'event':
        return jsonify({'error': '不在事件阶段'}), 400

    event = state['event']
    player = state['player']

    from game.events import process_event_choice
    player, result_desc, extra_data = process_event_choice(
        event['id'], choice_index, player, player['character']
    )

    state['player'] = player
    state['message'] = result_desc

    # 处理特殊额外数据
    if extra_data.get('action') == 'pick_card':
        state['card_rewards'] = extra_data.get('card_rewards', [])
        state['phase'] = 'card_reward'
    elif extra_data.get('action') == 'upgrade_card':
        state['phase'] = 'rest'  # 复用升级UI
    else:
        state['phase'] = 'map'

    state['event'] = None
    save_game(game_id, state)
    return jsonify({**_build_response(state), 'extra': extra_data})


# ===== API: 查看牌组 =====
@app.route('/api/deck', methods=['GET'])
def view_deck():
    """查看完整牌组"""
    game_id = request.args.get('game_id')
    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404

    player = state['player']
    return jsonify({
        'deck': player.get('deck', []),
        'deck_size': len(player.get('deck', [])),
    })


# ===== API: 药水 =====
@app.route('/api/use_potion', methods=['POST'])
def use_potion():
    """使用药水"""
    data = request.json or {}
    game_id = data.get('game_id')
    potion_index = data.get('potion_index', 0)
    target_index = data.get('target_index', 0)

    state = get_game(game_id)
    if not state:
        return jsonify({'error': '游戏不存在'}), 404

    player = state['player']
    potions = player.get('potions', [])

    if potion_index >= len(potions):
        return jsonify({'error': '无效的药水'}), 400

    potion = potions[potion_index]
    enemies = []
    if state['phase'] == 'combat' and state.get('combat'):
        enemies = state['combat']['enemies']

    from game.potions import use_potion as _use_potion
    player, enemies, logs = _use_potion(potion, player, enemies, target_index)

    # 移除已使用的药水
    potions.pop(potion_index)
    player['potions'] = potions

    if state['phase'] == 'combat' and state.get('combat'):
        state['combat']['enemies'] = enemies
        state['combat']['log'] = logs

    state['player'] = player
    state['message'] = logs[0] if logs else '使用了药水'
    save_game(game_id, state)
    return jsonify({**_build_response(state), 'log': logs})


@app.route('/api/shop/buy_potion', methods=['POST'])
def shop_buy_potion():
    """购买药水"""
    data = request.json or {}
    game_id = data.get('game_id')
    potion_id = data.get('potion_id')

    state = get_game(game_id)
    if not state or state['phase'] != 'shop':
        return jsonify({'error': '不在商店'}), 400

    shop = state['shop']
    player = state['player']

    potion = next((p for p in shop.get('potions', []) if p['id'] == potion_id), None)
    if not potion:
        return jsonify({'error': '药水不存在'}), 400

    price = potion.get('price', 50)
    if player.get('gold', 0) < price:
        return jsonify({'error': f'金币不足！需要 {price} 金币'}), 400

    # 最多携带3瓶药水
    if len(player.get('potions', [])) >= 3:
        return jsonify({'error': '药水槽已满（最多3瓶）'}), 400

    player['gold'] -= price
    player.setdefault('potions', []).append(potion)
    shop['potions'] = [p for p in shop.get('potions', []) if p['id'] != potion_id]

    state['message'] = f'🧪 购买了{potion["name"]} (-{price} 金币)'
    state['player'] = player
    state['shop'] = shop
    save_game(game_id, state)
    return jsonify(_build_response(state))


# ===== 辅助函数 =====
def _safe_player(player: dict) -> dict:
    """返回玩家的安全视图（不含内部状态）"""
    return {k: v for k, v in player.items() if k not in ('draw_pile', 'exhaust_pile')}


def _build_response(state: dict) -> dict:
    """构建标准响应"""
    player = state['player']
    combat = state.get('combat')

    resp = {
        'game_id': state['game_id'],
        'phase': state['phase'],
        'message': state.get('message', ''),
        'player': _safe_player(player),
        'turn': state.get('turn', 1),
    }

    if state['phase'] == 'map':
        resp['map'] = state.get('map')

    elif state['phase'] == 'combat' and combat:
        resp['combat'] = {
            'enemies': combat['enemies'],
            'turn': combat['turn'],
            'log': combat.get('log', []),
            'node_type': combat.get('node_type', 'monster'),
        }
        resp['hand'] = player.get('hand', [])
        resp['energy'] = player.get('energy', 0)
        resp['block'] = player.get('block', 0)
        resp['draw_pile_count'] = len(player.get('draw_pile', []))
        resp['discard_pile_count'] = len(player.get('discard_pile', []))
        resp['potions'] = player.get('potions', [])

    elif state['phase'] == 'card_reward':
        resp['card_rewards'] = state.get('card_rewards', [])

    elif state['phase'] == 'boss_relic':
        resp['boss_relic_choices'] = state.get('boss_relic_choices', [])

    elif state['phase'] == 'shop':
        resp['shop'] = state.get('shop')

    elif state['phase'] == 'event':
        resp['event'] = state.get('event')

    elif state['phase'] == 'rest':
        resp['deck'] = player.get('deck', [])

    elif state['phase'] in ('game_over', 'victory'):
        resp['final_stats'] = state.get('victory_stats') or {
            'floor': player.get('floor', 0),
            'kills': player.get('kills', 0),
            'turns': player.get('turns', 0),
            'cards_played': player.get('cards_played', 0),
            'damage_dealt': player.get('damage_dealt', 0),
            'damage_taken': player.get('damage_taken', 0),
            'gold_earned': player.get('gold_earned', 0),
            'relics_count': len(player.get('relics', [])),
            'deck_size': len(player.get('deck', [])),
            'ascension': state.get('ascension', 0),
            'character': player.get('character_name', ''),
        }

    resp['ascension'] = state.get('ascension', 0)
    resp['ascension_name'] = state.get('ascension_name', '普通模式')
    return resp


# ===== API: 排行榜 =====
@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    """获取排行榜（按分数降序，最多20条）"""
    limit = min(int(request.args.get('limit', 20)), 50)
    entries = get_leaderboard(limit)
    stats = get_stats_summary()
    return jsonify({'entries': entries, 'stats': stats})


@app.route('/api/active_players', methods=['GET'])
def active_players():
    """当前活跃玩家数"""
    from game.db import get_active_games
    games = get_active_games(50)
    return jsonify({
        'count': len(games),
        'games': games,
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    print(f'🎮 文字肉鸽游戏服务器启动 - http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=debug)
