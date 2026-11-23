"""Devoir TP3 - Objet Monster conforme aux 5 principes SOLID.

SRP  : la vie (Health) et l'affichage (HealthBarRenderer) sont separes du Monster.
OCP  : nouveau type de monstre = nouvelle sous-classe, Monster ne change pas.
LSP  : tout monstre peut etre utilise la ou un Monster est attendu (update, take_hit).
ISP  : capacites en petites interfaces (Movable, Shooter): chaque monstre
       n'implemente que ce dont il a besoin.
DIP  : le calcul des degats est une abstraction (DamageCalculator),
       le Monster ne depend d'aucune arme precise.
"""

import math
from abc import ABC, abstractmethod


# ======================================================================
# Armes (simples donnees)
# ======================================================================
class Weapon:
    def __init__(self, name, damage, kind="bullet"):
        self.name = name
        self.damage = damage
        self.kind = kind          # "bullet", "fire", "ice", ...


# ======================================================================
# DIP: abstraction du calcul de degats
# ======================================================================
class DamageCalculator(ABC):
    @abstractmethod
    def calculate(self, weapon) -> int:
        pass


class NormalDamage(DamageCalculator):
    def calculate(self, weapon):
        return weapon.damage


class ResistantDamage(DamageCalculator):
    """Resistant a un type d'arme: degats reduits."""

    def __init__(self, resistant_kind, factor=0.5):
        self.resistant_kind = resistant_kind
        self.factor = factor

    def calculate(self, weapon):
        if weapon.kind == self.resistant_kind:
            return int(weapon.damage * self.factor)
        return weapon.damage


class VulnerableDamage(DamageCalculator):
    """Faible contre un type d'arme: degats supplementaires."""

    def __init__(self, weak_kind, factor=2.0):
        self.weak_kind = weak_kind
        self.factor = factor

    def calculate(self, weapon):
        if weapon.kind == self.weak_kind:
            return int(weapon.damage * self.factor)
        return weapon.damage


class ShieldDamage(DamageCalculator):
    """Bouclier: retire une valeur fixe a chaque coup."""

    def __init__(self, shield):
        self.shield = shield

    def calculate(self, weapon):
        return max(0, weapon.damage - self.shield)


# ======================================================================
# SRP: composant "vie" (separe du monstre)
# ======================================================================
class Health:
    def __init__(self, max_hp=100):
        self.max_hp = max_hp
        self.hp = max_hp

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    @property
    def is_dead(self):
        return self.hp <= 0

    @property
    def ratio(self):
        return self.hp / self.max_hp


# ======================================================================
# SRP: affichage de la barre de vie (separe du monstre)
# ======================================================================
class HealthBarRenderer:
    """Dessine la barre de vie d'un monstre sur une surface pygame."""

    def __init__(self, width=50, height=6):
        self.width = width
        self.height = height

    def draw(self, surface, monster):
        import pygame

        x, y = int(monster.x), int(monster.y) - 12
        pygame.draw.rect(surface, (100, 100, 100), (x, y, self.width, self.height))
        pygame.draw.rect(surface, (0, 255, 0),
                         (x, y, self.width * monster.health.ratio, self.height))


class ConsoleHealthBar:
    """Meme role, pour tester sans fenetre."""

    def render(self, monster, length=20):
        filled = round(length * monster.health.ratio)
        bar = "#" * filled + "-" * (length - filled)
        return f"{monster.name:<16} [{bar}] {monster.health.hp}/{monster.health.max_hp}"


# ======================================================================
# ISP: petites interfaces de capacites
# ======================================================================
class Movable(ABC):
    @abstractmethod
    def move_towards(self, target_x, target_y):
        pass


class Shooter(ABC):
    @abstractmethod
    def shoot(self, target_x, target_y):
        pass


# ======================================================================
# Monster (classe de base)
# ======================================================================
class Monster(ABC):
    SIZE = 50

    def __init__(self, name, x, y, max_hp=100, damage_calculator=None):
        self.name = name
        self.x = x
        self.y = y
        self.health = Health(max_hp)
        # DIP: depend de l'abstraction, valeur par defaut = degats normaux
        self._damage_calculator = damage_calculator or NormalDamage()

    def take_hit(self, weapon):
        damage = self._damage_calculator.calculate(weapon)
        self.health.take_damage(damage)
        return damage

    @property
    def alive(self):
        return not self.health.is_dead

    @abstractmethod
    def update(self, target_x, target_y):
        """Contrat commun (LSP): appele a chaque image pour chaque monstre."""


