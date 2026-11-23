"""Entites du TP4: on ETEND Player et Bullet du TP3 sans les modifier."""
import math
import random

import pygame

from game_oop import Bullet, Player
from homework_monsters import Health
from tp4.settings import HEIGHT, WIDTH


class PlayerTP4(Player):
    def __init__(self, stats):
        super().__init__()
        self.stats = stats
        self.health = Health(stats.max_hp)
        self.effects = {}                 # nom du power-up -> images restantes
        self.slow_timer = self.poison_timer = self.iframes = self.cooldown = 0
        self.moving = False
        self.facing_right = True

    # ---- stats ----
    def refresh_stats(self):
        """Appele apres une amelioration (level up, boutique)."""
        old = self.health.max_hp
        self.health.max_hp = self.stats.max_hp
        self.health.hp = min(self.health.max_hp, self.health.hp + max(0, self.health.max_hp - old))

    @property
    def center(self):
        return self.x + self.SIZE / 2, self.y + self.SIZE / 2

    @property
    def damage_mult(self):
        return self.stats.damage_mult * (2 if "double_damage" in self.effects else 1)

    @property
    def shielded(self):
        return "shield" in self.effects

    def heal(self, amount):
        self.health.hp = min(self.health.max_hp, self.health.hp + amount)

    # ---- actions ----
    def handle_input(self, keys):
        dx = int(bool(keys[pygame.K_RIGHT] or keys[pygame.K_d])) - int(bool(keys[pygame.K_LEFT] or keys[pygame.K_a]))
        dy = int(bool(keys[pygame.K_DOWN] or keys[pygame.K_s])) - int(bool(keys[pygame.K_UP] or keys[pygame.K_w]))
        speed = self.stats.speed
        if "double_speed" in self.effects:
            speed *= 1.5
        if self.slow_timer > 0:
            speed *= 0.5
        if dx and dy:
            speed *= 0.7071
        self.x = max(0, min(WIDTH - self.SIZE, self.x + dx * speed))
        self.y = max(0, min(HEIGHT - self.SIZE, self.y + dy * speed))
        self.moving = bool(dx or dy)
        if dx:
            self.facing_right = dx > 0

    def hurt(self, amount, iframes=30):
        """Retourne True si le joueur a vraiment ete touche."""
        if self.iframes > 0 or self.shielded:
            return False
        self.health.take_damage(amount)
        self.iframes = iframes
        return True

    def tick(self):
        self.cooldown = max(0, self.cooldown - 1)
        self.iframes = max(0, self.iframes - 1)
        self.slow_timer = max(0, self.slow_timer - 1)
        self.poison_timer = max(0, self.poison_timer - 1)
        for name in list(self.effects):
            self.effects[name] -= 1
            if self.effects[name] <= 0:
                del self.effects[name]


class Projectile(Bullet):
    """Bullet du TP3 + description de l'arme (couleur, perforation, effet)."""

    def __init__(self, x, y, vx, vy, weapon, spec, from_player=True):
        super().__init__(x, y, vx, vy, weapon, from_player)
        self.spec = spec
        self.radius = spec.radius
        self.pierce_left = spec.pierce
        self.hit_ids = set()
        self.age = 0

    def off_screen(self):
        return self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20


class Pickup:
    """Piece ou power-up au sol."""

    def __init__(self, kind, x, y, value=0):
        self.kind, self.x, self.y, self.value = kind, x, y, value
        self.ttl = 900
        self.age = random.randint(0, 60)

    def update(self, px, py, magnet_range):
        """Retourne la distance au joueur (apres attraction)."""
        self.age += 1
        self.ttl -= 1
        d = math.hypot(px - self.x, py - self.y)
        if 1 < d < magnet_range:
            self.x += (px - self.x) / d * 7
            self.y += (py - self.y) / d * 7
        return d

    @property
    def expired(self):
        return self.ttl <= 0
