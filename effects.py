"""Particules, explosions et effets de tir (SRP: aucun lien avec les regles du jeu)."""
import math
import random

import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "gravity")

    def __init__(self, x, y, vx, vy, life, color, size, gravity=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size, self.gravity = color, size, gravity


class ParticleSystem:
    def __init__(self, max_particles=700):
        self.max_particles = max_particles
        self.particles = []
        self.rings = []        # [x, y, radius, max_radius, color]

    def _add(self, p):
        if len(self.particles) < self.max_particles:
            self.particles.append(p)

    def emit_explosion(self, x, y, color, count=26, speed=4.5, size=4):
        for _ in range(count):
            a = random.uniform(0, math.tau)
            s = random.uniform(0.3, 1.0) * speed
            c = random.choice([color, (255, 220, 120), (255, 255, 255)])
            self._add(Particle(x, y, math.cos(a) * s, math.sin(a) * s,
                               random.randint(18, 40), c, random.uniform(size * 0.5, size), 0.05))

    def emit_sparks(self, x, y, color, count=6):
        self.emit_explosion(x, y, color, count=count, speed=2.5, size=3)

    def emit_muzzle(self, x, y, angle, color):
        for _ in range(6):
            a = angle + random.uniform(-0.4, 0.4)
            s = random.uniform(1.5, 4.0)
            self._add(Particle(x, y, math.cos(a) * s, math.sin(a) * s,
                               random.randint(6, 12), color, 3))

    def emit_trail(self, x, y, color):
        self._add(Particle(x, y, random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3),
                           random.randint(8, 14), color, 3))

    def add_ring(self, x, y, max_radius, color):
        self.rings.append([x, y, 4.0, float(max_radius), color])

    def update(self):
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += p.gravity
            p.life -= 1
        self.particles = [p for p in self.particles if p.life > 0]
        for r in self.rings:
            r[2] += (r[3] - r[2]) * 0.2 + 1
        self.rings = [r for r in self.rings if r[2] < r[3] - 1]

    def draw(self, surface):
        for r in self.rings:
            fade = max(0.0, 1 - r[2] / r[3])
            color = tuple(int(c * fade) for c in r[4])
            pygame.draw.circle(surface, color, (int(r[0]), int(r[1])), int(r[2]), 2)
        for p in self.particles:
            f = p.life / p.max_life
            color = tuple(int(c * f) for c in p.color)
            pygame.draw.circle(surface, color, (int(p.x), int(p.y)), max(1, int(p.size * f)))
