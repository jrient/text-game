"""随机事件系统"""
import random
from typing import Dict, List


EVENTS = [
    {
        'id': 'ancient_writing',
        'title': '古老铭文',
        'description': '你发现了一片刻有神秘文字的石壁。研究这些文字或许会有所收获...',
        'image': '📜',
        'choices': [
            {
                'text': '仔细研读（获得1张随机升级牌）',
                'effect': 'upgrade_card',
                'description': '你花时间研究铭文，领悟了战斗的奥秘。'
            },
            {
                'text': '匆匆离开',
                'effect': 'nothing',
                'description': '你选择不冒险，继续前进。'
            }
        ]
    },
    {
        'id': 'cursed_tome',
        'title': '诅咒之书',
        'description': '一本散发着邪恶气息的魔法书漂浮在空中。翻阅它可能有危险，但也可能有收获...',
        'image': '📕',
        'choices': [
            {
                'text': '翻阅魔法书（获得20金币，失去5HP）',
                'effect': 'gold_hp',
                'value': {'gold': 20, 'hp': -5},
                'description': '你翻阅了魔法书，获得了财富，但付出了代价。'
            },
            {
                'text': '销毁它',
                'effect': 'nothing',
                'description': '你将书烧毁，感到一丝宽慰。'
            }
        ]
    },
    {
        'id': 'library',
        'title': '神秘图书馆',
        'description': '你发现了一个古老的图书馆。书架上摆满了各种卷轴和书籍。',
        'image': '📚',
        'choices': [
            {
                'text': '寻找有用的书（抽3张牌，保留1张）',
                'effect': 'pick_card',
                'description': '你在图书馆中找到了有用的战术指南。'
            },
            {
                'text': '休息一下（恢复15HP）',
                'effect': 'heal',
                'value': 15,
                'description': '你在图书馆中小憩片刻，恢复了体力。'
            }
        ]
    },
    {
        'id': 'merchant_robbery',
        'title': '落难商人',
        'description': '一个被盗贼洗劫一空的商人坐在路边。他声称如果你帮他找到遗失的货物，会给你报酬。',
        'image': '👨‍💼',
        'choices': [
            {
                'text': '帮助商人（获得随机遗物）',
                'effect': 'relic',
                'description': '你帮助了商人，他感激地给了你一件宝贝。'
            },
            {
                'text': '趁机抢劫（获得30金币，但战斗2次）',
                'effect': 'gold',
                'value': 30,
                'description': '你无耻地抢劫了落难商人...'
            },
            {
                'text': '继续赶路',
                'effect': 'nothing',
                'description': '你对商人的遭遇表示同情，但没有时间帮他。'
            }
        ]
    },
    {
        'id': 'mind_bloom',
        'title': '精神之花',
        'description': '你发现了一朵会散发迷幻孢子的奇异花朵。吸入这些孢子可能会改变你的意识...',
        'image': '🌸',
        'choices': [
            {
                'text': '吸入孢子（永久+10最大HP，获得诅咒）',
                'effect': 'max_hp',
                'value': 10,
                'description': '你的身体变强了，但内心多了一道阴影。'
            },
            {
                'text': '绕道而行',
                'effect': 'nothing',
                'description': '你明智地绕开了这株危险的植物。'
            }
        ]
    },
    {
        'id': 'golden_idol',
        'title': '黄金神像',
        'description': '一座散发光芒的黄金神像矗立在祭坛上。拿走它似乎会触发某种机关...',
        'image': '🏺',
        'choices': [
            {
                'text': '取走神像（获得250金币，触发陷阱-15HP）',
                'effect': 'gold_hp',
                'value': {'gold': 250, 'hp': -15},
                'description': '你取走了神像！但随之而来的飞镖让你受了伤。'
            },
            {
                'text': '用类似重量的东西替换（获得遗物）',
                'effect': 'relic',
                'description': '经典的替换手法！你获得了神像，还保住了性命。'
            },
            {
                'text': '不要触碰它',
                'effect': 'nothing',
                'description': '你明智地离开了这里。'
            }
        ]
    },
    {
        'id': 'drug_caravan',
        'title': '炼金商队',
        'description': '一队炼金术士正在售卖他们的秘制药水。这些药水看起来很诱人...',
        'image': '⚗️',
        'choices': [
            {
                'text': '购买增强药水（花费50金币，永久+2力量）',
                'effect': 'spend_gold_strength',
                'value': {'gold': 50, 'strength': 2},
                'description': '你喝下了强化药剂，感到力量涌遍全身！'
            },
            {
                'text': '购买治愈药水（花费30金币，恢复25HP）',
                'effect': 'spend_gold_heal',
                'value': {'gold': 30, 'hp': 25},
                'description': '伤口迅速愈合，你感觉好多了。'
            },
            {
                'text': '离开',
                'effect': 'nothing',
                'description': '你对这些可疑的药剂不感兴趣。'
            }
        ]
    },
    {
        'id': 'dead_adventurer',
        'title': '倒下的冒险者',
        'description': '你发现了一具冒险者的遗体，旁边散落着一些物品。',
        'image': '💀',
        'choices': [
            {
                'text': '搜索遗体（获得随机遗物或金币）',
                'effect': 'loot',
                'description': '你在遗体旁边找到了一些有价值的东西。'
            },
            {
                'text': '为其祈祷（获得1张随机牌）',
                'effect': 'card',
                'description': '你为这位冒险者祈祷，似乎从他的经验中领悟到了一些东西。'
            },
            {
                'text': '离开',
                'effect': 'nothing',
                'description': '你对逝者表示尊重，继续前进。'
            }
        ]
    },
    {
        'id': 'mysterious_sphere',
        'title': '神秘球体',
        'description': '一个发光的球体漂浮在虚空中，散发着难以名状的能量。',
        'image': '🔮',
        'choices': [
            {
                'text': '触碰球体（随机效果）',
                'effect': 'random',
                'description': '你伸手触碰了球体...'
            },
            {
                'text': '用力量打破它（需要20点力量，获得稀有遗物）',
                'effect': 'strength_check',
                'value': {'required_strength': 5, 'reward': 'rare_relic'},
                'description': '你用力量粉碎了球体！'
            },
            {
                'text': '绕开球体',
                'effect': 'nothing',
                'description': '你谨慎地绕开了这个不明物体。'
            }
        ]
    },
    {
        'id': 'knowing_skeleton',
        'title': '智慧骷髅',
        'description': '一具会说话的骷髅坐在角落里，自称拥有世界上所有的知识。',
        'image': '💬',
        'choices': [
            {
                'text': '询问如何变强（升级1张手牌）',
                'effect': 'upgrade_card',
                'description': '"知识就是力量！"骷髅传授了你宝贵的战斗技巧。'
            },
            {
                'text': '询问前方的危险（获知下一个Boss的信息）',
                'effect': 'boss_info',
                'description': '"前方有强大的敌人..."骷髅告诉了你未来的挑战。'
            },
            {
                'text': '"你不过是一堆骨头"（获得金币）',
                'effect': 'gold',
                'value': 40,
                'description': '骷髅气得牙关咯咯作响，金币哗哗落地。'
            }
        ]
    }
]


