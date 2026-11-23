"""XP, niveaux du joueur, niveaux du jeu (difficulte) et boutique. Aucune dependance pygame."""
import random
from dataclasses import dataclass

from tp4.weapons import WEAPONS


# ----------------------------------------------------------------------
# Ameliorations (level up et boutique)
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Upgrade:
    key: str
    title: str
    description: str
    shop_cost: int


UPGRADES = {
    "hp": Upgrade("hp", "Max HP +20", "Plus de points de vie", 40),
    "speed": Upgrade("speed", "Speed +0.4", "Deplacement plus rapide", 40),
    "damage": Upgrade("damage", "Damage +10%", "Toutes les armes font plus mal", 60),
    "fire_rate": Upgrade("fire_rate", "Fire rate +8%", "Tir plus rapide", 60),
    "magnet": Upgrade("magnet", "Magnet +30", "Attire les pieces de plus loin", 30),
}


class PlayerStats:
    BASE_HP, BASE_SPEED = 100, 5.0
    HP_STEP, SPEED_STEP, DAMAGE_STEP, RATE_STEP, MAGNET_STEP = 20, 0.4, 0.10, 0.08, 30

    def __init__(self, data):
        self.data = data
        self.level = data.player_level
        self.xp = data.xp

    def count(self, key):
        return self.data.upgrades.get(key, 0)

    @property
    def max_hp(self):
        return self.BASE_HP + self.HP_STEP * self.count("hp")

    @property
    def speed(self):
        return min(9.0, self.BASE_SPEED + self.SPEED_STEP * self.count("speed"))

    @property
    def damage_mult(self):
        return 1 + self.DAMAGE_STEP * self.count("damage")

    @property
    def fire_rate_mult(self):
        return 1 + self.RATE_STEP * self.count("fire_rate")

    @property
    def magnet_range(self):
        return 50 + self.MAGNET_STEP * self.count("magnet")

    @property
    def xp_to_next(self):
        return int(40 * self.level ** 1.4)

    def gain_xp(self, amount):
        """Ajoute de l'XP, retourne le nombre de level up obtenus."""
        self.xp += amount
        ups = 0
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            ups += 1
        return ups

    def add_upgrade(self, key):
        self.data.upgrades[key] = self.count(key) + 1

    def reset_run(self):
        self.level, self.xp = 1, 0

    def export(self):
        self.data.player_level, self.data.xp = self.level, self.xp

    @staticmethod
    def random_choices(n=3):
        return random.sample(list(UPGRADES.values()), n)


# ----------------------------------------------------------------------
# Niveaux du jeu (illimites)
# ----------------------------------------------------------------------
@dataclass
class LevelConfig:
    number: int
    count: int
    hp_mult: float
    speed_mult: float
    roster: list
    boss: str = None
    spawn_interval: int = 60


class LevelManager:
    BOSS_EVERY = 5
    BOSSES = ["boss_golem", "boss_frost", "boss_toxic"]
    UNLOCK_LEVEL = {"normal": 1, "fast": 1, "flying": 2, "shooter": 2, "strong": 3,
                    "poison": 3, "ice": 4, "teleport": 6, "tank": 7}

    def is_boss_level(self, n):
        return n % self.BOSS_EVERY == 0

    def config(self, n):
        count = min(12, 3 + n // 2)
        boss = None
        if self.is_boss_level(n):
            boss = self.BOSSES[(n // self.BOSS_EVERY - 1) % len(self.BOSSES)]
            count = min(6, 2 + n // self.BOSS_EVERY)
        return LevelConfig(
            number=n,
            count=count,
            hp_mult=1 + 0.12 * (n - 1),
            speed_mult=min(2.0, 1 + 0.04 * (n - 1)),
            roster=[k for k, lvl in self.UNLOCK_LEVEL.items() if lvl <= n],
            boss=boss,
            spawn_interval=max(25, 70 - 2 * n),
        )

    def build_queue(self, cfg):
        queue = [cfg.boss] if cfg.boss else []
        queue += random.choices(cfg.roster, k=cfg.count)
        return queue


# ----------------------------------------------------------------------
# Boutique
# ----------------------------------------------------------------------
@dataclass
class ShopItem:
    label: str
    kind: str        # "stat" ou "weapon"
    key: str         # cle d'amelioration ou nom d'arme
    base_cost: int


class Shop:
    def __init__(self, data, stats):
        self.data, self.stats = data, stats
        self._items = [ShopItem(u.title, "stat", u.key, u.shop_cost) for u in UPGRADES.values()]
        self._items += [ShopItem(w.name + " (weapon)", "weapon", w.name, w.price)
                        for w in WEAPONS if w.price > 0]

    def items(self):
        return self._items

    def price(self, item):
        if item.kind == "stat":
            return int(item.base_cost * (1 + 0.5 * self.stats.count(item.key)))
        return item.base_cost

    def owned(self, item):
        return item.kind == "weapon" and item.key in self.data.unlocks

    def can_buy(self, item):
        return not self.owned(item) and self.data.coins >= self.price(item)

    def buy(self, item):
        """Retourne (succes, message)."""
        if self.owned(item):
            return False, "Already owned"
        price = self.price(item)
        if self.data.coins < price:
            return False, "Not enough coins"
        self.data.coins -= price
        if item.kind == "stat":
            self.stats.add_upgrade(item.key)
        else:
            self.data.unlocks.append(item.key)
        return True, "Purchased: " + item.label
