"""卡牌系统 - 定义所有卡牌"""
from dataclasses import dataclass, field
from typing import Optional, List
import random


@dataclass
class Card:
    id: str
    name: str
    description: str
    cost: int
    card_type: str  # attack, skill, power, curse
    character: str  # warrior, mage, assassin, common
    rarity: str     # starter, common, uncommon, rare

    # 效果参数
    damage: int = 0
    block: int = 0
    draw: int = 0
    energy_gain: int = 0
    heal: int = 0

    # 特殊效果
    strength_gain: int = 0
    dexterity_gain: int = 0
    weak_turns: int = 0
    vulnerable_turns: int = 0
    poison_stacks: int = 0
    burn_stacks: int = 0

    # 卡牌修饰符
    exhaust: bool = False       # 打出后移除
    ethereal: bool = False      # 回合结束时移除
    innate: bool = False        # 总是在起手牌中
    unplayable: bool = False    # 不可打出
    retain: bool = False        # 回合结束保留

    # 连击/多段
    hits: int = 1               # 攻击次数
    apply_to_all: bool = False  # 对所有敌人

    # 升级后的值
    upgraded: bool = False

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cost': self.cost,
            'type': self.card_type,
            'character': self.character,
            'rarity': self.rarity,
            'damage': self.damage,
            'block': self.block,
            'draw': self.draw,
            'hits': self.hits,
            'exhaust': self.exhaust,
            'ethereal': self.ethereal,
            'upgraded': self.upgraded,
            'apply_to_all': self.apply_to_all,
            'poison_stacks': self.poison_stacks,
            'burn_stacks': self.burn_stacks,
            'strength_gain': self.strength_gain,
            'weak_turns': self.weak_turns,
            'vulnerable_turns': self.vulnerable_turns,
        }


# ===== 战士卡牌 =====
WARRIOR_CARDS = [
    # 起始牌
    Card('w_strike', '猛击', '造成6点伤害', 1, 'attack', 'warrior', 'starter', damage=6),
    Card('w_defend', '格挡', '获得5点格挡', 1, 'skill', 'warrior', 'starter', block=5),
    Card('w_bash', '重击', '造成8点伤害，使敌人虚弱2回合', 2, 'attack', 'warrior', 'starter', damage=8, weak_turns=2),

    # 普通牌
    Card('w_body_slam', '重拳', '造成等同于格挡值的伤害', 1, 'attack', 'warrior', 'common', damage=0),
    Card('w_clash', '冲撞', '此回合只打出过攻击牌时：造成14点伤害', 0, 'attack', 'warrior', 'common', damage=14),
    Card('w_cleave', '横扫', '对所有敌人造成8点伤害', 1, 'attack', 'warrior', 'common', damage=8, apply_to_all=True),
    Card('w_clothesline', '重拳连击', '造成12点伤害，使敌人虚弱2回合', 2, 'attack', 'warrior', 'common', damage=12, weak_turns=2),
    Card('w_iron_wave', '铁浪', '获得5点格挡并造成5点伤害', 1, 'attack', 'warrior', 'common', damage=5, block=5),
    Card('w_sword_boomerang', '飞旋剑', '随机攻击3次，每次3点伤害', 1, 'attack', 'warrior', 'common', damage=3, hits=3),
    Card('w_twin_strike', '双重打击', '攻击2次，每次5点伤害', 1, 'attack', 'warrior', 'common', damage=5, hits=2),
    Card('w_wild_strike', '狂野打击', '造成12点伤害，将一张创伤加入弃牌堆', 1, 'attack', 'warrior', 'common', damage=12),

    Card('w_armaments', '武装', '获得5点格挡', 1, 'skill', 'warrior', 'common', block=5),
    Card('w_flex', '健壮', '本回合力量+2，回合结束力量-2', 0, 'skill', 'warrior', 'common', strength_gain=2),
    Card('w_havoc', '破坏', '抽一张牌，立即打出后排入弃牌', 1, 'skill', 'warrior', 'common', draw=1),
    Card('w_shrug_it_off', '一笑置之', '获得11点格挡，抽一张牌', 1, 'skill', 'warrior', 'common', block=11, draw=1),
    Card('w_true_grit', '强韧', '获得7点格挡，随机移除手牌一张', 1, 'skill', 'warrior', 'common', block=7),
    Card('w_warcry', '战吼', '抽2张牌', 0, 'skill', 'warrior', 'common', draw=2, exhaust=True),

    Card('w_anger', '愤怒', '造成6点伤害，将一份愤怒加入弃牌堆', 0, 'power', 'warrior', 'common', damage=6),
    Card('w_flame_barrier', '火焰屏障', '获得12点格挡，本回合受到攻击时反弹4点伤害', 2, 'skill', 'warrior', 'common', block=12),

    # 罕见牌
    Card('w_fiend_fire', '恶魔烈焰', '耗尽手牌，每张牌造成7点伤害', 2, 'attack', 'warrior', 'rare', damage=7, exhaust=True),
    Card('w_immolate', '燃烧牺牲', '对所有敌人造成21点伤害，将一张灼伤加入弃牌堆', 2, 'attack', 'warrior', 'rare', damage=21, apply_to_all=True),
    Card('w_limit_break', '极限爆发', '力量翻倍', 1, 'skill', 'warrior', 'rare', exhaust=True, strength_gain=99),
    Card('w_reaper', '死亡镰刀', '对所有敌人造成4点伤害，并恢复等同伤害的生命', 2, 'attack', 'warrior', 'rare', damage=4, apply_to_all=True),

    # 能力牌
    Card('w_barricade', '壁垒', '格挡不在回合结束时消失', 3, 'power', 'warrior', 'rare'),
    Card('w_demon_form', '恶魔形态', '每回合开始获得2点力量', 3, 'power', 'warrior', 'rare', strength_gain=2),
    Card('w_metallicize', '金属化', '每回合结束获得3点格挡', 1, 'power', 'warrior', 'common'),
    Card('w_inflame', '激怒', '永久力量+2', 1, 'power', 'warrior', 'common', strength_gain=2),
]

