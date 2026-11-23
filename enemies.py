"""Ennemis du TP4.

Les monstres du TP3 (homework_monsters.py) ne sont pas modifies. On ajoute:
  - de nouvelles sous-classes de WalkingMonster (Ice, Poison, Teleport, Tank, Boss...),
  - Enemy: un monstre + un comportement (Strategy) + une attaque (Strategy) + des etats,
  - EnemyFactory: cree un Enemy a partir d'une cle ("normal", "ice", ...) et du niveau.
"""
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

from homework_monsters import (
    DamageCalculator, FastMonster, FlyingMonster, Health, NormalMonster, ResistantDamage,
    ShieldDamage, ShooterMonster, StrongMonster, VulnerableDamage, WalkingMonster, Weapon,
)
from tp4.settings import HEIGHT, WIDTH


# ======================================================================
# DIP: combiner plusieurs calculateurs de degats
# ======================================================================
class CompositeDamage(DamageCalculator):
    def __init__(self, *calculators):
        self.calculators = calculators

    def calculate(self, weapon):
        damage = weapon.damage
        for calc in self.calculators:
            damage = calc.calculate(Weapon(weapon.name, damage, weapon.kind))
        return int(damage)


# ======================================================================
# Nouveaux monstres (OCP: simples sous-classes)
# ======================================================================
class IceMonster(WalkingMonster):
    def __init__(self, x, y):
        super().__init__("Ice Monster", x, y, speed=1.6, max_hp=110,
                         damage_calculator=CompositeDamage(ResistantDamage("ice", 0.2),
                                                           VulnerableDamage("fire", 1.5)))


class PoisonMonster(WalkingMonster):
    def __init__(self, x, y):
        super().__init__("Poison Monster", x, y, speed=1.9, max_hp=90,
                         damage_calculator=VulnerableDamage("fire", 1.3))


class TeleportMonster(WalkingMonster):
    def __init__(self, x, y):
        super().__init__("Teleport Monster", x, y, speed=2.2, max_hp=80)


class TankMonster(WalkingMonster):
    SIZE = 70

    def __init__(self, x, y):
        super().__init__("Tank Monster", x, y, speed=0.8, max_hp=400,
                         damage_calculator=CompositeDamage(ShieldDamage(15),
                                                           ResistantDamage("bullet", 0.6)))


class BossMonster(WalkingMonster):
    SIZE = 90


class GolemBoss(BossMonster):
    def __init__(self, x, y):
        super().__init__("Boss Golem", x, y, speed=1.0, max_hp=900,
                         damage_calculator=ShieldDamage(8))


class FrostBoss(BossMonster):
    def __init__(self, x, y):
        super().__init__("Boss Frost", x, y, speed=1.3, max_hp=800,
                         damage_calculator=CompositeDamage(ResistantDamage("ice", 0.1),
                                                           VulnerableDamage("fire", 1.6)))


class ToxicBoss(BossMonster):
    def __init__(self, x, y):
        super().__init__("Boss Toxic", x, y, speed=1.5, max_hp=750)


# ======================================================================
# Contexte donne aux comportements
# ======================================================================
class AIContext:
    def __init__(self, px, py, enemies, frame, player_shots=()):
        self.px, self.py = px, py              # centre du joueur
        self.enemies = enemies
        self.frame = frame
        self.player_shots = player_shots
        self.events = []                       # ex: ("teleport", x0, y0, x1, y1)


def _unit(dx, dy):
    d = math.hypot(dx, dy)
    if d == 0:
        return 0.0, 0.0, 0.0
    return dx / d, dy / d, d


# ======================================================================
# Comportements de deplacement (Strategy)
# ======================================================================
class Behavior(ABC):
    @abstractmethod
    def move(self, enemy, ctx):
        pass


class ChaseBehavior(Behavior):
    def move(self, enemy, ctx):
        enemy.step_towards(ctx.px, ctx.py)


