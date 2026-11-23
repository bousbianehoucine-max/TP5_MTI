"""ABSTRACT FACTORY: chaque niveau a son monde (Space / Fantasy).

Une WorldFactory fabrique une FAMILLE de produits qui vont ensemble:
    - un fond (Background)
    - un ensemble de monstres (MonsterSet)
    - un ensemble de recompenses (RewardSet)
Le jeu ne connait que les classes abstraites: il ne sait jamais quel monde il utilise.
"""
import random
from abc import ABC, abstractmethod

from tp4.powerups import POWERUPS
from tp4.progression import LevelManager
from tp5.monsters import DEFAULT_CREATORS


# ----------------------------------------------------------------------
# Produits abstraits
# ----------------------------------------------------------------------
class MonsterSet(ABC):
    keys = ()                     # monstres du monde (cles de la fabrique d'ennemis)

    def unlock_level(self, key):
        for c in DEFAULT_CREATORS:
            if c.key == key:
                return c.unlock_level
        return LevelManager.UNLOCK_LEVEL.get(key, 1)

    def roster(self, level):
        """Monstres disponibles a ce niveau (jamais vide)."""
        keys = [k for k in self.keys if self.unlock_level(k) <= level]
        return keys or [self.keys[0]]


class RewardSet(ABC):
    coin_mult = 1.0
    favorite_powerups = ()

    def powerup_kind(self):
        """Power-up lache par un monstre: 60% un favori du monde, sinon au hasard."""
        if self.favorite_powerups and random.random() < 0.6:
            return random.choice(self.favorite_powerups)
        return random.choice(list(POWERUPS))


class Background(ABC):
    @abstractmethod
    def draw(self, surface, t):
        pass


# ----------------------------------------------------------------------
# Famille SPACE
# ----------------------------------------------------------------------
class SpaceMonsters(MonsterSet):
    keys = ("robot", "fast", "flying", "shooter", "teleport", "tank")


class SpaceRewards(RewardSet):
    coin_mult = 1.5
    favorite_powerups = ("rapid_fire", "double_speed", "magnet")


# ----------------------------------------------------------------------
# Famille FANTASY
# ----------------------------------------------------------------------
class FantasyMonsters(MonsterSet):
    keys = ("zombie", "normal", "dragon", "poison", "ice", "strong")


class FantasyRewards(RewardSet):
    coin_mult = 1.0
    favorite_powerups = ("health", "shield", "double_damage")


def _themed_background(width, height, image, top, bottom, mountain):
    # import tardif: ce module reste utilisable (et testable) sans pygame
    from tp4.background import ParallaxBackground

    class Themed(ParallaxBackground, Background):
        def _gradient(self):
            import pygame
            surf = pygame.Surface((self.width, self.height))
            for y in range(0, self.height, 4):
                k = y / self.height
                color = tuple(int(a + (b - a) * k) for a, b in zip(top, bottom))
                pygame.draw.rect(surf, color, (0, y, self.width, 4))
            return surf

        def _mountains(self):
            import math
            import pygame
            surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            w, h = self.width, self.height
            points = [(0, h)]
            for x in range(0, w + 1, 10):
                y = h - 110 + 35 * math.sin(math.tau * 2 * x / w) + 20 * math.sin(math.tau * 5 * x / w)
                points.append((x, int(y)))
            points.append((w, h))
            pygame.draw.polygon(surf, mountain, points)
            return surf

    return Themed(width, height, image)


# ----------------------------------------------------------------------
# Fabriques abstraite et concretes
# ----------------------------------------------------------------------
class WorldFactory(ABC):
    name = ""

    @abstractmethod
    def create_background(self, width, height, image=None):
        pass

    @abstractmethod
    def create_monsters(self):
        pass

    @abstractmethod
    def create_rewards(self):
        pass


class SpaceWorldFactory(WorldFactory):
    name = "Space"

    def create_background(self, width, height, image=None):
        return _themed_background(width, height, image, (6, 6, 24), (30, 10, 60), (40, 30, 80, 255))

    def create_monsters(self):
        return SpaceMonsters()

    def create_rewards(self):
        return SpaceRewards()


class FantasyWorldFactory(WorldFactory):
    name = "Fantasy"

    def create_background(self, width, height, image=None):
        return _themed_background(width, height, image, (20, 40, 30), (70, 30, 60), (25, 60, 40, 255))

    def create_monsters(self):
        return FantasyMonsters()

    def create_rewards(self):
        return FantasyRewards()


# ----------------------------------------------------------------------
# Client: un monde = les produits d'une fabrique
# ----------------------------------------------------------------------
class World:
    def __init__(self, factory):
        self.factory = factory
        self.name = factory.name
        self.monsters = factory.create_monsters()
        self.rewards = factory.create_rewards()

    def create_background(self, width, height, image=None):
        return self.factory.create_background(width, height, image)


class WorldRotation:
    """Un monde par niveau: Space, Fantasy, Space, ... (les niveaux de boss gardent le monde en cours)."""

    def __init__(self, factories=(SpaceWorldFactory(), FantasyWorldFactory())):
        self.worlds = [World(f) for f in factories]

    def for_level(self, level):
        return self.worlds[(level - 1) % len(self.worlds)]
