"""GameBoardTP5: GameBoardTP4 + Factory Method (monstres), Abstract Factory (mondes), Singleton (joueur)."""
import random

from tp4.board import GameBoardTP4
from tp5.monsters import CreatorEnemyFactory
from tp5.singleton import PlayerManager
from tp5.worlds import WorldRotation


class GameBoardTP5(GameBoardTP4):
    def __init__(self, data, stats, audio, resume=False):
        self.worlds = WorldRotation()           # avant super(): reset() en a besoin
        super().__init__(data, stats, audio, resume)
        self.factory = CreatorEnemyFactory()    # remplace EnemyFactory (meme interface)

    # ---- Singleton: un seul joueur ----
    def reset(self):
        PlayerManager().clear()
        super().reset()                         # le parent cree PlayerTP4
        self.player = PlayerManager().register(self.player)

    # ---- Abstract Factory: le monde du niveau ----
    def _begin_level(self):
        super()._begin_level()
        self.world = self.worlds.for_level(self.level)
        roster = self.world.monsters.roster(self.level)
        queue = [self.config.boss] if self.config.boss else []
        self.spawn_queue = queue + random.choices(roster, k=self.config.count)

    def _on_kill(self, e):
        before = len(self.pickups)
        super()._on_kill(e)
        rewards = self.world.rewards
        for pk in self.pickups[before:]:        # recompenses du monde
            if pk.kind == "coin":
                pk.value = max(1, int(pk.value * rewards.coin_mult))
            else:
                pk.kind = rewards.powerup_kind()
