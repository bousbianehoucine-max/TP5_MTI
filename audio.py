"""Musique et effets sonores.

Les sons sont GENERES par le code (aucun fichier necessaire). Si un fichier
assets/sounds/<nom>.wav (ou .ogg) existe, il remplace le son genere.
Si la carte son n'est pas disponible, le jeu continue sans son.
"""
import math
import os
import random
from array import array

import pygame

from tp4.settings import ROOT_DIR

SAMPLE_RATE = 44100


def _wave(kind, phase):
    s = math.sin(phase)
    return s if kind == "sine" else (1.0 if s >= 0 else -1.0)


def _tone(duration, freq, end_freq=None, vol=0.4, noise=0.0, decay=4.0, wave="sine"):
    end_freq = end_freq or freq
    n = int(SAMPLE_RATE * duration)
    buf, phase = array("h"), 0.0
    for i in range(n):
        k = i / n
        phase += math.tau * (freq + (end_freq - freq) * k) / SAMPLE_RATE
        s = _wave(wave, phase) * (1 - noise) + random.uniform(-1, 1) * noise
        buf.append(int(32767 * vol * s * math.exp(-decay * k)))
    return buf


def _arpeggio(freqs, note_len, vol=0.3):
    buf = array("h")
    for f in freqs:
        buf.extend(_tone(note_len, f, vol=vol, decay=2.5, wave="square"))
    return buf


def _music():
    chords = [(220, 261, 329), (175, 220, 262), (262, 330, 392), (196, 247, 294)]  # Am F C G
    buf = array("h")
    for chord in chords:
        for i in range(8):
            f = chord[[0, 1, 2, 1][i % 4]] * (2 if i >= 4 else 1)
            note = _tone(0.2, f, vol=0.13, decay=1.8, wave="square")
            bass = _tone(0.2, chord[0] / 2, vol=0.12, decay=1.2)
            buf.extend(array("h", (a + b for a, b in zip(note, bass))))
    return buf


SFX = {
    "shoot": lambda: _tone(0.10, 880, 440, 0.25, wave="square", decay=5),
    "laser": lambda: _tone(0.12, 1800, 600, 0.22, decay=4),
    "rocket": lambda: _tone(0.25, 200, 80, 0.35, noise=0.5, decay=3),
    "ice": lambda: _tone(0.15, 1200, 1800, 0.22),
    "lightning": lambda: _tone(0.18, 300, 1500, 0.25, noise=0.4, wave="square"),
    "plasma": lambda: _tone(0.20, 500, 250, 0.3, wave="square"),
    "hit": lambda: _tone(0.06, 300, 150, 0.3, noise=0.4, decay=5),
    "explosion": lambda: _tone(0.45, 150, 40, 0.5, noise=0.8, decay=4),
    "coin": lambda: _tone(0.12, 1200, 1700, 0.25),
    "powerup": lambda: _tone(0.30, 500, 1200, 0.3),
    "levelup": lambda: _arpeggio([523, 659, 784, 1046], 0.1),
    "hurt": lambda: _tone(0.20, 220, 110, 0.4, noise=0.3, wave="square"),
    "click": lambda: _tone(0.04, 700, 700, 0.2),
    "teleport": lambda: _tone(0.25, 1500, 300, 0.25),
    "boss": lambda: _tone(0.60, 90, 60, 0.5, wave="square", decay=2),
}


class SoundManager:
    def __init__(self, master=0.7, music=0.5, sfx=0.8):
        self.master, self.music_volume, self.sfx_volume = master, music, sfx
        self.enabled = False
        self.sounds, self.music, self.channel = {}, None, None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
            pygame.mixer.set_reserved(1)
            self.channel = pygame.mixer.Channel(0)
            self.enabled = True
        except pygame.error:
            return
        for name, make in SFX.items():
            self.sounds[name] = self._load_file(name) or pygame.mixer.Sound(buffer=make().tobytes())
        self.music = self._load_file("music") or pygame.mixer.Sound(buffer=_music().tobytes())
        self._apply_volumes()

    @staticmethod
    def _load_file(name):
        for ext in (".wav", ".ogg"):
            path = os.path.join(ROOT_DIR, "assets", "sounds", name + ext)
            if os.path.exists(path):
                try:
                    return pygame.mixer.Sound(path)
                except pygame.error:
                    pass
        return None

    def _apply_volumes(self):
        if not self.enabled:
            return
        for snd in self.sounds.values():
            snd.set_volume(self.master * self.sfx_volume)
        self.channel.set_volume(self.master * self.music_volume)

    def set_volumes(self, master, music, sfx):
        self.master, self.music_volume, self.sfx_volume = master, music, sfx
        self._apply_volumes()

    def play(self, name):
        snd = self.sounds.get(name)
        if self.enabled and snd:
            snd.play()

    def start_music(self):
        if self.enabled and not self.channel.get_busy():
            self.channel.play(self.music, loops=-1)

    def pause_music(self):
        if self.enabled:
            self.channel.pause()

    def resume_music(self):
        if self.enabled:
            self.channel.unpause()
