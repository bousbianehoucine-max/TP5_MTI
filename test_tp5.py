"""Tests pytest du TP5 (logique pure, sans fenetre): py -m pytest test_tp5.py"""
import pytest

from homework_monsters import Weapon
from tp5.monsters import (CreatorEnemyFactory, DragonMonster, MonsterCreator, RobotMonster,
                          ZombieMonster)
from tp5.singleton import PlayerManager, SingletonMeta
from tp5.worlds import FantasyWorldFactory, SpaceWorldFactory, World, WorldRotation
from workshop import part1_factory_method as p1
from workshop import part2_abstract_factory as p2
from workshop import part3_singleton as p3
from workshop import part4_builder as p4


# ---------------- Factory Method (monstres) ----------------
def test_creators_make_right_monsters():
    f = CreatorEnemyFactory()
    for key, cls in (("zombie", ZombieMonster), ("dragon", DragonMonster), ("robot", RobotMonster)):
        e = f.create(key, 600, 300)
        assert isinstance(e.monster, cls) and e.key == key
        assert f.monster_class(key) is cls


def test_old_keys_still_work_and_scaling():
    f = CreatorEnemyFactory()
    assert f.create("ice", 0, 0).monster.name == "Ice Monster"
    a, b = f.create("zombie", 0, 0, 1.0, 1.0), f.create("zombie", 0, 0, 2.0, 1.5)
    assert b.monster.health.max_hp == 2 * a.monster.health.max_hp
    assert b.monster.speed == pytest.approx(1.5 * a.monster.speed)
    assert b.xp > a.xp


def test_new_monster_without_touching_factory():           # OCP
    class GhostMonster(ZombieMonster):
        pass

    class GhostCreator(MonsterCreator):
        key, monster_cls = "ghost", GhostMonster

        def create_monster(self, x, y): return GhostMonster(x, y)
        def create_behavior(self): return None

    f = CreatorEnemyFactory()
    f.register(GhostCreator())
    assert isinstance(f.create("ghost", 1, 1).monster, GhostMonster)


def test_monster_damage_rules():
    f = CreatorEnemyFactory()
    assert f.create("zombie", 0, 0).monster.take_hit(Weapon("f", 40, "fire")) == 60
    assert f.create("dragon", 0, 0).monster.take_hit(Weapon("f", 40, "fire")) == 8
    assert f.create("robot", 0, 0).monster.take_hit(Weapon("l", 30, "lightning")) == 48


# ---------------- Abstract Factory (mondes) ----------------
def test_each_world_gives_its_own_family():
    space, fantasy = World(SpaceWorldFactory()), World(FantasyWorldFactory())
    assert "robot" in space.monsters.keys and "dragon" not in space.monsters.keys
    assert "dragon" in fantasy.monsters.keys and "robot" not in fantasy.monsters.keys
    assert space.rewards.coin_mult > fantasy.rewards.coin_mult


def test_roster_respects_unlock_levels_and_never_empty():
    fantasy = World(FantasyWorldFactory())
    assert "dragon" not in fantasy.monsters.roster(1) and "dragon" in fantasy.monsters.roster(3)
    assert fantasy.monsters.roster(1)


def test_rewards_favor_world_powerups():
    space = World(SpaceWorldFactory())
    kinds = [space.rewards.powerup_kind() for _ in range(400)]
    fav = sum(k in space.rewards.favorite_powerups for k in kinds)
    assert fav > 200


def test_rotation_one_world_per_level():
    r = WorldRotation()
    assert [r.for_level(n).name for n in (1, 2, 3, 4)] == ["Space", "Fantasy", "Space", "Fantasy"]


# ---------------- Singleton (joueur) ----------------
@pytest.fixture(autouse=True)
def fresh_manager():
    SingletonMeta._instances.pop(PlayerManager, None)
    yield
    SingletonMeta._instances.pop(PlayerManager, None)


def test_manager_is_singleton_and_one_player():
    assert PlayerManager() is PlayerManager()
    m, p1_, p2_ = PlayerManager(), object(), object()
    assert m.register(p1_) is p1_
    assert m.register(p2_) is p1_ and m.players == [p1_]       # pas de 2e joueur
    m.clear()
    assert m.register(p2_) is p2_


def test_manager_configurable_for_two_players():
    m = PlayerManager()
    m.set_max_players(2)
    a, b, c = object(), object(), object()
    assert m.register(a) is a and m.register(b) is b
    assert m.register(c) is a and len(m.players) == 2


# ---------------- Workshop ----------------
def test_workshop_shapes_and_factories(capsys):
    assert isinstance(p1.ShapeFactory.createShape("Triangle"), p1.Triangle)
    with pytest.raises(ValueError):
        p1.ShapeFactory_SCT.createShape("Rectangle")
    assert isinstance(p1.ShapeFactory_SCR.createShape("Rectangle"), p1.Rectangle)
    assert isinstance(p2.ShapeFactory2D.createShape("Circle"), p2.Circle2D)
    assert isinstance(p2.ShapeFactory3D.createShape("Square"), p2.Square3D)


def test_workshop_accounts():
    m = p1.ManagerCreator().create_account("a")
    s = p1.SellerCreator().create_account("b")
    v = p1.VisitorCreator().create_account("c")
    assert m.can("see_income") and not s.can("see_income") and not v.can("sell")
    assert v.can("view_stock") and v.can("order")


def test_workshop_singleton_and_pool(tmp_path):
    f1, f2 = p3.FileWriter(str(tmp_path / "x.txt")), p3.FileWriter()
    assert f1 is f2
    f1.close()
    d1 = p3.Database()
    assert d1 is p3.Database()
    d1.close()
    pool = p3.LimitedResource(object, limit=2)
    a, b = pool.acquire(), pool.acquire()
    with pytest.raises(RuntimeError):
        pool.acquire()
    pool.release(a)
    assert pool.acquire() is a


def test_workshop_builders():
    ig = p4.InstagramConcreteBuilder()
    d = p4.StoryDirector(); d.construct(ig); d.video_story()
    assert ig.story.parts == ["video Instagram", "effect Instagram"]
    assert "pita" in str(p4.SandwichDirector(p4.SandwichBuilder()).shawarma())
    assert len(p4.CarDirector.full().options) == 4 and p4.CarDirector.basic().options == []
