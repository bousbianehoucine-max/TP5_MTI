"""TP5 - Partie 3: Singleton (fichier, base de donnees, acces simultanes limites)."""
import sqlite3
import tempfile
import os


class Singleton:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = object.__new__(cls)
        return cls.instance


# 1) acces unique a un fichier en ecriture
class FileWriter:
    _instance = None

    def __new__(cls, path="output.txt"):
        if cls._instance is None:
            inst = object.__new__(cls)
            inst.path = path
            inst._file = open(path, "a", encoding="utf-8")
            cls._instance = inst
        return cls._instance

    def write(self, text):
        self._file.write(text + "\n")
        self._file.flush()

    def close(self):
        if self._file and not self._file.closed:
            self._file.close()
        FileWriter._instance = None


# 2) connexion unique a une base de donnees
class Database:
    _instance = None

    def __new__(cls, path=":memory:"):
        if cls._instance is None:
            inst = object.__new__(cls)
            inst.connection = sqlite3.connect(path)
            cls._instance = inst
        return cls._instance

    def execute(self, sql, params=()):
        return self.connection.execute(sql, params)

    def close(self):
        self.connection.close()
        Database._instance = None


# 3) amelioration: un nombre LIMITE d'acces simultanes (pool d'instances)
class LimitedResource:
    """N acces simultanes au maximum. acquire() reutilise les ressources libres."""

    def __init__(self, factory, limit=3):
        self._factory, self.limit = factory, limit
        self._free, self._used = [], []

    def acquire(self):
        if self._free:
            res = self._free.pop()
        elif len(self._used) < self.limit:
            res = self._factory()
        else:
            raise RuntimeError(f"limit reached ({self.limit} simultaneous accesses)")
        self._used.append(res)
        return res

    def release(self, res):
        self._used.remove(res)
        self._free.append(res)


if __name__ == "__main__":
    a, b = Singleton(), Singleton()
    assert a is b
    tmp = os.path.join(tempfile.gettempdir(), "tp5_demo.txt")
    f1, f2 = FileWriter(tmp), FileWriter(tmp)
    assert f1 is f2
    f1.write("hello"); f1.close()

    d1, d2 = Database(), Database()
    assert d1 is d2
    d1.execute("create table t(x)"); d1.execute("insert into t values (1)")
    print("rows:", d1.execute("select * from t").fetchall()); d1.close()

    pool = LimitedResource(lambda: sqlite3.connect(":memory:"), limit=2)
    c1, c2 = pool.acquire(), pool.acquire()
    try:
        pool.acquire()
    except RuntimeError as e:
        print("OK:", e)
    pool.release(c1)
    assert pool.acquire() is c1