# ===== 法师卡牌 =====
MAGE_CARDS = [
    # 起始牌
    Card('m_zap', '电击', '造成7点伤害', 1, 'attack', 'mage', 'starter', damage=7),
    Card('m_defend', '防护', '获得4点格挡', 1, 'skill', 'mage', 'starter', block=4),
    Card('m_dualcast', '双重施法', '激活当前法球2次', 1, 'skill', 'mage', 'starter'),

    # 普通牌
    Card('m_cold_snap', '寒冰弹', '造成6点伤害，获得1个冰霜法球', 1, 'attack', 'mage', 'common', damage=6),
    Card('m_compile_driver', '汇编驱动', '造成3+法球数量的伤害', 1, 'attack', 'mage', 'common', damage=6),
    Card('m_go_for_the_eyes', '直击要害', '随机造成3点伤害，使敌人虚弱1回合', 1, 'attack', 'mage', 'common', damage=3, weak_turns=1),
    Card('m_rebound', '反弹', '造成9点伤害，将本牌置于抽牌堆顶', 1, 'attack', 'mage', 'common', damage=9),
    Card('m_stream_of_power', '能量流', '造成15点伤害', 2, 'attack', 'mage', 'common', damage=15),
    Card('m_sweeping_beam', '横扫光束', '对所有敌人造成6点伤害，抽1张牌', 1, 'attack', 'mage', 'common', damage=6, apply_to_all=True, draw=1),
    Card('m_thunder_strike', '雷击', '每有1个闪电法球造成7点伤害', 3, 'attack', 'mage', 'rare', damage=7, hits=3),

    Card('m_aggregate', '聚合', '抽到每4张牌获得1点能量', 1, 'skill', 'mage', 'common', draw=2),
    Card('m_ball_lightning', '球状闪电', '造成7点伤害，获得1个闪电法球', 1, 'attack', 'mage', 'common', damage=7),
    Card('m_capacitor', '电容器', '获得3个闪电法球', 1, 'skill', 'mage', 'common'),
    Card('m_defragment', '碎片整理', '能量+1', 1, 'power', 'mage', 'common', energy_gain=1),
    Card('m_skim', '略读', '抽3张牌', 1, 'skill', 'mage', 'common', draw=3),
    Card('m_stack', '叠加', '获得等同弃牌堆数量的格挡', 1, 'skill', 'mage', 'common', block=6),
    Card('m_static_discharge', '静电释放', '每次受到非法球伤害时激活闪电法球1次', 1, 'power', 'mage', 'common'),

    # 罕见牌
    Card('m_all_for_one', '全力一击', '造成10点伤害，将弃牌堆中0费牌全部拿回手牌', 2, 'attack', 'mage', 'rare', damage=10),
    Card('m_hyperbeam', '超光束', '对所有敌人造成26点伤害，你的敏捷-3', 3, 'attack', 'mage', 'rare', damage=26, apply_to_all=True),
    Card('m_meteor_strike', '陨石打击', '造成24点伤害，获得3个等离子体法球', 5, 'attack', 'mage', 'rare', damage=24),

    Card('m_biased_cognition', '偏向认知', '能量+1，每回合开始专注-1', 1, 'power', 'mage', 'rare', energy_gain=1),
    Card('m_creative_ai', '创意智能', '每回合开始获得1张随机能力牌', 3, 'power', 'mage', 'rare'),
    Card('m_echo_form', '回声形态', '首次打出的牌将被触发2次', 3, 'power', 'mage', 'rare'),
]

