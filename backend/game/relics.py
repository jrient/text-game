"""遗物系统"""
import random
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Relic:
    id: str
    name: str
    description: str
    rarity: str    # starter, common, uncommon, rare, boss, shop

    # 效果参数
    hp_bonus: int = 0           # 增加最大HP
    energy_bonus: int = 0       # 每回合额外能量
    start_block: int = 0        # 战斗开始时格挡
    start_strength: int = 0     # 战斗开始力量
    gold_on_kill: int = 0       # 击杀获得金币
    card_draw: int = 0          # 每回合额外抽牌

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rarity': self.rarity,
        }


# 职业起始遗物
STARTER_RELICS = {
    'warrior': Relic('burning_blood', '燃烧之血', '每场战斗结束恢复6点HP', 'starter', hp_bonus=0),
    'mage': Relic('cracked_core', '破裂核心', '每场战斗开始获得1个闪电法球', 'starter'),
    'assassin': Relic('ring_of_snake', '蛇之戒', '每场战斗开始额外抽2张牌', 'starter', card_draw=2),
}

# 通用遗物池
ALL_RELICS = [
    # 普通
    Relic('anchor', '锚', '每场战斗开始获得10点格挡', 'common', start_block=10),
    Relic('ancient_tea_set', '古茶具', '每次进入休息点额外获得2点能量', 'common'),
    Relic('art_of_war', '兵法', '若一回合内未打出攻击牌，下回合额外获得1点能量', 'common'),
    Relic('bag_of_marbles', '弹珠袋', '每场战斗开始使所有敌人虚弱1回合', 'common'),
    Relic('bag_of_preparation', '准备袋', '每场战斗开始额外抽2张牌', 'common', card_draw=2),
    Relic('blood_vial', '血瓶', '每场战斗开始恢复2点HP', 'common'),
    Relic('bronze_scales', '铜鳞', '受到攻击时反弹3点伤害', 'common'),
    Relic('centennial_puzzle', '百年谜题', '第一次每回合失去HP时抽3张牌', 'common'),
    Relic('ceramic_fish', '陶瓷鱼', '每次将牌加入牌组时获得9金币', 'common'),
    Relic('dream_catcher', '捕梦网', '在休息点时额外获得一次选牌机会', 'common'),
    Relic('happy_flower', '快乐花', '每3回合获得1点能量', 'common'),
    Relic('lantern', '灯笼', '第一回合额外获得1点能量', 'common'),
    Relic('maw_bank', '大颌银行', '每层获得12金币，当购物时停止收益', 'common'),
    Relic('meal_ticket', '餐券', '每次进入商店恢复15点HP', 'common'),
    Relic('nunchaku', '双截棍', '每打出10张攻击牌获得1点能量', 'common'),

    # 非普通
    Relic('bird_faced_urn', '鸟脸瓮', '每次打出能力牌时恢复2点HP', 'uncommon'),
    Relic('calipers', '卡尺', '回合结束时保留至少15点格挡', 'uncommon'),
    Relic('captain_wheel', '船长之轮', '战斗开始时获得力量+3，敏捷+3，格挡+3', 'uncommon', start_strength=3, start_block=3),
    Relic('dead_branch', '枯枝', '每次耗尽一张牌时获得一张随机牌加入手牌', 'uncommon'),
    Relic('du_vu_doll', '巫毒娃娃', '每收集一张诅咒牌力量+1', 'uncommon'),
    Relic('frozen_core', '冰封核心', '若回合结束时法球槽为空，获得一个冰霜法球', 'uncommon'),
    Relic('horn_cleat', '角钳', '前两回合开始时额外获得14点格挡', 'uncommon', start_block=14),
    Relic('ink_bottle', '墨水瓶', '每打出10张牌抽1张牌', 'uncommon'),
    Relic('kunai', '苦无', '每回合打出3张攻击牌获得1点敏捷', 'uncommon'),
    Relic('letter_opener', '拆信刀', '每回合打出3张技能牌对所有敌人造成5点伤害', 'uncommon'),
    Relic('matryoshka', '俄罗斯套娃', '前两个宝箱各给出2个遗物', 'uncommon'),
    Relic('meat_on_the_bone', '骨头上的肉', 'HP低于50%时战斗结束恢复12HP', 'uncommon'),
    Relic('mercury_hourglass', '汞沙漏', '每回合开始对所有敌人造成3点伤害', 'uncommon'),
    Relic('molten_egg', '熔岩蛋', '加入牌组的攻击牌自动升级', 'uncommon'),
    Relic('mummified_hand', '木乃伊手', '每次打出能力牌时随机降低手牌费用1点', 'uncommon'),
    Relic('ornamental_fan', '装饰扇', '每回合打出3张攻击牌获得4点格挡', 'uncommon'),
    Relic('pantograph', '刻字板', '每场Boss战开始恢复25HP', 'uncommon'),
    Relic('pear', '梨', '永久增加10点最大HP', 'uncommon', hp_bonus=10),
    Relic('question_card', '问号牌', '获得牌的选项增加一张', 'uncommon'),
    Relic('shuriken', '飞镖星', '每回合打出3张攻击牌获得1点力量', 'uncommon'),
    Relic('singing_bowl', '鸣碗', '跳过选牌时增加2点最大HP', 'uncommon', hp_bonus=2),
    Relic('strike_dummy', '攻击靶', '带"攻击"名称的牌多造成3点伤害', 'uncommon'),
    Relic('sundial', '日晷', '每洗牌3次获得2点能量', 'uncommon'),
    Relic('the_courier', '信使', '商店中牌的价格降低20%', 'uncommon'),
    Relic('toxic_egg', '毒卵', '加入牌组的技能牌自动升级', 'uncommon'),
    Relic('white_beast_statue', '白兽雕像', '每回合回血2点', 'uncommon'),

    # 稀有
    Relic('black_star', '黑星', '精英战后获得两个遗物选择', 'rare'),
    Relic('busted_crown', '破损王冠', '获得1点能量，每场战斗抽牌减少2', 'rare', energy_bonus=1),
    Relic('calling_bell', '召唤铃', '获得诅咒，以及固定遗物奖励', 'rare'),
    Relic('coffee_dripper', '咖啡滴漏器', '每回合获得1点额外能量，无法在休息点休息', 'rare', energy_bonus=1),
    Relic('dead_cat', '死猫', '最大HP设为1，但获得9张猫命牌', 'rare'),
    Relic('ice_cream', '冰淇淋', '未使用能量保留到下回合', 'rare'),
    Relic('lizard_tail', '蜥蜴尾巴', '第一次死亡时以10%HP存活', 'rare'),
    Relic('mark_of_pain', '痛苦印记', '获得1点每回合能量，但每场战斗开始承受2张伤口', 'rare', energy_bonus=1),
    Relic('philosopher_stone', '哲人石', '获得1点能量，所有敌人力量+1', 'rare', energy_bonus=1),
    Relic('runic_dome', '符文穹顶', '获得1点能量，但无法看到敌人意图', 'rare', energy_bonus=1),
    Relic('slavers_collar', '奴隶主项圈', '休息、购物和事件节点额外获得1点能量', 'rare'),
    Relic('snecko_eye', '蛇蝎之眼', '每回合抽2张额外牌，所有牌费用随机化', 'rare', card_draw=2),
    Relic('sozu', '素珠', '获得1点能量，但无法获得药水', 'rare', energy_bonus=1),
    Relic('tingsha', '叮钹', '每次丢弃牌时对随机敌人造成3点伤害', 'rare'),
    Relic('tough_bandages', '坚韧绷带', '每次丢弃牌时获得3点格挡', 'rare'),
    Relic('true_grit_relic', '强韧', '每次丢弃牌时获得2点格挡', 'common'),
    Relic('turnip', '萝卜', '无法获得虚弱效果', 'uncommon'),
    Relic('unceasing_top', '不停陀螺', '只要手牌为空就持续抽牌', 'uncommon'),

    # Boss遗物
    Relic('astrolabe', '星盘', '变身！将3张牌升级（Boss）', 'boss'),
    Relic('black_blood', '黑血', '燃烧之血升级：战斗结束恢复12HP', 'boss'),
    Relic('frozen_eye', '冰霜之眼', '可以看到抽牌堆顺序', 'boss'),
    Relic('holy_water', '圣水', '起始3张牌加入你的牌组（Boss）', 'boss'),
    Relic('pandoras_box', '潘多拉魔盒', '将所有起始攻击和防御牌替换为随机牌（Boss）', 'boss'),
    Relic('runic_pyramid', '符文金字塔', '回合结束时不弃手牌', 'boss'),
    Relic('sacred_bark', '圣树皮', '药水效果翻倍', 'boss'),
    Relic('slaver_collar', '奴隶项圈', '在非战斗节点获得额外能量', 'boss'),
    Relic('snecko_skull', '蛇蝎头骨', '中毒敌人每回合额外损失1HP', 'boss'),
    Relic('wrist_blade', '腕刃', '费用为0的牌造成额外4点伤害', 'boss'),
    Relic('violet_lotus', '紫莲', '获得额外能量1点（每层恢复后）', 'boss'),
]

# 遗物字典
ALL_RELICS_DICT = {r.id: r for r in ALL_RELICS}
ALL_RELICS_DICT.update({k: v for k, v in STARTER_RELICS.items()})


def get_starter_relic(character: str) -> dict:
    return STARTER_RELICS[character].to_dict()


def get_boss_relic_choices(count: int = 3) -> List[dict]:
    boss_relics = [r for r in ALL_RELICS if r.rarity == 'boss']
    selected = random.sample(boss_relics, min(count, len(boss_relics)))
    return [r.to_dict() for r in selected]


def get_shop_relics(count: int = 2) -> List[dict]:
    shop_pool = [r for r in ALL_RELICS if r.rarity in ('common', 'uncommon')]
    selected = random.sample(shop_pool, min(count, len(shop_pool)))
    return [r.to_dict() for r in selected]


def get_random_relic(rarity: str = None) -> dict:
    if rarity:
        pool = [r for r in ALL_RELICS if r.rarity == rarity]
    else:
        pool = [r for r in ALL_RELICS if r.rarity in ('common', 'uncommon', 'rare')]
    return random.choice(pool).to_dict() if pool else None
