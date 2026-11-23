"""FACTORY METHOD: des monstres differents "a la demande" (Zombie, Dragon, Robot).

MonsterCreator.create() est la methode "template": elle appelle la methode fabrique
create_monster() que chaque sous-classe redefinit pour choisir le type concret.
Ajouter un monstre = ajouter une classe Monster + un Creator (OCP), rien d'autre ne change.
"""
from abc import ABC, abstractmethod

from homework_monsters import Health, ResistantDamage, VulnerableDamage, WalkingMonster
from tp4.enemies import (ChaseBehavior, CompositeDamage, Enemy, EnemyFactory, EvadeBehavior,
                         KeepDistanceBehavior, LowHealthFlee, ProjectileAttack)
from tp4.weapons import ENEMY_SHOTS, WeaponSpec

# nouveaux projectiles ennemis (meme dictionnaire que le TP4)
ENEMY_SHOTS.setdefault("dragonfire", WeaponSpec("Dragon Fire", 12, "enemy", 0, 6, (255, 120, 0), 7))
ENEMY_SHOTS.setdefault("laserbolt", WeaponSpec("Laser Bolt", 9, "enemy", 0, 7, (255, 60, 60), 4))


# ----------------------------------------------------------------------
# Produits: les nouveaux monstres
# ----------------------------------------------------------------------
class ZombieMonster(WalkingMonster):
    def __init__(self, x, y):
        super().__init__("Zombie", x, y, speed=1.2, max_hp=140,
                         damage_calculator=VulnerableDamage("fire", 1.5))


class DragonMonster(WalkingMonster):
    SIZE = 64
    flies = True

    def __init__(self, x, y):
        super().__init__("Dragon", x, y, speed=1.4, max_hp=220,
                         damage_calculator=CompositeDamage(ResistantDamage("fire", 0.2),
                                                           VulnerableDamage("ice", 1.5)))


class RobotMonster(WalkingMonster):
    def __init__(self, x, y):
        super().__init__("Robot", x, y, speed=1.8, max_hp=150,
                         damage_calculator=VulnerableDamage("lightning", 1.6))


# ----------------------------------------------------------------------
# Createurs (Factory Method)
# ----------------------------------------------------------------------
class MonsterCreator(ABC):
    key = ""
    monster_cls = None
    unlock_level = 1
    xp, coins, contact_damage = 15, 6, 8
    color = (220, 20, 60)

    @abstractmethod
    def create_monster(self, x, y):
        """LA methode fabrique: retourne le monstre concret."""

    @abstractmethod
    def create_behavior(self):
        """Comportement de deplacement (Strategy du TP4)."""

    def create_attack(self):
        return None

    def create(self, x, y, hp_mult=1.0, speed_mult=1.0):
        monster = self.create_monster(x, y)
        monster.health = Health(int(monster.health.max_hp * hp_mult))
        monster.speed *= speed_mult
        reward = 1 + (hp_mult - 1) * 0.5
        return Enemy(self.key, monster, self.create_behavior(), self.create_attack(),
                     xp=int(self.xp * reward), coins=int(self.coins * reward),
                     contact_damage=self.contact_damage, color=self.color)


class ZombieCreator(MonsterCreator):
    key, monster_cls, unlock_level = "zombie", ZombieMonster, 1
    xp, coins, color = 14, 5, (110, 150, 90)

    def create_monster(self, x, y):
        return ZombieMonster(x, y)

    def create_behavior(self):
        return ChaseBehavior()


class DragonCreator(MonsterCreator):
    key, monster_cls, unlock_level = "dragon", DragonMonster, 3
    xp, coins, contact_damage, color = 40, 16, 14, (220, 70, 30)

    def create_monster(self, x, y):
        return DragonMonster(x, y)

    def create_behavior(self):
        return LowHealthFlee(KeepDistanceBehavior(240))

    def create_attack(self):
        return ProjectileAttack("dragonfire", 100, count=3, spread=0.25)


class RobotCreator(MonsterCreator):
    key, monster_cls, unlock_level = "robot", RobotMonster, 1
    xp, coins, color = 20, 8, (150, 160, 175)

    def create_monster(self, x, y):
        return RobotMonster(x, y)

    def create_behavior(self):
        return EvadeBehavior(0.9)

    def create_attack(self):
        return ProjectileAttack("laserbolt", 110)


DEFAULT_CREATORS = (ZombieCreator(), DragonCreator(), RobotCreator())


class CreatorEnemyFactory(EnemyFactory):
    """Meme interface que EnemyFactory (TP4): le jeu ne change pas.
    Les cles inconnues sont deleguees a la fabrique du TP4."""

    def __init__(self, creators=DEFAULT_CREATORS):
        super().__init__()
        self.creators = {c.key: c for c in creators}

    def register(self, creator):
        self.creators[creator.key] = creator

    def monster_class(self, key):
        c = self.creators.get(key)
        return c.monster_cls if c else super().monster_class(key)

    def create(self, key, x, y, hp_mult=1.0, speed_mult=1.0):
        c = self.creators.get(key)
        if c:
            return c.create(x, y, hp_mult, speed_mult)
        return super().create(key, x, y, hp_mult, speed_mult)
