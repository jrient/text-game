"""地图生成系统 - 类Slay the Spire节点地图"""
import random
from typing import List, Dict, Optional


NODE_TYPES = {
    'monster': {'label': '⚔️ 战斗', 'color': 'red', 'weight': 45},
    'elite': {'label': '💀 精英', 'color': 'purple', 'weight': 12},
    'rest': {'label': '🔥 篝火', 'color': 'green', 'weight': 12},
    'shop': {'label': '🛒 商店', 'color': 'gold', 'weight': 10},
    'event': {'label': '❓ 事件', 'color': 'cyan', 'weight': 16},
    'treasure': {'label': '📦 宝箱', 'color': 'yellow', 'weight': 5},
}

ACT_CONFIG = {
    1: {'floors': 7, 'boss': 'boss1'},
    2: {'floors': 7, 'boss': 'boss2'},
    3: {'floors': 5, 'boss': 'boss3'},
}


def generate_map(act: int = 1) -> Dict:
    """生成一幕的地图"""
    config = ACT_CONFIG.get(act, ACT_CONFIG[1])
    floors = config['floors']

    # 每层3-4个节点
    nodes = []
    for floor in range(floors):
        num_nodes = random.randint(3, 4)
        floor_nodes = []
        for pos in range(num_nodes):
            node_type = _pick_node_type(floor, floors)
            node = {
                'id': f'{floor}_{pos}',
                'floor': floor,
                'position': pos,
                'type': node_type,
                'label': NODE_TYPES[node_type]['label'],
                'color': NODE_TYPES[node_type]['color'],
                'visited': False,
                'connections': [],  # 连接到下一层的节点id
                'available': floor == 0,  # 第一层可选
            }
            floor_nodes.append(node)
        nodes.append(floor_nodes)

    # 生成连接（每个节点连接到下一层1-2个节点）
    for floor in range(floors - 1):
        current_floor = nodes[floor]
        next_floor = nodes[floor + 1]
        for node in current_floor:
            # 随机连接1-2个下一层节点
            num_connections = random.randint(1, min(2, len(next_floor)))
            chosen = random.sample(next_floor, num_connections)
            node['connections'] = [n['id'] for n in chosen]

    # 确保所有下一层节点至少有一个入口
    for floor in range(floors - 1):
        next_floor = nodes[floor + 1]
        current_floor = nodes[floor]
        all_connected = set()
        for node in current_floor:
            all_connected.update(node['connections'])
        for next_node in next_floor:
            if next_node['id'] not in all_connected:
                # 随机给它一个入口
                random.choice(current_floor)['connections'].append(next_node['id'])

    # 扁平化节点列表，加上Boss节点
    flat_nodes = {}
    for floor_nodes in nodes:
        for node in floor_nodes:
            flat_nodes[node['id']] = node

    # 添加Boss节点
    boss_node = {
        'id': f'boss_{act}',
        'floor': floors,
        'position': 0,
        'type': 'boss',
        'label': '👑 Boss',
        'color': 'crimson',
        'visited': False,
        'connections': [],
        'available': False,
    }
    # 最后一层所有节点连接到Boss
    for node in nodes[-1]:
        node['connections'].append(boss_node['id'])
    flat_nodes[boss_node['id']] = boss_node

    return {
        'act': act,
        'floors': floors + 1,  # 包含Boss层
        'nodes': flat_nodes,
        'current_floor': 0,
        'available_nodes': [nodes[0][i]['id'] for i in range(len(nodes[0]))],
    }


def _pick_node_type(floor: int, total_floors: int) -> str:
    """根据楼层选择节点类型"""
    # 第一层只有普通战斗
    if floor == 0:
        return 'monster'
    # 最后一层前不出现精英（太难了）
    if floor == total_floors - 1:
        types = ['monster', 'rest', 'shop', 'event']
        weights = [40, 25, 20, 15]
    else:
        types = list(NODE_TYPES.keys())
        weights = [NODE_TYPES[t]['weight'] for t in types]

    return random.choices(types, weights=weights)[0]


def get_next_available_nodes(map_data: dict, visited_node_id: str) -> List[str]:
    """访问节点后，更新可用节点列表"""
    node = map_data['nodes'].get(visited_node_id)
    if not node:
        return map_data['available_nodes']

    node['visited'] = True
    # 将连接的节点设为可用
    new_available = []
    for connected_id in node['connections']:
        connected = map_data['nodes'].get(connected_id)
        if connected and not connected['visited']:
            connected['available'] = True
            new_available.append(connected_id)

    # 更新available_nodes：移除当前访问的节点，加入新可用节点
    current_available = map_data.get('available_nodes', [])
    # 移除同层所有节点（选了一个就不能选其他）
    current_floor = node['floor']
    updated = [n for n in current_available
               if map_data['nodes'].get(n, {}).get('floor', -1) != current_floor]
    updated.extend(new_available)

    map_data['available_nodes'] = updated
    map_data['current_floor'] = node['floor'] + 1
    return updated
