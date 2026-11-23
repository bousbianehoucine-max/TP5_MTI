"""GameRendererTP5: dessine le fond du monde courant (fourni par la WorldFactory)."""
from tp4.render import GameRendererTP4
from tp4.settings import HEIGHT, WIDTH


class GameRendererTP5(GameRendererTP4):
    def __init__(self, assets):
        super().__init__(assets)
        self._assets = assets
        self._backgrounds = {}

    def draw(self, surface, board, animate=True):
        world = board.world
        if world.name not in self._backgrounds:
            self._backgrounds[world.name] = world.create_background(WIDTH, HEIGHT, self._assets.background)
        self.background = self._backgrounds[world.name]
        super().draw(surface, board, animate)
        label = self.font_tiny.render("World: " + world.name, True, (220, 220, 220))
        surface.blit(label, (WIDTH - label.get_width() - 8, HEIGHT - 20))