# ===== 刺客卡牌 =====
ASSASSIN_CARDS = [
    # 起始牌
    Card('a_strike', '刺击', '造成6点伤害', 1, 'attack', 'assassin', 'starter', damage=6),
    Card('a_defend', '闪躲', '获得5点格挡', 1, 'skill', 'assassin', 'starter', block=5),
    Card('a_survivor', '幸存', '获得8点格挡，丢弃1张牌', 1, 'skill', 'assassin', 'starter', block=8),

    # 普通牌
    Card('a_acrobatics', '杂技', '抽3张牌，丢弃1张', 1, 'skill', 'assassin', 'common', draw=3),
    Card('a_backflip', '后空翻', '获得5点格挡，抽2张牌', 2, 'skill', 'assassin', 'common', block=5, draw=2),
    Card('a_blade_dance', '刀光剑影', '获得3张匕首加入手牌', 1, 'skill', 'assassin', 'common'),
    Card('a_cloak_and_dagger', '隐蔽匕首', '获得6点格挡，获得1张匕首', 1, 'skill', 'assassin', 'common', block=6),
    Card('a_dagger_spray', '匕首喷射', '对所有敌人造2次3点伤害', 1, 'attack', 'assassin', 'common', damage=3, hits=2, apply_to_all=True),
    Card('a_dash', '冲刺', '获得10点格挡，造成10点伤害', 2, 'attack', 'assassin', 'common', damage=10, block=10),
    Card('a_deadly_poison', '致命毒素', '对敌人施加5层毒素', 1, 'skill', 'assassin', 'common', poison_stacks=5),
    Card('a_deflect', '偏转', '获得4点格挡', 0, 'skill', 'assassin', 'common', block=4, exhaust=True),
    Card('a_doppelganger', '替身', '根据丢弃牌数量抽取等量牌', 1, 'skill', 'assassin', 'common', draw=2),
    Card('a_flechettes', '飞镖', '每有1张技能牌在手：造成4点伤害', 1, 'attack', 'assassin', 'common', damage=4, hits=2),
    Card('a_footwork', '步法', '敏捷+2', 1, 'power', 'assassin', 'common', dexterity_gain=2),
    Card('a_leg_sweep', '扫腿', '使敌人虚弱3回合，获得11点格挡', 2, 'skill', 'assassin', 'common', block=11, weak_turns=3),
    Card('a_neutralize', '使敌软弱', '造成3点伤害，使敌人虚弱1回合', 0, 'attack', 'assassin', 'common', damage=3, weak_turns=1),
    Card('a_predator', '猎手', '造成15点伤害，在下一回合开始抽2张牌', 2, 'attack', 'assassin', 'common', damage=15, draw=1),
    Card('a_quick_slash', '快斩', '造成8点伤害，抽1张牌', 1, 'attack', 'assassin', 'common', damage=8, draw=1),
    Card('a_slice', '斩击', '造成6点伤害', 0, 'attack', 'assassin', 'common', damage=6),
    Card('a_sneaky_strike', '暗袭', '此回合丢弃过牌时：造成12点伤害，获得2点能量', 2, 'attack', 'assassin', 'common', damage=12),
    Card('a_sucker_punch', '偷袭', '造成7点伤害，使敌人虚弱1回合', 1, 'attack', 'assassin', 'common', damage=7, weak_turns=1),

    # 罕见牌
    Card('a_adrenaline', '肾上腺素', '获得2点能量，抽2张牌', 0, 'skill', 'assassin', 'rare', draw=2, energy_gain=2, exhaust=True),
    Card('a_all_out_attack', '全力攻击', '对所有敌人造成10点伤害，随机丢弃1张牌', 1, 'attack', 'assassin', 'rare', damage=10, apply_to_all=True),
    Card('a_bullet_time', '子弹时间', '本回合牌费用为0，但无法抽牌', 3, 'skill', 'assassin', 'rare'),
    Card('a_burst', '爆发', '接下来打出的技能牌触发2次', 1, 'skill', 'assassin', 'rare'),
    Card('a_corpse_explosion', '尸爆', '对敌人施加6层毒，敌人死亡时对所有敌人造成等同其生命上限的伤害', 2, 'skill', 'assassin', 'rare', poison_stacks=6),
    Card('a_die_die_die', '杀杀杀', '对所有敌人造成13点伤害', 1, 'attack', 'assassin', 'rare', damage=13, apply_to_all=True, exhaust=True),
    Card('a_envenom', '毒化', '每次无升级攻击牌命中敌人时施加1层毒', 2, 'power', 'assassin', 'rare', poison_stacks=1),
    Card('a_glass_knife', '玻璃匕首', '造成2x12点伤害，每次使用后伤害-2', 1, 'attack', 'assassin', 'rare', damage=12, hits=2),
    Card('a_grand_finale', '终幕', '抽牌堆为空时：造成50点伤害', 0, 'attack', 'assassin', 'rare', damage=50),
    Card('a_phantasmal_killer', '幻影杀手', '下一次攻击造成双倍伤害', 1, 'skill', 'assassin', 'rare', exhaust=True),
]

