"""Constantes globales du TP4."""
import os

WIDTH, HEIGHT, FPS = 800, 600, 60
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_FILE = os.path.join(ROOT_DIR, "savegame.json")
