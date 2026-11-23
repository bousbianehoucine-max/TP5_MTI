"""Armes du joueur et projectiles ennemis.

Weapon (homework_monsters.py) reste la classe de base: on l'etend avec WeaponSpec.
OCP: une nouvelle arme = une nouvelle ligne dans WEAPONS (+ eventuellement un HitEffect).
"""
import math

from homework_monsters import Weapon


# ----------------------------------------------------------------------
# Effets a l'impact (Strategy)
# ----------------------------------------------------------------------
class HitEffect:
    def apply(self, board, enemy, shot):
        pass


class SlowEffect(HitEffect):
    def __init__(self, frames, factor):
        self.frames, self.factor = frames, factor

    def apply(self, board, enemy, shot):
        enemy.apply_slow(self.frames, self.factor)


class ExplosionEffect(HitEffect):
    """Degats de zone autour du point d'impact."""

    def __init__(self, radius, factor):
        self.radius, self.factor = radius, factor

    def apply(self, board, enemy, shot):
        board.explode(shot.x, shot.y, self.radius, shot.spec.color)
        for other in board.enemies:
            if other is enemy or not other.alive:
                continue
            if math.hypot(other.cx - shot.x, other.cy - shot.y) <= self.radius:
                board.damage_enemy(other, Weapon(shot.weapon.name,
                                                 int(shot.weapon.damage * self.factor),
                                                 shot.weapon.kind))


class ChainEffect(HitEffect):
    """Eclair: saute vers les ennemis proches."""

    def __init__(self, jumps, reach, factor):
        self.jumps, self.reach, self.factor = jumps, reach, factor

    def apply(self, board, enemy, shot):
        current, hit = enemy, {id(enemy)}
        for _ in range(self.jumps):
            nxt = board.nearest_enemy(current.cx, current.cy, exclude=hit, max_dist=self.reach)
            if nxt is None:
                break
            board.add_arc(current.cx, current.cy, nxt.cx, nxt.cy)
            board.damage_enemy(nxt, Weapon(shot.weapon.name,
                                           int(shot.weapon.damage * self.factor), shot.weapon.kind))
            hit.add(id(nxt))
            current = nxt


# ----------------------------------------------------------------------
# Description d'une arme
# ----------------------------------------------------------------------
class WeaponSpec(Weapon):
    def __init__(self, name, damage, kind, cooldown, speed, color, radius=5, pierce=0,
                 effect=None, sound="shoot", shape="circle", price=0):
        super().__init__(name, damage, kind)
        self.cooldown = cooldown        # images entre deux tirs
        self.speed = speed
        self.color = color
        self.radius = radius
        self.pierce = pierce            # nombre d'ennemis traverses en plus
        self.effect = effect or HitEffect()
        self.sound = sound
        self.shape = shape              # circle / line / rocket / bolt / plasma
        self.price = price

    def make_shot_weapon(self, damage_mult):
        """Weapon simple (donnees) avec les degats du joueur appliques."""
        return Weapon(self.name, max(1, int(self.damage * damage_mult)), self.kind)


WEAPONS = [
    WeaponSpec("Bullet", 40, "bullet", 18, 12, (255, 215, 0), 5, sound="shoot"),
    WeaponSpec("Fireball", 40, "fire", 24, 9, (255, 110, 0), 7, sound="shoot", shape="plasma"),
    WeaponSpec("Laser", 22, "laser", 8, 20, (0, 255, 255), 3, pierce=3, sound="laser",
               shape="line", price=100),
    WeaponSpec("Rocket", 55, "rocket", 50, 7, (255, 70, 50), 7, sound="rocket",
               effect=ExplosionEffect(75, 0.6), shape="rocket", price=150),
    WeaponSpec("Ice Gun", 25, "ice", 20, 10, (150, 220, 255), 6, sound="ice",
               effect=SlowEffect(150, 0.45), price=120),
    WeaponSpec("Lightning", 30, "lightning", 32, 16, (255, 255, 160), 4, sound="lightning",
               effect=ChainEffect(2, 150, 0.7), shape="bolt", price=200),
    WeaponSpec("Plasma", 70, "plasma", 40, 8, (230, 60, 255), 11, pierce=1, sound="plasma",
               shape="plasma", price=250),
]

# Projectiles des ennemis (meme classe de base, jamais achetes)
ENEMY_SHOTS = {
    "spit": WeaponSpec("Spit", 10, "enemy", 0, 6, (0, 255, 255), 5),
    "frost": WeaponSpec("Frost", 8, "frost", 0, 5, (150, 230, 255), 6),
    "venom": WeaponSpec("Venom", 6, "poison", 0, 5, (140, 255, 60), 6),
    "boss": WeaponSpec("Orb", 14, "enemy", 0, 5, (255, 80, 80), 8),
}


def get_weapon(name):
    for w in WEAPONS:
        if w.name == name:
            return w
    return WEAPONS[0]
