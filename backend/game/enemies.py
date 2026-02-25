"""敌人系统 - 定义所有敌人和AI"""
import random
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EnemyIntent:
    action: str      # attack, block, buff, special
    value: int = 0   # 伤害值或格挡值
    times: int = 1   # 次数
    description: str = ""


@dataclass
class Enemy:
    id: str
    name: str
    max_hp: int

    # 状态
    hp: int = 0
    block: int = 0

    # 战斗属性
    strength: int = 0
    dexterity: int = 0

    # 状态效果
    poison: int = 0
    burn: int = 0
    weak_turns: int = 0
    vulnerable_turns: int = 0
    ritual: int = 0      # 每回合获得力量

    # AI
    move_history: List[str] = field(default_factory=list)
    current_intent: Optional[EnemyIntent] = None

    # 特殊属性
    is_boss: bool = False
    is_elite: bool = False

    def __post_init__(self):
        if self.hp == 0:
            self.hp = self.max_hp

    def get_next_intent(self) -> EnemyIntent:
        """由子类重写，获取下一个行动意图"""
        return EnemyIntent('attack', 6, 1, f'攻击 6')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'block': self.block,
            'strength': self.strength,
            'dexterity': self.dexterity,
            'poison': self.poison,
            'burn': self.burn,
            'weak_turns': self.weak_turns,
            'vulnerable_turns': self.vulnerable_turns,
            'is_boss': self.is_boss,
            'is_elite': self.is_elite,
            'intent': self.current_intent.__dict__ if self.current_intent else None
        }


class Cultist(Enemy):
    def __init__(self):
        super().__init__('cultist', '邪教徒', random.randint(40, 48))

    def get_next_intent(self) -> EnemyIntent:
        if len(self.move_history) == 0:
            return EnemyIntent('buff', 2, 1, '召唤仪式（每回合+2力量）')
        return EnemyIntent('attack', 5 + self.strength, 1, f'攻击 {5 + self.strength}')


class JawWorm(Enemy):
    def __init__(self):
        super().__init__('jaw_worm', '颌虫', random.randint(36, 42))

    def get_next_intent(self) -> EnemyIntent:
        if len(self.move_history) == 0:
            return EnemyIntent('attack', 9, 1, '撕咬 9')
        r = random.random()
        if r < 0.45:
            return EnemyIntent('attack', 9, 1, '撕咬 9')
        elif r < 0.75:
            return EnemyIntent('block', 5, 1, '蜷缩（格挡 5）')
        return EnemyIntent('attack', 6, 1, '嘶鸣（攻击 6）')


class RedLouse(Enemy):
    def __init__(self):
        super().__init__('red_louse', '红虱', random.randint(8, 13))

    def get_next_intent(self) -> EnemyIntent:
        r = random.random()
        if r < 0.25:
            return EnemyIntent('buff', 3, 1, '自噬（力量+3）')
        return EnemyIntent('attack', random.randint(5, 7), 1, f'撕咬 {random.randint(5,7)}')


class Slime(Enemy):
    def __init__(self, size='acid'):
        if size == 'acid':
            super().__init__('acid_slime_m', '中型酸液史莱姆', random.randint(28, 32))
        else:
            super().__init__('spike_slime_m', '中型尖刺史莱姆', random.randint(28, 32))
        self.slime_type = size

    def get_next_intent(self) -> EnemyIntent:
        r = random.random()
        if r < 0.3:
            return EnemyIntent('attack', 7, 2, '吐酸（2x7伤害）')
        return EnemyIntent('block', 0, 1, '腐蚀（弱化敌人2回合）')


class GremlinNob(Enemy):
    def __init__(self):
        super().__init__('gremlin_nob', '哥布林领袖', random.randint(82, 86))
        self.is_elite = True

    def get_next_intent(self) -> EnemyIntent:
        if len(self.move_history) == 0:
            return EnemyIntent('buff', 2, 1, '愤怒（每次打出技能牌额外承受3伤害）')
        r = random.random()
        if r < 0.33:
            return EnemyIntent('attack', 14, 1, '冲撞 14')
        return EnemyIntent('attack', 6, 2, '斩击 2x6')


class Lagavulin(Enemy):
    def __init__(self):
        super().__init__('lagavulin', '沉睡巨魔', random.randint(109, 111))
        self.is_elite = True
        self.sleeping = True

    def get_next_intent(self) -> EnemyIntent:
        if len(self.move_history) < 3 and self.sleeping:
            return EnemyIntent('special', 0, 1, '沉睡中...')
        if len(self.move_history) == 3:
            self.sleeping = False
            return EnemyIntent('buff', 0, 1, '觉醒（力量-1，敏捷-1）')
        r = random.random()
        if r < 0.45:
            return EnemyIntent('attack', 18, 1, '黏液袭击 18')
        return EnemyIntent('buff', 0, 1, '虹吸（从玩家偷取力量和敏捷各1点）')


