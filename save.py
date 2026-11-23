"""Sauvegarde du jeu (SRP: seule cette classe lit/ecrit le fichier JSON)."""
import json
import os
from dataclasses import dataclass, field, fields

from tp4.settings import SAVE_FILE


def _default_upgrades():
    return {"hp": 0, "speed": 0, "damage": 0, "fire_rate": 0, "magnet": 0}


@dataclass
class SaveData:
    # --- progression permanente ---
    high_score: int = 0
    coins: int = 0
    unlocks: list = field(default_factory=lambda: ["Bullet", "Fireball"])
    upgrades: dict = field(default_factory=_default_upgrades)
    # --- partie en cours (Continue) ---
    has_run: bool = False
    game_level: int = 1
    player_level: int = 1
    xp: int = 0
    score: int = 0
    # --- options ---
    master_volume: float = 0.7
    music_volume: float = 0.5
    sfx_volume: float = 0.8
    show_fps: bool = True


class SaveManager:
    def __init__(self, path=SAVE_FILE):
        self.path = path

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            names = {f.name for f in fields(SaveData)}
            data = SaveData(**{k: v for k, v in raw.items() if k in names})
        except (OSError, ValueError, TypeError, AttributeError):
            return SaveData()
        for key, value in _default_upgrades().items():
            data.upgrades.setdefault(key, value)
        for weapon in ("Bullet", "Fireball"):
            if weapon not in data.unlocks:
                data.unlocks.append(weapon)
        return data

    def save(self, data):
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data.__dict__, f, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            pass  # ne jamais faire planter le jeu pour une sauvegarde
