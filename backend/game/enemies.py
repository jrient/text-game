"""敌人系统 - 定义所有敌人和AI"""
import random
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EnemyIntent:
    action: str      # attack, block, buff, special, debuff
    value: int = 0   # 伤害值或格挡值
    times: int = 1   # 次数
    description: str = ""
    debuff_type: str = "weak"  # debuff行动类型：weak / vulnerable


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
        super().__init__('cultist', '邪教徒', random.randint(48, 56))

    def get_next_intent(self) -> EnemyIntent:
        if len(self.move_history) == 0:
            return EnemyIntent('buff', 2, 1, '召唤仪式（每回合+2力量）')
        return EnemyIntent('attack', 8 + self.strength, 1, f'攻击 {8 + self.strength}')


class JawWorm(Enemy):
    def __init__(self):
        super().__init__('jaw_worm', '颌虫', random.randint(44, 52))

    def get_next_intent(self) -> EnemyIntent:
        if len(self.move_history) == 0:
            return EnemyIntent('attack', 13, 1, '撕咬 13')
        r = random.random()
        if r < 0.45:
            return EnemyIntent('attack', 13, 1, '撕咬 13')
        elif r < 0.75:
            return EnemyIntent('block', 5, 1, '蜷缩（格挡 5）')
        return EnemyIntent('attack', 8, 1, '嘶鸣（攻击 8）')


class RedLouse(Enemy):
    def __init__(self):
        super().__init__('red_louse', '红虱', random.randint(18, 25))

    def get_next_intent(self) -> EnemyIntent:
        r = random.random()
        if r < 0.25:
            return EnemyIntent('buff', 3, 1, '自噬（力量+3）')
        return EnemyIntent('attack', random.randint(7, 10), 1, f'撕咬 {random.randint(7,10)}')


class Slime(Enemy):
    def __init__(self, size='acid'):
        if size == 'acid':
            super().__init__('acid_slime_m', '中型酸液史莱姆', random.randint(34, 40))
        else:
            super().__init__('spike_slime_m', '中型尖刺史莱姆', random.randint(34, 40))
        self.slime_type = size

    def get_next_intent(self) -> EnemyIntent:
        r = random.random()
        if r < 0.3:
            return EnemyIntent('attack', 9, 2, '吐酸（2x9伤害）')
        return EnemyIntent('block', 0, 1, '腐蚀（弱化敌人2回合）')


class GremlinNob(Enemy):
    def __init__(self):
        super().__init__('gremlin_nob', '哥布林领袖', random.randint(90, 98))
        self.is_elite = True

    def get_next_intent(self) -> EnemyIntent:
        if len(self.move_history) == 0:
            return EnemyIntent('buff', 2, 1, '愤怒（每次打出技能牌额外承受3伤害）')
        r = random.random()
        if r < 0.33:
            return EnemyIntent('attack', 18, 1, '冲撞 18')
        return EnemyIntent('attack', 8, 2, '斩击 2x8')


class Lagavulin(Enemy):
    def __init__(self):
        super().__init__('lagavulin', '沉睡巨魔', random.randint(115, 120))
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
            return EnemyIntent('attack', 22, 1, '黏液袭击 22')
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


# ===== 第2幕普通敌人 =====
class FungiBeast(Enemy):
    """第2幕普通 - 菌兽（逐渐增强型）"""
    def __init__(self):
        super().__init__('fungi_beast', '菌兽', random.randint(62, 75))

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        if turn % 4 == 0:
            return EnemyIntent('buff', 2, 1, '孢子增强（力量+2）')
        elif turn % 4 == 1:
            dmg = 13 + self.strength
            return EnemyIntent('attack', dmg, 1, f'孢子打击 {dmg}')
        elif turn % 4 == 2:
            dmg = 9 + self.strength
            return EnemyIntent('attack', dmg, 2, f'爆裂孢 2×{dmg}')
        return EnemyIntent('block', 8, 1, '孢子甲（格挡8）')


class CopperGolem(Enemy):
    """第2幕普通 - 铜傀儡（攻守交替型）"""
    def __init__(self):
        super().__init__('copper_golem', '铜傀儡', random.randint(72, 84))

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        if turn % 3 == 0:
            return EnemyIntent('attack', 16, 1, '铁拳 16')
        elif turn % 3 == 1:
            return EnemyIntent('block', 10, 1, '硬化（格挡10）')
        return EnemyIntent('attack', 10, 2, '双击 2×10')


# ===== 第3幕普通敌人 =====
class VoidWalker(Enemy):
    """第3幕普通 - 虚空行者（力量堆叠型）"""
    def __init__(self):
        super().__init__('void_walker', '虚空行者', random.randint(85, 98))

    def get_next_intent(self) -> EnemyIntent:
        if len(self.move_history) == 0:
            return EnemyIntent('buff', 3, 1, '虚空汲取（力量+3）')
        r = random.random()
        if r < 0.55:
            dmg = 18 + self.strength
            return EnemyIntent('attack', dmg, 1, f'暗影打击 {dmg}')
        return EnemyIntent('buff', 2, 1, '汲取（力量+2）')


class DarkSentinel(Enemy):
    """第3幕普通 - 暗影哨兵（重甲重击型）"""
    def __init__(self):
        super().__init__('dark_sentinel', '暗影哨兵', random.randint(108, 122))

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        if turn % 4 == 0:
            return EnemyIntent('block', 16, 1, '暗影护盾（格挡16）')
        elif turn % 4 == 1:
            return EnemyIntent('attack', 22, 1, '能量斩 22')
        elif turn % 4 == 2:
            return EnemyIntent('attack', 11, 2, '双重打击 2×11')
        return EnemyIntent('buff', 2, 1, '强化（力量+2）')