def get_random_event() -> Dict:
    """获取随机事件"""
    return random.choice(EVENTS).copy()


def process_event_choice(event_id: str, choice_index: int, player: dict,
                          character: str) -> tuple:
    """
    处理玩家的事件选择
    返回: (更新后的player, 结果描述, 额外数据)
    """
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    if not event or choice_index >= len(event['choices']):
        return player, '无效的选择', {}

    choice = event['choices'][choice_index]
    effect = choice.get('effect', 'nothing')
    value = choice.get('value', 0)
    result_desc = choice.get('description', '事件已处理')
    extra_data = {}

    if effect == 'nothing':
        pass

    elif effect == 'heal':
        heal_amount = value if isinstance(value, int) else 15
        player['hp'] = min(player['max_hp'], player['hp'] + heal_amount)
        result_desc += f' (+{heal_amount} HP)'

    elif effect == 'gold':
        gold_amount = value if isinstance(value, int) else 20
        player['gold'] = player.get('gold', 0) + gold_amount
        result_desc += f' (+{gold_amount} 金币)'

    elif effect == 'gold_hp':
        gold = value.get('gold', 0) if isinstance(value, dict) else 0
        hp = value.get('hp', 0) if isinstance(value, dict) else 0
        player['gold'] = player.get('gold', 0) + gold
        player['hp'] = max(1, min(player['max_hp'], player['hp'] + hp))
        result_desc += f' (+{gold} 金币, {hp:+d} HP)'

    elif effect == 'max_hp':
        bonus = value if isinstance(value, int) else 10
        player['max_hp'] += bonus
        player['hp'] = min(player['max_hp'], player['hp'] + bonus)
        result_desc += f' (最大HP +{bonus})'

    elif effect == 'relic':
        from .relics import get_random_relic
        new_relic = get_random_relic('uncommon')
        if new_relic:
            player.setdefault('relics', []).append(new_relic)
            extra_data['new_relic'] = new_relic
            result_desc += f' (获得遗物: {new_relic["name"]})'

    elif effect == 'loot':
        # 随机奖励
        r = random.random()
        if r < 0.5:
            from .relics import get_random_relic
            new_relic = get_random_relic('common')
            if new_relic:
                player.setdefault('relics', []).append(new_relic)
                extra_data['new_relic'] = new_relic
                result_desc += f' (获得遗物: {new_relic["name"]})'
        else:
            gold = random.randint(30, 60)
            player['gold'] = player.get('gold', 0) + gold
            result_desc += f' (+{gold} 金币)'

    elif effect == 'upgrade_card':
        extra_data['action'] = 'upgrade_card'
        result_desc += ' (请选择要升级的牌)'

    elif effect == 'pick_card':
        from .cards import get_card_rewards
        rewards = get_card_rewards(character, player.get('floor', 1), 3)
        extra_data['card_rewards'] = rewards
        extra_data['action'] = 'pick_card'

    elif effect == 'card':
        from .cards import get_card_rewards
        rewards = get_card_rewards(character, player.get('floor', 1), 1)
        if rewards:
            player.setdefault('deck', []).append(rewards[0])
            extra_data['new_card'] = rewards[0]
            result_desc += f' (获得: {rewards[0]["name"]})'

    elif effect == 'spend_gold_strength':
        gold_cost = value.get('gold', 50) if isinstance(value, dict) else 50
        strength_gain = value.get('strength', 2) if isinstance(value, dict) else 2
        if player.get('gold', 0) >= gold_cost:
            player['gold'] -= gold_cost
            player['strength'] = player.get('strength', 0) + strength_gain
            result_desc += f' (-{gold_cost} 金币, 力量 +{strength_gain})'
        else:
            result_desc = '金币不足！'

    elif effect == 'spend_gold_heal':
        gold_cost = value.get('gold', 30) if isinstance(value, dict) else 30
        hp_gain = value.get('hp', 25) if isinstance(value, dict) else 25
        if player.get('gold', 0) >= gold_cost:
            player['gold'] -= gold_cost
            player['hp'] = min(player['max_hp'], player['hp'] + hp_gain)
            result_desc += f' (-{gold_cost} 金币, +{hp_gain} HP)'
        else:
            result_desc = '金币不足！'

    elif effect == 'strength_check':
        required = value.get('required_strength', 5) if isinstance(value, dict) else 5
        if player.get('strength', 0) >= required:
            from .relics import get_random_relic
            new_relic = get_random_relic('rare')
            if new_relic:
                player.setdefault('relics', []).append(new_relic)
                extra_data['new_relic'] = new_relic
                result_desc += f' (获得稀有遗物: {new_relic["name"]})'
        else:
            result_desc = f'力量不足（需要{required}点）！你无法打破球体。'

    elif effect == 'random':
        # 随机效果
        effects = [
            lambda: player.update({'hp': min(player['max_hp'], player['hp'] + 20)}) or '恢复20HP！',
            lambda: player.update({'hp': max(1, player['hp'] - 10)}) or '失去10HP！',
            lambda: player.update({'gold': player.get('gold', 0) + 50}) or '获得50金币！',
            lambda: player.update({'strength': player.get('strength', 0) + 1}) or '力量+1！',
        ]
        chosen_effect = random.choice(effects)
        result_desc += f' {chosen_effect()}'

    elif effect == 'boss_info':
        result_desc += ' (Boss信息已记录)'

    return player, result_desc, extra_data
