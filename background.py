"""Arriere-plan parallaxe: plusieurs couches qui defilent a des vitesses differentes."""
import math
import random

import pygame


class ParallaxBackground:
    def __init__(self, width, height, image=None):
        self.width, self.height = width, height
        self.layers = []                        # (surface, vitesse en px/image)
        self.base = self._gradient()
        if image is not None:
            self.layers.append((image, 0.3))
        else:
            self.layers.append((self._stars(), 0.15))
            self.layers.append((self._mountains(), 0.4))
        self.layers.append((self._grid(), 1.0))

    def _gradient(self):
        surf = pygame.Surface((self.width, self.height))
        for y in range(0, self.height, 4):
            k = y / self.height
            color = (int(18 + 20 * k), int(18 + 14 * k), int(34 + 30 * k))
            pygame.draw.rect(surf, color, (0, y, self.width, 4))
        return surf

    def _layer(self):
        return pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def _stars(self):
        surf = self._layer()
        rng = random.Random(7)
        for _ in range(90):
            pos = (rng.randint(0, self.width), rng.randint(0, self.height - 120))
            c = rng.randint(120, 255)
            pygame.draw.circle(surf, (c, c, c), pos, rng.choice([1, 1, 2]))
        return surf

    def _mountains(self):
        surf = self._layer()
        w, h = self.width, self.height
        points = [(0, h)]
        for x in range(0, w + 1, 10):             # periodique => sans coupure visible
            y = h - 110 + 35 * math.sin(math.tau * 2 * x / w) + 20 * math.sin(math.tau * 5 * x / w)
            points.append((x, int(y)))
        points.append((w, h))
        pygame.draw.polygon(surf, (30, 30, 58, 255), points)
        return surf

    def _grid(self):
        surf = self._layer()
        for x in range(0, self.width, 40):
            pygame.draw.line(surf, (255, 255, 255, 14), (x, 0), (x, self.height))
        for y in range(0, self.height, 40):
            pygame.draw.line(surf, (255, 255, 255, 14), (0, y), (self.width, y))
        return surf

    def draw(self, surface, t):
        surface.blit(self.base, (0, 0))
        for layer, speed in self.layers:
            off = int(t * speed) % self.width
            surface.blit(layer, (-off, 0))
            surface.blit(layer, (self.width - off, 0))