class SentryPair(Enemy):
    def __init__(self):
        super().__init__('sentry', '哨兵', random.randint(38, 42))
        self.is_elite = True

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        if turn % 3 == 0:
            return EnemyIntent('block', 0, 1, '射击（将眩晕加入弃牌堆）')
        return EnemyIntent('attack', 9, 1, '激光束 9')


# ===== Boss =====
class TheGuardian(Enemy):
    """第1幕Boss"""
    def __init__(self):
        super().__init__('the_guardian', '守卫者', random.randint(230, 240))
        self.is_boss = True
        self.mode = 'normal'  # normal / defensive
        self.mode_shift_count = 0

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        if self.mode == 'normal':
            if turn % 4 == 0:
                return EnemyIntent('attack', 18, 1, '重击 18')
            elif turn % 4 == 1:
                return EnemyIntent('block', 0, 1, '充能（切换防御模式）')
            return EnemyIntent('attack', 9, 2, '扫击 2x9')
        else:
            if turn % 3 == 0:
                return EnemyIntent('block', 20, 1, '保护模式（格挡20）')
            return EnemyIntent('attack', 7, 3, '角刺 3x7')


class HexaGhost(Enemy):
    """第2幕Boss"""
    def __init__(self):
        super().__init__('hexa_ghost', '六角幽灵', random.randint(250, 265))
        self.is_boss = True
        self.ritual_stacks = 0

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        if turn % 7 == 0:
            return EnemyIntent('special', 0, 1, '召唤（将3张灼伤加入弃牌堆）')
        elif turn % 7 < 3:
            dmg = 6 + self.strength
            return EnemyIntent('attack', dmg, 1, f'折磨 {dmg}')
        elif turn % 7 == 3:
            return EnemyIntent('buff', 3, 1, '仪式（力量+3）')
        return EnemyIntent('attack', 14 + self.strength, 1, f'能量爆发 {14 + self.strength}')


class CorruptHeart(Enemy):
    """第3幕最终Boss"""
    def __init__(self):
        super().__init__('corrupt_heart', '腐化之心', random.randint(750, 800))
        self.is_boss = True
        self.invincible = True
        self.invincible_turns = 4

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        if self.invincible and turn < 4:
            return EnemyIntent('special', 0, 1, f'调试模式（{4-turn}回合后可被伤害）')
        self.invincible = False
        if turn % 3 == 0:
            return EnemyIntent('attack', 12, 3, '橙色光束 3x12')
        elif turn % 3 == 1:
            return EnemyIntent('buff', 0, 1, '回血（恢复100HP）')
        return EnemyIntent('special', 0, 1, '诅咒（将10张诅咒加入牌组）')


# 地图节点敌人池
ENEMY_POOLS = {
    'act1_normal': [Cultist, JawWorm, RedLouse, Slime],
    'act1_elite': [GremlinNob, Lagavulin, SentryPair],
    'act1_boss': [TheGuardian],
    'act2_normal': [Cultist, JawWorm, Slime, GremlinNob],
    'act2_elite': [Lagavulin, SentryPair, GremlinNob],
    'act2_boss': [HexaGhost],
    'act3_normal': [GremlinNob, SentryPair, Lagavulin],
    'act3_elite': [Lagavulin, SentryPair, GremlinNob],
    'act3_boss': [CorruptHeart],
}


def create_enemy(enemy_type: str, floor: int) -> Enemy:
    """根据类型和楼层创建敌人"""
    act = 1 if floor <= 16 else (2 if floor <= 33 else 3)

    if enemy_type == 'normal':
        pool = ENEMY_POOLS[f'act{act}_normal']
    elif enemy_type == 'elite':
        pool = ENEMY_POOLS[f'act{act}_elite']
    elif enemy_type == 'boss':
        pool = ENEMY_POOLS[f'act{act}_boss']
    else:
        pool = ENEMY_POOLS['act1_normal']

    enemy_class = random.choice(pool)
    enemy = enemy_class()
    # 缩放HP
    enemy.current_intent = enemy.get_next_intent()
    return enemy


def create_enemy_from_dict(data: dict) -> Enemy:
    """从字典重建敌人对象（用于游戏状态恢复）"""
    enemy = Enemy(
        id=data['id'],
        name=data['name'],
        max_hp=data['max_hp'],
        hp=data['hp'],
        block=data.get('block', 0),
        strength=data.get('strength', 0),
        dexterity=data.get('dexterity', 0),
        poison=data.get('poison', 0),
        weak_turns=data.get('weak_turns', 0),
        vulnerable_turns=data.get('vulnerable_turns', 0),
        is_boss=data.get('is_boss', False),
        is_elite=data.get('is_elite', False),
    )
    if data.get('intent'):
        intent_data = data['intent']
        enemy.current_intent = EnemyIntent(
            action=intent_data['action'],
            value=intent_data.get('value', 0),
            times=intent_data.get('times', 1),
            description=intent_data.get('description', '')
        )
    return enemy
