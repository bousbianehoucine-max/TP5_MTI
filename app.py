"""AppTP5: meme application que le TP4, avec le plateau et le rendu du TP5."""
import pygame

from tp4.app import App
from tp4.progression import PlayerStats
from tp4.screens import GameScreen
from tp5.board import GameBoardTP5
from tp5.render import GameRendererTP5


class AppTP5(App):
    def __init__(self):
        super().__init__()
        pygame.display.set_caption("2D Shooting Game - TP5 (Design Patterns)")
        self.renderer = GameRendererTP5(self.assets)

    def start_new_game(self):
        stats = PlayerStats(self.data)
        stats.reset_run()
        self.reset_stack(GameScreen(self, GameBoardTP5(self.data, stats, self.audio)))

    def continue_game(self):
        if self.data.has_run:
            stats = PlayerStats(self.data)
            self.reset_stack(GameScreen(self, GameBoardTP5(self.data, stats, self.audio, resume=True)))
