"""SINGLETON: une seule instance du joueur principal dans la partie.

Version "repensee" (devoir W5): le Singleton ne verrouille pas le nombre a 1 pour toujours,
le nombre maximum de joueurs est configurable (1 = mode solo, 2 = mode duo, ...).
"""


class SingletonMeta(type):
    """Metaclasse: toute classe qui l'utilise n'a qu'UNE instance."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in SingletonMeta._instances:
            SingletonMeta._instances[cls] = super().__call__(*args, **kwargs)
        return SingletonMeta._instances[cls]


class PlayerManager(metaclass=SingletonMeta):
    """Seul point d'acces aux joueurs. Il refuse un joueur de plus que le maximum."""

    def __init__(self, max_players=1):
        self.max_players = max_players
        self.players = []

    def set_max_players(self, n):
        self.max_players = max(1, n)

    def clear(self):
        """Nouvelle partie: on oublie les anciens joueurs."""
        self.players.clear()

    def register(self, player):
        """Enregistre le joueur. Si la limite est atteinte, renvoie le joueur principal
        (jamais un doublon)."""
        if len(self.players) < self.max_players:
            self.players.append(player)
            return player
        return self.players[0]

    @property
    def main(self):
        return self.players[0] if self.players else None