class EvadeBehavior(Behavior):
    """Poursuite en zigzag + esquive des tirs du joueur."""

    def __init__(self, amplitude=1.1):
        self.amplitude = amplitude

    def move(self, enemy, ctx):
        s = enemy.monster.speed * enemy.speed_factor
        for shot in ctx.player_shots:
            sx, sy = shot.x - enemy.cx, shot.y - enemy.cy
            if math.hypot(sx, sy) < 110:
                vx, vy, _ = _unit(shot.vx, shot.vy)
                if -sx * vx - sy * vy > 0:                      # le tir arrive sur nous
                    side = 1 if sx * vy - sy * vx > 0 else -1
                    enemy.move_by(-vy * side * s * 1.6, vx * side * s * 1.6)
                    return
        ux, uy, _ = _unit(ctx.px - enemy.cx, ctx.py - enemy.cy)
        wave = math.sin(ctx.frame * 0.07 + enemy.phase) * self.amplitude
        enemy.move_by((ux - uy * wave) * s, (uy + ux * wave) * s)


class GroupAttackBehavior(Behavior):
    """Les ennemis du groupe encerclent le joueur puis foncent tous ensemble."""

    def __init__(self, radius=130):
        self.radius = radius

    def move(self, enemy, ctx):
        group = [e for e in ctx.enemies if e.alive and e.group_attack]
        n = max(1, len(group))
        idx = group.index(enemy) if enemy in group else 0
        rush = ctx.frame % 420 > 300 or n == 1
        if rush:
            enemy.step_towards(ctx.px, ctx.py, 1.25)
            return
        angle = math.tau * idx / n + ctx.frame * 0.01
        enemy.step_towards(ctx.px + math.cos(angle) * self.radius,
                           ctx.py + math.sin(angle) * self.radius)


class KeepDistanceBehavior(Behavior):
    """Reste a bonne distance pour tirer."""

    def __init__(self, preferred=260, tolerance=40):
        self.preferred, self.tolerance = preferred, tolerance

    def move(self, enemy, ctx):
        ux, uy, d = _unit(ctx.px - enemy.cx, ctx.py - enemy.cy)
        s = enemy.monster.speed * enemy.speed_factor
        if d > self.preferred + self.tolerance:
            enemy.move_by(ux * s, uy * s)
        elif d < self.preferred - self.tolerance:
            enemy.move_by(-ux * s * 1.1, -uy * s * 1.1)
        else:
            sign = 1 if enemy.phase > 3 else -1
            enemy.move_by(-uy * s * 0.5 * sign, ux * s * 0.5 * sign)


class FleeBehavior(Behavior):
    def move(self, enemy, ctx):
        enemy.step_away(ctx.px, ctx.py, 1.1)


class LowHealthFlee(Behavior):
    """Decorateur: fuit quand la vie est basse, sinon delegue."""

    def __init__(self, inner, threshold=0.2):
        self.inner, self.threshold = inner, threshold

    def move(self, enemy, ctx):
        if enemy.hp_ratio < self.threshold:
            enemy.step_away(ctx.px, ctx.py, 1.1)
        else:
            self.inner.move(enemy, ctx)


