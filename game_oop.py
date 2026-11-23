"""Jeu de tir 2D en POO (TP3 - devoir): utilise les monstres de homework_monsters.py.

Fichiers a mettre dans le MEME dossier:  homework_monsters.py  +  game_oop.py
Lancer:  py game_oop.py

Controles: fleches = deplacer | ESPACE = balle | F = boule de feu | R = rejouer | ECHAP = quitter
But: eliminer 5 monstres (Normal, Fast, Flying, Strong, Shooter) sans mourir.

Architecture (SRP): chaque classe a UNE responsabilite.
  Player        -> l'etat et le deplacement du joueur
  Bullet        -> une balle (joueur ou monstre)
  GameBoard     -> les regles du jeu (collisions, score, etats)
  GameRenderer  -> TOUT le dessin (aucune autre classe ne dessine)
  AssetManager  -> (TP4) charge les images: fond, heros, monstres (dossier assets/)

TP4: on change l'apparence SANS toucher a la logique: pour changer une image,
il suffit de remplacer le fichier dans assets/ (aucune modification du code).
Si une image manque, le jeu utilise un rectangle de couleur (fallback).
"""

import math
import os
import random
import sys

import pygame

from homework_monsters import (
    FastMonster, FlyingMonster, Health, HealthBarRenderer, NormalMonster,
    Shooter, ShooterMonster, StrongMonster, Weapon,
)

WIDTH, HEIGHT, FPS = 800, 600, 60

# Armes du joueur: meme balle, kinds differents -> degats differents selon le monstre (DIP)
BULLET_WEAPON = Weapon("Bullet", 40, "bullet")
FIRE_WEAPON = Weapon("Fireball", 40, "fire")
SPIT_WEAPON = Weapon("Spit", 10, "enemy")      # projectile du monstre tireur

WAVE = [NormalMonster, FastMonster, FlyingMonster, StrongMonster, ShooterMonster]


def center_of(obj, size):
    return obj.x + size / 2, obj.y + size / 2


# ======================================================================
# Player
# ======================================================================
class Player:
    SIZE = 40

    def __init__(self):
        self.x, self.y = 150, 275
        self.speed = 5
        self.health = Health(100)

    def handle_input(self, keys):
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
        if keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.y += self.speed
        self.x = max(0, min(WIDTH - self.SIZE, self.x))
        self.y = max(0, min(HEIGHT - self.SIZE, self.y))

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.SIZE, self.SIZE)


# ======================================================================
# Bullet
# ======================================================================
class Bullet:
    RADIUS = 5

    def __init__(self, x, y, vx, vy, weapon, from_player=True):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.weapon = weapon
        self.from_player = from_player

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def off_screen(self):
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT


# ======================================================================
# GameBoard (regles du jeu, sans aucun dessin)
# ======================================================================
class GameBoard:
    WIN_SCORE = 5
    SHOOT_EVERY = 90          # images entre deux tirs du monstre tireur

    def __init__(self):
        self.reset()

    def reset(self):
        self.player = Player()
        self.bullets = []
        self.score = 0
        self.state = "PLAYING"            # PLAYING / GAME_OVER / WIN
        self._shoot_timer = 0
        self._spawn_monster()

    def _spawn_monster(self):
        monster_class = WAVE[self.score % len(WAVE)]
        self.monster = monster_class(WIDTH - 60, random.randint(50, HEIGHT - 100))
        self._shoot_timer = 0

    # ---- actions du joueur ----
    def fire(self, weapon):
        """Tir avec visee automatique vers le monstre."""
        if self.state != "PLAYING":
            return
        px, py = center_of(self.player, Player.SIZE)
        mx, my = center_of(self.monster, self.monster.SIZE)
        dx, dy = mx - px, my - py
        distance = math.hypot(dx, dy)
        if distance > 0:
            self.bullets.append(Bullet(px, py, dx / distance * 10, dy / distance * 10, weapon))

    # ---- mise a jour d'une image ----
    def update(self):
        if self.state != "PLAYING":
            return

        # Le monstre agit (LSP: n'importe quel Monster respecte update())
        self.monster.update(self.player.x, self.player.y)

        # ISP: seuls les monstres qui sont des Shooter tirent
        if isinstance(self.monster, Shooter):
            self._shoot_timer += 1
            if self._shoot_timer >= self.SHOOT_EVERY:
                self._shoot_timer = 0
                shot = self.monster.shoot(self.player.x, self.player.y)
                self.bullets.append(Bullet(shot["x"] + 25, shot["y"] + 25,
                                           shot["vx"], shot["vy"], SPIT_WEAPON, from_player=False))

        # Contact monstre / joueur
        monster_rect = pygame.Rect(int(self.monster.x), int(self.monster.y),
                                   self.monster.SIZE, self.monster.SIZE)
        if self.player.rect.colliderect(monster_rect):
            self.player.health.take_damage(1)

        # Balles
        for bullet in list(self.bullets):
            bullet.update()
            point = (int(bullet.x), int(bullet.y))
            if bullet.off_screen():
                self.bullets.remove(bullet)
            elif bullet.from_player and monster_rect.collidepoint(point):
                self.bullets.remove(bullet)
                self.monster.take_hit(bullet.weapon)       # DIP: calcul des degats delegue
                if not self.monster.alive:
                    self.score += 1
                    if self.score < self.WIN_SCORE:
                        self._spawn_monster()
                    break
            elif not bullet.from_player and self.player.rect.collidepoint(point):
                self.bullets.remove(bullet)
                self.player.health.take_damage(bullet.weapon.damage)

        # Fin de partie
        if self.player.health.is_dead:
            self.state = "GAME_OVER"
        elif self.score >= self.WIN_SCORE:
            self.state = "WIN"