# ===== 通用卡牌（诅咒/状态）=====
COMMON_CARDS = [
    Card('curse_wound', '创伤', '诅咒：无法被打出', 'X', 'curse', 'common', 'curse', unplayable=True),
    Card('curse_burn', '灼伤', '回合结束失去1点HP', 'X', 'curse', 'common', 'curse', unplayable=True),
    Card('curse_dazed', '眩晕', '以太：回合结束移除', 0, 'status', 'common', 'curse', ethereal=True, unplayable=True),
]

# 所有卡牌字典
ALL_CARDS = {}
for card in WARRIOR_CARDS + MAGE_CARDS + ASSASSIN_CARDS + COMMON_CARDS:
    ALL_CARDS[card.id] = card


def get_starter_deck(character: str) -> List[dict]:
    """获取职业初始牌组"""
    starters = {
        'warrior': [
            ('w_strike', 5), ('w_defend', 4), ('w_bash', 1)
        ],
        'mage': [
            ('m_zap', 4), ('m_defend', 4), ('m_dualcast', 1)
        ],
        'assassin': [
            ('a_strike', 5), ('a_defend', 4), ('a_survivor', 1)
        ]
    }
    deck = []
    for card_id, count in starters.get(character, []):
        for _ in range(count):
            deck.append(dict(ALL_CARDS[card_id].to_dict()))
    return deck


def get_card_rewards(character: str, floor: int, count: int = 3) -> List[dict]:
    """获取战斗奖励卡牌（随机3张）"""
    # 按稀有度权重
    if floor < 10:
        pool = [c for c in (WARRIOR_CARDS if character == 'warrior' else
                             MAGE_CARDS if character == 'mage' else ASSASSIN_CARDS)
                if c.rarity in ('common', 'uncommon') and c.rarity != 'starter']
    else:
        pool = [c for c in (WARRIOR_CARDS if character == 'warrior' else
                             MAGE_CARDS if character == 'mage' else ASSASSIN_CARDS)
                if c.rarity != 'starter']

    selected = random.sample(pool, min(count, len(pool)))
    return [c.to_dict() for c in selected]


def get_shop_cards(character: str) -> List[dict]:
    """获取商店卡牌列表"""
    char_cards = (WARRIOR_CARDS if character == 'warrior' else
                  MAGE_CARDS if character == 'mage' else ASSASSIN_CARDS)
    pool = [c for c in char_cards if c.rarity in ('common', 'uncommon', 'rare')]
    selected = random.sample(pool, min(5, len(pool)))
    return [c.to_dict() for c in selected]