class TeleportBehavior(Behavior):
    def __init__(self, inner, interval=150):
        self.inner, self.interval = inner, interval
        self.timer = random.randint(0, interval // 2)

    def move(self, enemy, ctx):
        self.timer += 1
        if self.timer < self.interval:
            self.inner.move(enemy, ctx)
            return
        self.timer = 0
        old = (enemy.cx, enemy.cy)
        angle, dist = random.uniform(0, math.tau), random.uniform(110, 170)
        enemy.place(ctx.px + math.cos(angle) * dist, ctx.py + math.sin(angle) * dist)
        ctx.events.append(("teleport", old[0], old[1], enemy.cx, enemy.cy))


# ======================================================================
# Attaques a distance (Strategy)
# ======================================================================
class AttackPattern(ABC):
    @abstractmethod
    def update(self, enemy, ctx):
        """Retourne une liste de tirs: (x, y, vx, vy, cle_de_tir)."""


class ProjectileAttack(AttackPattern):
    def __init__(self, shot_key, interval, count=1, spread=0.0):
        from tp4.weapons import ENEMY_SHOTS
        self.spec = ENEMY_SHOTS[shot_key]
        self.shot_key, self.interval, self.count, self.spread = shot_key, interval, count, spread
        self.timer = random.randint(0, interval // 2)

    def update(self, enemy, ctx):
        self.timer += 1
        if self.timer < self.interval:
            return []
        self.timer = 0
        base = math.atan2(ctx.py - enemy.cy, ctx.px - enemy.cx)
        shots = []
        for i in range(self.count):
            a = base + (i - (self.count - 1) / 2) * self.spread
            shots.append((enemy.cx, enemy.cy, math.cos(a) * self.spec.speed,
                          math.sin(a) * self.spec.speed, self.shot_key))
        return shots


class RadialBurstAttack(AttackPattern):
    """Salve circulaire; le boss s'enrage sous 50% de vie."""

    def __init__(self, shot_key, interval, count):
        from tp4.weapons import ENEMY_SHOTS
        self.spec = ENEMY_SHOTS[shot_key]
        self.shot_key, self.interval, self.count = shot_key, interval, count
        self.timer = 0

    def update(self, enemy, ctx):
        enraged = enemy.hp_ratio < 0.5
        self.timer += 1
        if self.timer < self.interval * (0.7 if enraged else 1.0):
            return []
        self.timer = 0
        n = int(self.count * (1.5 if enraged else 1.0))
        offset = random.uniform(0, math.tau)
        return [(enemy.cx, enemy.cy,
                 math.cos(offset + math.tau * i / n) * self.spec.speed,
                 math.sin(offset + math.tau * i / n) * self.spec.speed, self.shot_key)
                for i in range(n)]


class CompositeAttack(AttackPattern):
    def __init__(self, *patterns):
        self.patterns = patterns

    def update(self, enemy, ctx):
        shots = []
        for p in self.patterns:
            shots += p.update(enemy, ctx)
        return shots


# ======================================================================
# Enemy: monstre + comportement + attaque + etats
# ======================================================================
class Enemy:
    def __init__(self, key, monster, behavior, attack=None, xp=10, coins=5,
                 contact_damage=8, group_attack=False, is_boss=False, color=(220, 20, 60)):
        self.key, self.monster = key, monster
        self.behavior, self.attack = behavior, attack
        self.xp, self.coins = xp, coins
        self.contact_damage, self.group_attack = contact_damage, group_attack
        self.is_boss, self.color = is_boss, color
        self.slow_timer, self.slow_factor = 0, 1.0
        self.flash = 0
        self.age = 0
        self.phase = random.uniform(0, 6.28)
        self.facing_right = False

    # ---- acces pratiques ----
    @property
    def x(self):
        return self.monster.x

    @property
    def y(self):
        return self.monster.y

    @property
    def cx(self):
        return self.monster.x + self.monster.SIZE / 2

    @property
    def cy(self):
        return self.monster.y + self.monster.SIZE / 2

    @property
    def alive(self):
        return self.monster.alive

    @property
    def hp_ratio(self):
        return self.monster.health.ratio

    @property
    def speed_factor(self):
        return self.slow_factor if self.slow_timer > 0 else 1.0

    # ---- etats ----
    def apply_slow(self, frames, factor):
        self.slow_timer, self.slow_factor = frames, factor

    # ---- mouvement ----
    def move_by(self, dx, dy):
        m = self.monster
        m.x = max(0.0, min(WIDTH - m.SIZE, m.x + dx))
        m.y = max(0.0, min(HEIGHT - m.SIZE, m.y + dy))

    def place(self, cx, cy):
        m = self.monster
        m.x = max(0.0, min(WIDTH - m.SIZE, cx - m.SIZE / 2))
        m.y = max(0.0, min(HEIGHT - m.SIZE, cy - m.SIZE / 2))

    def step_towards(self, tx, ty, mult=1.0):
        ux, uy, _ = _unit(tx - self.cx, ty - self.cy)
        s = self.monster.speed * self.speed_factor * mult
        self.move_by(ux * s, uy * s)

    def step_away(self, tx, ty, mult=1.0):
        ux, uy, _ = _unit(tx - self.cx, ty - self.cy)
        s = self.monster.speed * self.speed_factor * mult
        self.move_by(-ux * s, -uy * s)

    def update(self, ctx):
        self.age += 1
        self.flash = max(0, self.flash - 1)
        self.slow_timer = max(0, self.slow_timer - 1)
        self.behavior.move(self, ctx)
        self.facing_right = ctx.px > self.cx
        return self.attack.update(self, ctx) if self.attack else []


# ======================================================================
# Fabrique (registre extensible)
# ======================================================================
@dataclass
class EnemySpec:
    monster_cls: type
    behavior: Callable
    attack: Callable = lambda: None
    xp: int = 10
    coins: int = 5
    contact_damage: int = 8
    group_attack: bool = False
    is_boss: bool = False
    color: tuple = (220, 20, 60)


ENEMY_SPECS = {
    "normal": EnemySpec(NormalMonster, lambda: LowHealthFlee(GroupAttackBehavior()),
                        xp=10, coins=4, group_attack=True, color=(220, 20, 60)),
    "fast": EnemySpec(FastMonster, lambda: EvadeBehavior(),
                      xp=12, coins=5, color=(255, 140, 0)),
    "flying": EnemySpec(FlyingMonster, lambda: LowHealthFlee(EvadeBehavior(1.6)),
                        xp=15, coins=6, color=(160, 100, 255)),
    "shooter": EnemySpec(ShooterMonster, lambda: KeepDistanceBehavior(260),
                         lambda: ProjectileAttack("spit", 90),
                         xp=18, coins=8, color=(0, 170, 170)),
    "strong": EnemySpec(StrongMonster, lambda: ChaseBehavior(),
                        xp=30, coins=12, contact_damage=12, color=(130, 0, 0)),
    "ice": EnemySpec(IceMonster, lambda: KeepDistanceBehavior(230),
                     lambda: ProjectileAttack("frost", 110, count=2, spread=0.3),
                     xp=25, coins=10, color=(130, 220, 255)),
    "poison": EnemySpec(PoisonMonster, lambda: LowHealthFlee(EvadeBehavior()),
                        lambda: ProjectileAttack("venom", 130),
                        xp=22, coins=9, color=(110, 200, 60)),
    "teleport": EnemySpec(TeleportMonster, lambda: TeleportBehavior(ChaseBehavior(), 150),
                          xp=28, coins=11, color=(230, 80, 230)),
    "tank": EnemySpec(TankMonster, lambda: ChaseBehavior(),
                      xp=45, coins=18, contact_damage=16, color=(90, 100, 110)),
    "boss_golem": EnemySpec(GolemBoss, lambda: ChaseBehavior(),
                            lambda: CompositeAttack(ProjectileAttack("boss", 80, 3, 0.25),
                                                    RadialBurstAttack("boss", 200, 10)),
                            xp=200, coins=100, contact_damage=20, is_boss=True,
                            color=(150, 90, 40)),
    "boss_frost": EnemySpec(FrostBoss, lambda: KeepDistanceBehavior(250),
                            lambda: CompositeAttack(ProjectileAttack("frost", 60, 3, 0.3),
                                                    RadialBurstAttack("frost", 220, 12)),
                            xp=220, coins=110, contact_damage=18, is_boss=True,
                            color=(60, 140, 230)),
    "boss_toxic": EnemySpec(ToxicBoss, lambda: TeleportBehavior(KeepDistanceBehavior(220), 200),
                            lambda: CompositeAttack(ProjectileAttack("venom", 50, 2, 0.35),
                                                    RadialBurstAttack("venom", 180, 14)),
                            xp=240, coins=120, contact_damage=18, is_boss=True,
                            color=(80, 160, 40)),
}


class EnemyFactory:
    def __init__(self, specs=None):
        self.specs = specs or ENEMY_SPECS

    def monster_class(self, key):
        return self.specs[key].monster_cls

    def create(self, key, x, y, hp_mult=1.0, speed_mult=1.0):
        spec = self.specs[key]
        monster = spec.monster_cls(x, y)
        monster.health = Health(int(monster.health.max_hp * hp_mult))
        monster.speed *= speed_mult
        reward = 1 + (hp_mult - 1) * 0.5
        return Enemy(key, monster, spec.behavior(), spec.attack(),
                     xp=int(spec.xp * reward), coins=int(spec.coins * reward),
                     contact_damage=spec.contact_damage, group_attack=spec.group_attack,
                     is_boss=spec.is_boss, color=spec.color)
