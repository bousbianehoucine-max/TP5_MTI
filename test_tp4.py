"""Tests pytest du TP4 (logique pure, sans fenetre): py -m pytest test_tp4.py"""
import os
import tempfile

from homework_monsters import Weapon
from tp4.enemies import (AIContext, ChaseBehavior, EnemyFactory, EvadeBehavior,
                         KeepDistanceBehavior, LowHealthFlee, TeleportBehavior)
from tp4.progression import LevelManager, PlayerStats, Shop
from tp4.save import SaveData, SaveManager
from tp4.weapons import WEAPONS, get_weapon


def make(key="normal", hp=1.0):
    return EnemyFactory().create(key, 600, 300, hp, 1.0)


def test_xp_and_level_up():
    stats = PlayerStats(SaveData())
    assert stats.gain_xp(10) == 0
    assert stats.gain_xp(1000) >= 2 and stats.level >= 3


def test_levels_are_unlimited_and_harder():
    lm = LevelManager()
    a, b = lm.config(1), lm.config(30)
    assert b.hp_mult > a.hp_mult and b.speed_mult > a.speed_mult and b.count >= a.count
    assert lm.config(5).boss and lm.config(10).boss and lm.config(5).boss != lm.config(10).boss
    assert lm.config(4).boss is None


def test_shop_buy_weapon_and_stat():
    data = SaveData(coins=500)
    shop = Shop(data, PlayerStats(data))
    laser = next(i for i in shop.items() if i.key == "Laser")
    assert shop.buy(laser)[0] and "Laser" in data.unlocks and data.coins == 400
    assert not shop.buy(laser)[0]                       # deja achete
    hp = next(i for i in shop.items() if i.key == "hp")
    p1 = shop.price(hp)
    assert shop.buy(hp)[0] and shop.price(hp) > p1       # le prix augmente
    data.coins = 0
    assert not shop.buy(hp)[0]


def test_save_roundtrip_and_corrupt_file():
    path = os.path.join(tempfile.mkdtemp(), "s.json")
    mgr = SaveManager(path)
    d = SaveData(high_score=99, coins=7)
    d.unlocks.append("Laser")
    mgr.save(d)
    loaded = mgr.load()
    assert loaded.high_score == 99 and "Laser" in loaded.unlocks
    open(path, "w").write("{not json")
    assert mgr.load().coins == 0                         # fichier corrompu -> valeurs par defaut


def test_damage_strategies():
    ice, fire, ice_gun = make("ice"), get_weapon("Fireball"), get_weapon("Ice Gun")
    assert ice.monster.take_hit(Weapon("f", 40, "fire")) == 60      # faible au feu x1.5
    assert ice.monster.take_hit(Weapon("i", 40, "ice")) == 8        # resistant a la glace
    tank = make("tank")
    assert tank.monster.take_hit(Weapon("b", 40, "bullet")) < 20    # bouclier + resistance


def test_flee_when_low_health():
    e = make("normal")
    e.behavior = LowHealthFlee(ChaseBehavior(), 0.2)
    e.monster.health.hp = 5
    ctx = AIContext(100, 300, [e], 0)
    x0 = e.x
    e.behavior.move(e, ctx)
    assert e.x > x0                                       # s'eloigne du joueur (a gauche)


def test_keep_distance_and_chase():
    e = make("shooter")
    ctx = AIContext(100, 300, [e], 0)
    e.behavior = KeepDistanceBehavior(260, 40)
    x0 = e.x
    e.behavior.move(e, ctx)
    assert e.x < x0                                       # trop loin -> s'approche
    e2 = make("fast")
    e2.behavior = EvadeBehavior()
    e2.behavior.move(e2, ctx)


def test_teleport_event():
    e = make("teleport")
    b = TeleportBehavior(ChaseBehavior(), interval=1)
    ctx = AIContext(100, 300, [e], 0)
    b.move(e, ctx)
    assert ctx.events and ctx.events[0][0] == "teleport"


def test_all_weapons_and_enemies_exist():
    assert {w.name for w in WEAPONS} >= {"Laser", "Rocket", "Ice Gun", "Lightning", "Plasma"}
    for key in ("ice", "poison", "teleport", "tank", "boss_golem"):
        assert make(key).monster.alive
