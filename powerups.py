"""Power-ups qui tombent des monstres (OCP: une classe par bonus)."""
import random
from abc import ABC, abstractmethod


class PowerUp(ABC):
    kind = ""
    label = ""
    icon = "?"
    color = (255, 255, 255)
    duration = 0          # en images (60 = 1 seconde)

    @abstractmethod
    def apply(self, player):
        pass


class HealthPowerUp(PowerUp):
    kind, label, icon, color = "health", "Health", "+", (255, 70, 90)

    def apply(self, player):
        player.heal(35)


class TimedPowerUp(PowerUp):
    def apply(self, player):
        player.effects[self.kind] = self.duration


class ShieldPowerUp(TimedPowerUp):
    kind, label, icon, color, duration = "shield", "Shield", "S", (90, 170, 255), 60 * 6


class DoubleDamagePowerUp(TimedPowerUp):
    kind, label, icon, color, duration = "double_damage", "Double Damage", "D", (255, 150, 40), 60 * 10


class DoubleSpeedPowerUp(TimedPowerUp):
    kind, label, icon, color, duration = "double_speed", "Double Speed", ">", (80, 255, 120), 60 * 8


class RapidFirePowerUp(TimedPowerUp):
    kind, label, icon, color, duration = "rapid_fire", "Rapid Fire", "R", (255, 235, 70), 60 * 8


class MagnetPowerUp(TimedPowerUp):
    kind, label, icon, color, duration = "magnet", "Magnet", "M", (200, 120, 255), 60 * 10


POWERUPS = {p.kind: p for p in (
    HealthPowerUp(), ShieldPowerUp(), DoubleDamagePowerUp(),
    DoubleSpeedPowerUp(), RapidFirePowerUp(), MagnetPowerUp(),
)}


def random_powerup_kind():
    return random.choice(list(POWERUPS))