# ===== 第2幕精英敌人 =====
class SerpentDancer(Enemy):
    """第2幕精英 - 毒舞者（虚弱施加型）"""
    def __init__(self):
        super().__init__('serpent_dancer', '毒舞者', random.randint(130, 145))
        self.is_elite = True

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        cycle = turn % 5
        if cycle == 0:
            return EnemyIntent('debuff', 2, 1, '毒雾缠绕（使你虚弱2回合）')
        elif cycle == 1:
            dmg = 18 + self.strength
            return EnemyIntent('attack', dmg, 1, f'毒牙 {dmg}')
        elif cycle == 2:
            return EnemyIntent('buff', 2, 1, '毒液强化（力量+2）')
        elif cycle == 3:
            return EnemyIntent('debuff', 3, 1, '死亡缠绕（使你虚弱3回合）')
        else:
            dmg = 26 + self.strength
            return EnemyIntent('attack', dmg, 1, f'猛烈毒击 {dmg}')


class IronGoliath(Enemy):
    """第2幕精英 - 铁巨人（高格挡重击型）"""
    def __init__(self):
        super().__init__('iron_goliath', '铁巨人', random.randint(160, 178))
        self.is_elite = True

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        cycle = turn % 4
        if cycle == 0:
            return EnemyIntent('block', 28, 1, '铁甲（格挡28）')
        elif cycle == 1:
            return EnemyIntent('attack', 26, 1, '巨拳 26')
        elif cycle == 2:
            return EnemyIntent('attack', 12, 2, '踩踏 2×12')
        else:
            return EnemyIntent('buff', 3, 1, '愤怒（力量+3）')


# ===== 第3幕精英敌人 =====
class VoidKnight(Enemy):
    """第3幕精英 - 虚空骑士（快速力量堆叠型）"""
    def __init__(self):
        super().__init__('void_knight', '虚空骑士', random.randint(190, 210))
        self.is_elite = True

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        cycle = turn % 4
        if cycle == 0:
            return EnemyIntent('buff', 4, 1, '虚空充能（力量+4）')
        elif cycle == 1:
            dmg = 32 + self.strength
            return EnemyIntent('attack', dmg, 1, f'暗影斩 {dmg}')
        elif cycle == 2:
            return EnemyIntent('buff', 2, 1, '虚空汲取（力量+2）')
        else:
            dmg = 22 + self.strength
            return EnemyIntent('attack', dmg, 2, f'虚空爆发 2×{dmg}')


class CorruptedSeer(Enemy):
    """第3幕精英 - 腐化占卜师（易伤施加+高伤）"""
    def __init__(self):
        super().__init__('corrupted_seer', '腐化占卜师', random.randint(180, 200))
        self.is_elite = True

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        cycle = turn % 5
        if cycle == 0:
            return EnemyIntent('debuff', 2, 1, '黑暗祈祷（使你易伤2回合）', 'vulnerable')
        elif cycle == 1:
            dmg = 24 + self.strength
            return EnemyIntent('attack', dmg, 1, f'腐化射线 {dmg}')
        elif cycle == 2:
            return EnemyIntent('block', 18, 1, '虚空护盾（格挡18）')
        elif cycle == 3:
            return EnemyIntent('debuff', 3, 1, '凝视（使你易伤3回合）', 'vulnerable')
        else:
            dmg = 36 + self.strength
            return EnemyIntent('attack', dmg, 1, f'终焉之光 {dmg}')


# ===== Boss =====
class TheGuardian(Enemy):
    """第1幕Boss"""
    def __init__(self):
        super().__init__('the_guardian', '守卫者', random.randint(240, 260))
        self.is_boss = True
        self.mode = 'normal'  # normal / defensive
        self.mode_shift_count = 0

    def get_next_intent(self) -> EnemyIntent:
        turn = len(self.move_history)
        if self.mode == 'normal':
            if turn % 4 == 0:
                return EnemyIntent('attack', 22, 1, '重击 22')
            elif turn % 4 == 1:
                return EnemyIntent('block', 0, 1, '充能（切换防御模式）')
            return EnemyIntent('attack', 9, 2, '扫击 2x9')
        else:
            if turn % 3 == 0:
                return EnemyIntent('block', 20, 1, '保护模式（格挡20）')
            return EnemyIntent('attack', 9, 3, '角刺 3x9')


class HexaGhost(Enemy):
    """第2幕Boss"""
    def __init__(self):
        super().__init__('hexa_ghost', '六角幽灵', random.randint(265, 285))
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
            return EnemyIntent('buff', 4, 1, '仪式（力量+4）')
        return EnemyIntent('attack', 18 + self.strength, 1, f'能量爆发 {18 + self.strength}')


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
    'act2_normal': [FungiBeast, CopperGolem],
    'act2_elite': [SerpentDancer, IronGoliath],
    'act2_boss': [HexaGhost],
    'act3_normal': [VoidWalker, DarkSentinel],
    'act3_elite': [VoidKnight, CorruptedSeer],
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
            description=intent_data.get('description', ''),
            debuff_type=intent_data.get('debuff_type', 'weak'),
        )
    return enemy