# ======================================================================
# Types de monstres (OCP + LSP)
# ======================================================================
class ImmobileMonster(Monster):
    """Monstre qui ne bouge pas: update ne fait rien, le contrat est respecte."""

    def update(self, target_x, target_y):
        pass


class WalkingMonster(Monster, Movable):
    def __init__(self, name, x, y, speed=2.0, **kwargs):
        super().__init__(name, x, y, **kwargs)
        self.speed = speed

    def move_towards(self, target_x, target_y):
        dx, dy = target_x - self.x, target_y - self.y
        distance = math.hypot(dx, dy)
        if distance > 1:
            self.x += dx / distance * self.speed
            self.y += dy / distance * self.speed

    def update(self, target_x, target_y):
        self.move_towards(target_x, target_y)


class NormalMonster(WalkingMonster):
    def __init__(self, x, y):
        super().__init__("Normal Monster", x, y, speed=2.0, max_hp=100)


class FastMonster(WalkingMonster):
    def __init__(self, x, y):
        super().__init__("Fast Monster", x, y, speed=4.0, max_hp=60)


class FlyingMonster(WalkingMonster):
    flies = True

    def __init__(self, x, y):
        super().__init__("Flying Monster", x, y, speed=3.0, max_hp=80,
                         damage_calculator=VulnerableDamage("fire", 1.5))


class StrongMonster(WalkingMonster):
    def __init__(self, x, y):
        super().__init__("Strong Monster", x, y, speed=1.0, max_hp=300,
                         damage_calculator=ShieldDamage(10))


class FireResistantMonster(WalkingMonster):
    def __init__(self, x, y):
        super().__init__("Fire Resistant", x, y, speed=2.0, max_hp=120,
                         damage_calculator=ResistantDamage("fire", 0.25))


class ShooterMonster(WalkingMonster, Shooter):
    """Marche ET tire: implemente Movable et Shooter, rien d'autre."""

    def __init__(self, x, y):
        super().__init__("Shooter Monster", x, y, speed=1.5, max_hp=90)

    def shoot(self, target_x, target_y):
        dx, dy = target_x - self.x, target_y - self.y
        distance = math.hypot(dx, dy) or 1
        return {"x": self.x, "y": self.y, "vx": dx / distance * 6, "vy": dy / distance * 6}


# ======================================================================
# main call
# ======================================================================
if __name__ == "__main__":
    player_x, player_y = 100, 100
    bar = ConsoleHealthBar()

    monsters = [
        NormalMonster(700, 100),
        FastMonster(700, 200),
        FlyingMonster(700, 300),
        StrongMonster(700, 400),
        FireResistantMonster(700, 500),
        ShooterMonster(700, 50),
        ImmobileMonster("Totem", 400, 400, max_hp=150),
    ]

    # LSP: la meme boucle fonctionne pour TOUS les monstres
    print("=== 3 images de deplacement ===")
    for _ in range(3):
        for m in monsters:
            m.update(player_x, player_y)
    for m in monsters:
        print(f"{m.name:<16} position = ({m.x:.1f}, {m.y:.1f})")

    # DIP: meme arme, degats differents selon le calculateur du monstre
    print("\n=== Tir de balle (damage=40) ===")
    bullet = Weapon("Bullet", 40, "bullet")
    for m in monsters:
        dealt = m.take_hit(bullet)
        print(f"{m.name:<16} recoit {dealt:>2} degats")

    print("\n=== Tir de feu (damage=40) ===")
    fire = Weapon("Fireball", 40, "fire")
    for m in monsters:
        dealt = m.take_hit(fire)
        print(f"{m.name:<16} recoit {dealt:>2} degats")

    # SRP: l'affichage de la vie est fait par un autre objet
    print("\n=== Barres de vie ===")
    for m in monsters:
        print(bar.render(m))

    # ISP: seul ShooterMonster sait tirer
    print("\n=== Capacites ===")
    for m in monsters:
        print(f"{m.name:<16} Movable={isinstance(m, Movable)}  Shooter={isinstance(m, Shooter)}")
    shooter = monsters[5]
    print("Projectile du tireur:", {k: round(v, 1) for k, v in shooter.shoot(player_x, player_y).items()})