# ======================================================================
# AssetManager (TP4): chargement des images, separe de la logique
# ======================================================================
class AssetManager:
    ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

    def __init__(self):
        self.background = self._load("background.png", (WIDTH, HEIGHT))
        self.player = self._load("hero.png", (Player.SIZE + 20, Player.SIZE + 40))
        self.monsters = {
            NormalMonster: self._load("monster_normal.png", (NormalMonster.SIZE + 20,) * 2),
            FastMonster: self._load("monster_fast.png", (FastMonster.SIZE,) * 2),
            FlyingMonster: self._load("monster_flying.png", (FlyingMonster.SIZE + 10,) * 2),
            StrongMonster: self._load("monster_strong.png", (StrongMonster.SIZE + 40,) * 2),
            ShooterMonster: self._load("monster_shooter.png", (ShooterMonster.SIZE + 10,) * 2),
        }

    def _load(self, filename, size):
        """Retourne l'image redimensionnee, ou None si le fichier est absent."""
        path = os.path.join(self.ASSET_DIR, filename)
        try:
            image = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(image, size)
        except (pygame.error, FileNotFoundError):
            return None


# ======================================================================
# GameRenderer (tout l'affichage)
# ======================================================================
class GameRenderer:
    BG = (30, 30, 40)
    GRID = (45, 45, 60)
    TEXT = (255, 255, 255)
    MONSTER_COLORS = {
        NormalMonster: (220, 20, 60),
        FastMonster: (255, 140, 0),
        FlyingMonster: (160, 100, 255),
        StrongMonster: (130, 0, 0),
        ShooterMonster: (0, 170, 170),
    }
    BULLET_COLORS = {"bullet": (255, 215, 0), "fire": (255, 90, 0), "enemy": (0, 255, 255)}

    def __init__(self, assets):
        self.assets = assets
        self.font_small = pygame.font.SysFont("arial", 20)
        self.font_large = pygame.font.SysFont("arial", 40)
        self.bars = HealthBarRenderer()
        self.player_bar = HealthBarRenderer(width=Player.SIZE)

    def draw(self, surface, board):
        self._background(surface)
        if board.state == "PLAYING":
            self._playing(surface, board)
        elif board.state == "GAME_OVER":
            self._message(surface, "GAME OVER - MONSTER GOT YOU!", (255, 50, 50))
        else:
            self._message(surface, "YOU WIN! SURVIVED!", (50, 255, 50))

    def _background(self, surface):
        if self.assets.background:
            surface.blit(self.assets.background, (0, 0))
            return
        surface.fill(self.BG)                      # fallback: fond uni + grille
        for x in range(0, WIDTH, 40):
            pygame.draw.line(surface, self.GRID, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(surface, self.GRID, (0, y), (WIDTH, y))

    def _draw_sprite(self, surface, sprite, rect, fallback_color):
        """Dessine l'image centree sur rect, sinon un rectangle de couleur."""
        if sprite:
            surface.blit(sprite, sprite.get_rect(center=rect.center))
        else:
            pygame.draw.rect(surface, fallback_color, rect, border_radius=8)

    def _playing(self, surface, board):
        for b in board.bullets:
            color = self.BULLET_COLORS.get(b.weapon.kind, (255, 255, 255))
            pygame.draw.circle(surface, color, (int(b.x), int(b.y)), Bullet.RADIUS)

        # joueur
        self._draw_sprite(surface, self.assets.player, board.player.rect, (50, 205, 50))
        self.player_bar.draw(surface, board.player)

        # monstre
        m = board.monster
        color = self.MONSTER_COLORS.get(type(m), (220, 20, 60))
        m_rect = pygame.Rect(int(m.x), int(m.y), m.SIZE, m.SIZE)
        self._draw_sprite(surface, self.assets.monsters.get(type(m)), m_rect, color)
        self.bars.draw(surface, m)
        label = self.font_small.render(m.name, True, self.TEXT)
        label_x = max(5, min(int(m.x) - 10, WIDTH - label.get_width() - 5))   # reste dans l'ecran
        surface.blit(label, (label_x, int(m.y) - 34))

        surface.blit(self.font_small.render(f"Score: {board.score} / {board.WIN_SCORE}", True, self.TEXT), (20, 20))
        surface.blit(self.font_small.render("Espace: balle   F: feu   Fleches: bouger", True, self.TEXT),
                     (20, HEIGHT - 30))

    def _message(self, surface, text, color):
        big = self.font_large.render(text, True, color)
        small = self.font_small.render("Press 'R' to Restart or 'ESC' to Quit", True, self.TEXT)
        surface.blit(big, (WIDTH // 2 - big.get_width() // 2, HEIGHT // 2 - 50))
        surface.blit(small, (WIDTH // 2 - small.get_width() // 2, HEIGHT // 2 + 10))


# ======================================================================
# Programme principal
# ======================================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Shooting Game - TP4")
    clock = pygame.time.Clock()

    board = GameBoard()
    renderer = GameRenderer(AssetManager())
    running = True

    while running:
        # 1. evenements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif board.state == "PLAYING":
                    if event.key == pygame.K_SPACE:
                        board.fire(BULLET_WEAPON)
                    elif event.key == pygame.K_f:
                        board.fire(FIRE_WEAPON)
                elif event.key == pygame.K_r:
                    board.reset()

        # 2. entrees continues + 3. mise a jour
        if board.state == "PLAYING":
            board.player.handle_input(pygame.key.get_pressed())
        board.update()

        # 4. dessin
        renderer.draw(screen, board)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

