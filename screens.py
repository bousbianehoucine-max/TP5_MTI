"""Ecrans du jeu (pattern State): menu, options, credits, jeu, pause, level up, boutique, game over."""
from dataclasses import dataclass
from typing import Callable

import pygame

from tp4.progression import PlayerStats, Shop
from tp4.settings import HEIGHT, WIDTH

GOLD, WHITE, GRAY = (255, 215, 0), (255, 255, 255), (120, 120, 135)


def draw_text(surface, text, font, color, pos, align="center"):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if align == "center":
        rect.center = pos
    elif align == "left":
        rect.midleft = pos
    else:
        rect.midright = pos
    surface.blit(img, rect)


def dim(surface, alpha=150):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surface.blit(overlay, (0, 0))


def is_enter(event):
    return event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Screen:
    transparent = False        # True: l'ecran du dessous reste visible (pause, boutique...)

    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass

    def on_exit(self):
        pass


# ======================================================================
# Menus generiques
# ======================================================================
@dataclass
class MenuItem:
    label: str
    action: Callable
    enabled: Callable = lambda: True


class MenuScreen(Screen):
    title = ""
    title_color = GOLD

    def __init__(self, app):
        super().__init__(app)
        self.items = self.build_items()
        self.index = 0

    def build_items(self):
        return []

    def on_escape(self):
        pass

    def _move(self, step):
        for _ in range(len(self.items)):
            self.index = (self.index + step) % len(self.items)
            if self.items[self.index].enabled():
                break
        self.app.audio.play("click")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self._move(-1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._move(1)
        elif event.key == pygame.K_ESCAPE:
            self.on_escape()
        elif is_enter(event):
            item = self.items[self.index]
            if item.enabled():
                self.app.audio.play("click")
                item.action()

    def draw_items(self, surface, top=240):
        f = self.app.fonts
        for i, item in enumerate(self.items):
            y = top + i * 50
            if not item.enabled():
                draw_text(surface, item.label, f["medium"], (70, 70, 85), (WIDTH // 2, y))
            elif i == self.index:
                draw_text(surface, "> " + item.label + " <", f["medium"], GOLD, (WIDTH // 2, y))
            else:
                draw_text(surface, item.label, f["medium"], WHITE, (WIDTH // 2, y))

    def draw(self, surface):
        draw_text(surface, self.title, self.app.fonts["large"], self.title_color, (WIDTH // 2, 120))
        self.draw_items(surface)


class MainMenuScreen(MenuScreen):
    title = "SHOOTER - TP4"

    def build_items(self):
        app = self.app
        return [
            MenuItem("Play", app.start_new_game),
            MenuItem("Continue", app.continue_game, lambda: app.data.has_run),
            MenuItem("Options", lambda: app.push(OptionsScreen(app))),
            MenuItem("Credits", lambda: app.push(CreditsScreen(app))),
            MenuItem("Exit", app.quit),
        ]

    def draw(self, surface):
        self.app.menu_background.draw(surface, self.app.ticks)
        dim(surface, 90)
        super().draw(surface)
        d, f = self.app.data, self.app.fonts
        draw_text(surface, f"High score: {d.high_score}     Coins: {d.coins}", f["small"], GOLD,
                  (WIDTH // 2, HEIGHT - 60))


class PauseScreen(MenuScreen):
    transparent = True
    title = "PAUSE"

    def __init__(self, app, board):
        self.board = board
        super().__init__(app)
        app.audio.pause_music()

    def build_items(self):
        app = self.app
        return [
            MenuItem("Resume", self.app.pop),
            MenuItem("Shop", lambda: app.push(ShopScreen(app, self.board)),
                     lambda: self.board.state != "GAME_OVER"),
            MenuItem("Options", lambda: app.push(OptionsScreen(app))),
            MenuItem("Save & Main menu", self.quit_to_menu),
        ]

    def quit_to_menu(self):
        if self.board.state == "PLAYING":
            self.board.snapshot(self.board.level)
        app = self.app
        app.save()
        app.to_main_menu()

    def on_escape(self):
        self.app.pop()

    def on_exit(self):
        self.app.audio.resume_music()

    def draw(self, surface):
        dim(surface)
        super().draw(surface)


class GameOverScreen(MenuScreen):
    transparent = True
    title = "GAME OVER"
    title_color = (255, 70, 70)

    def __init__(self, app, board):
        self.board = board
        super().__init__(app)

    def build_items(self):
        return [MenuItem("Play again", self.app.start_new_game),
                MenuItem("Main menu", self.app.to_main_menu)]

    def draw(self, surface):
        dim(surface, 170)
        super().draw(surface)
        f, d = self.app.fonts, self.app.data
        draw_text(surface, f"Score: {self.board.score}    High score: {d.high_score}", f["small"], WHITE,
                  (WIDTH // 2, 180))
        draw_text(surface, f"Reached level {self.board.level}", f["small"], WHITE, (WIDTH // 2, 205))


# ======================================================================
# Options et credits
# ======================================================================
class OptionsScreen(Screen):
    transparent = True
    ROWS = ["Master volume", "Music volume", "SFX volume", "Show FPS", "Back"]

    def __init__(self, app):
        super().__init__(app)
        self.index = 0

    def _value(self, row):
        d = self.app.data
        return [d.master_volume, d.music_volume, d.sfx_volume, d.show_fps][row]

    def _change(self, step):
        d, row = self.app.data, self.index
        if row == 3:
            d.show_fps = not d.show_fps
        elif row < 3:
            names = ["master_volume", "music_volume", "sfx_volume"]
            setattr(d, names[row], round(max(0.0, min(1.0, getattr(d, names[row]) + step * 0.1)), 1))
        self.app.apply_options()
        self.app.audio.play("click")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(self.ROWS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(self.ROWS)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._change(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._change(1)
        elif event.key == pygame.K_ESCAPE or (is_enter(event) and self.index == 4):
            self.app.save()
            self.app.pop()
        elif is_enter(event) and self.index == 3:
            self._change(1)

    def draw(self, surface):
        dim(surface, 200)
        f = self.app.fonts
        draw_text(surface, "OPTIONS", f["large"], GOLD, (WIDTH // 2, 110))
        for i, row in enumerate(self.ROWS):
            y = 220 + i * 55
            color = GOLD if i == self.index else WHITE
            draw_text(surface, row, f["medium"], color, (200, y), "left")
            if i < 3:
                v = self._value(i)
                pygame.draw.rect(surface, (60, 60, 80), (450, y - 8, 200, 16), border_radius=6)
                pygame.draw.rect(surface, color, (450, y - 8, int(200 * v), 16), border_radius=6)
                draw_text(surface, f"{int(v * 100)}%", f["small"], color, (670, y), "left")
            elif i == 3:
                draw_text(surface, "ON" if self._value(i) else "OFF", f["medium"], color, (450, y), "left")
        draw_text(surface, "Left/Right: change   Esc: back", f["small"], GRAY, (WIDTH // 2, HEIGHT - 50))


class CreditsScreen(Screen):
    LINES = ["CREDITS", "", "Game design & code: [Nom Prenom 1] - [Nom Prenom 2]",
             "Master 1 GSI - Universite AMO de Bouira", "Module MTI - TP 4", "",
             "Python 3 + Pygame", "Sounds and music generated by code", "", "Press any key to return"]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.app.pop()

    def draw(self, surface):
        self.app.menu_background.draw(surface, self.app.ticks)
        dim(surface, 160)
        f = self.app.fonts
        for i, line in enumerate(self.LINES):
            font = f["large"] if i == 0 else f["small"]
            draw_text(surface, line, font, GOLD if i == 0 else WHITE, (WIDTH // 2, 120 + i * 40))


# ======================================================================
# Partie
# ======================================================================
class GameScreen(Screen):
    def __init__(self, app, board):
        super().__init__(app)
        self.board = board
        self.over = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        b = self.board
        if event.key in (pygame.K_ESCAPE, pygame.K_p):
            self.app.push(PauseScreen(self.app, b))
        elif event.key == pygame.K_b and b.state == "LEVEL_CLEAR":
            self.app.push(ShopScreen(self.app, b))
        elif event.key == pygame.K_q:
            b.cycle_weapon(-1)
        elif event.key == pygame.K_e:
            b.cycle_weapon(1)
        elif pygame.K_1 <= event.key <= pygame.K_9:
            b.select_weapon(event.key - pygame.K_1)

    def update(self):
        b = self.board
        keys = pygame.key.get_pressed()
        if b.state != "GAME_OVER":
            b.player.handle_input(keys)
            if keys[pygame.K_SPACE]:
                b.fire()
        b.update()
        if b.needs_save:
            self.app.save()
            b.needs_save = False
        if b.pending_upgrades > 0 and b.state != "GAME_OVER":
            b.pending_upgrades -= 1
            self.app.push(UpgradeScreen(self.app, b))
        elif b.state == "GAME_OVER" and not self.over:
            self.over = True
            self.app.push(GameOverScreen(self.app, b))

    def draw(self, surface):
        r = self.app.renderer
        r.fps = self.app.clock.get_fps()
        r.show_fps = self.app.data.show_fps
        r.draw(surface, self.board, animate=self.app.top is self)


class UpgradeScreen(Screen):
    transparent = True

    def __init__(self, app, board):
        super().__init__(app)
        self.board = board
        self.choices = PlayerStats.random_choices(3)
        self.index = 0

    def _pick(self, i):
        choice = self.choices[i]
        self.board.stats.add_upgrade(choice.key)
        self.board.player.refresh_stats()
        self.app.audio.play("powerup")
        self.app.pop()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.index = (self.index - 1) % 3
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.index = (self.index + 1) % 3
        elif pygame.K_1 <= event.key <= pygame.K_3:
            self._pick(event.key - pygame.K_1)
        elif is_enter(event):
            self._pick(self.index)

    def draw(self, surface):
        dim(surface, 190)
        f = self.app.fonts
        draw_text(surface, "LEVEL UP!", f["large"], GOLD, (WIDTH // 2, 110))
        draw_text(surface, f"You are now level {self.board.stats.level} - choose an upgrade",
                  f["small"], WHITE, (WIDTH // 2, 160))
        for i, up in enumerate(self.choices):
            rect = pygame.Rect(70 + i * 230, 220, 210, 230)
            selected = i == self.index
            pygame.draw.rect(surface, (40, 45, 80) if selected else (28, 28, 45), rect, border_radius=12)
            pygame.draw.rect(surface, GOLD if selected else GRAY, rect, 3, border_radius=12)
            draw_text(surface, str(i + 1), f["large"], GOLD, (rect.centerx, rect.y + 45))
            draw_text(surface, up.title, f["small"], WHITE, (rect.centerx, rect.y + 110))
            draw_text(surface, up.description, f["tiny"], GRAY, (rect.centerx, rect.y + 150))
        draw_text(surface, "Press 1 / 2 / 3 or use arrows + Enter", f["small"], GRAY, (WIDTH // 2, HEIGHT - 60))


class ShopScreen(Screen):
    transparent = True

    def __init__(self, app, board):
        super().__init__(app)
        self.board = board
        self.shop = Shop(app.data, board.stats)
        self.index = 0
        self.message = ""

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        items = self.shop.items()
        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(items)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(items)
        elif event.key in (pygame.K_ESCAPE, pygame.K_b):
            self.app.save()
            self.app.pop()
        elif is_enter(event):
            item = items[self.index]
            ok, self.message = self.shop.buy(item)
            self.app.audio.play("coin" if ok else "hurt")
            if ok:
                self.board.player.refresh_stats()
                if item.kind == "weapon":
                    self.board.weapon_name = item.key
                self.app.save()

    def draw(self, surface):
        dim(surface, 200)
        f = self.app.fonts
        panel = pygame.Rect(120, 50, 560, 500)
        pygame.draw.rect(surface, (24, 24, 40), panel, border_radius=14)
        pygame.draw.rect(surface, GOLD, panel, 3, border_radius=14)
        draw_text(surface, "SHOP", f["large"], GOLD, (WIDTH // 2, 90))
        draw_text(surface, f"Coins: {self.app.data.coins}", f["medium"], GOLD, (WIDTH // 2, 135))
        for i, item in enumerate(self.shop.items()):
            y = 180 + i * 31
            selected = i == self.index
            owned = self.shop.owned(item)
            if selected:
                pygame.draw.rect(surface, (45, 50, 85), (140, y - 14, 520, 28), border_radius=6)
            color = GRAY if owned else (WHITE if self.shop.can_buy(item) else (150, 90, 90))
            draw_text(surface, item.label, f["small"], color, (160, y), "left")
            right = "OWNED" if owned else f"{self.shop.price(item)} coins"
            draw_text(surface, right, f["small"], color, (640, y), "right")
        draw_text(surface, self.message, f["small"], WHITE, (WIDTH // 2, 500))
        draw_text(surface, "Up/Down: select   Enter: buy   Esc: back", f["tiny"], GRAY, (WIDTH // 2, 528))
