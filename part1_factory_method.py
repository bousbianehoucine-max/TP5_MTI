"""TP5 - Partie 1: Sans design pattern -> Simple Factory -> Factory Method (+ application stock)."""
import sys
from abc import ABC, abstractmethod


# ======================================================================
# 1) SANS design pattern (le client fait les if/elif lui-meme)
# ======================================================================
class Shape(ABC):
    @abstractmethod
    def draw(self): ...

    @abstractmethod
    def erase(self): ...


class Circle(Shape):
    def draw(self): print("Circle.draw")
    def erase(self): print("Circle.erase")


class Square(Shape):
    def draw(self): print("Square.draw")
    def erase(self): print("Square.erase")


class Triangle(Shape):                      # ajoute (question 2)
    def draw(self): print("Triangle.draw")
    def erase(self): print("Triangle.erase")


class Rectangle(Shape):                     # ajoute (question 2)
    def draw(self): print("Rectangle.draw")
    def erase(self): print("Rectangle.erase")


def without_pattern():
    for type_ in ("Circle", "Square", "Triangle", "Rectangle"):
        if type_ == "Circle":
            shape = Circle()
        elif type_ == "Square":
            shape = Square()
        elif type_ == "Triangle":
            shape = Triangle()
        elif type_ == "Rectangle":
            shape = Rectangle()
        else:
            print("Bad shape creation: " + type_)
            sys.exit()
        shape.draw()
        shape.erase()


# ======================================================================
# 2) SIMPLE FACTORY: la creation est encapsulee dans ShapeFactory
# ======================================================================
class ShapeFactory:
    @staticmethod
    def createShape(type):
        if type == "Circle": return Circle()
        elif type == "Square": return Square()
        elif type == "Triangle": return Triangle()
        elif type == "Rectangle": return Rectangle()
        raise ValueError("Bad shape creation: " + type)


def simple_factory():
    for type_ in ("Circle", "Square", "Triangle", "Rectangle"):
        shape = ShapeFactory.createShape(type_)
        shape.draw()
        shape.erase()


# ======================================================================
# 3) FACTORY METHOD: fabriques specialisees
# ======================================================================
class ShapeFactoryBase(ABC):
    """Createur abstrait: chaque sous-classe decide quelles formes elle sait produire."""
    available = {}

    @classmethod
    def createShape(cls, type):
        try:
            return cls.available[type]()
        except KeyError:
            raise ValueError(f"{cls.__name__} cannot create: {type}") from None


class ShapeFactory_SCT(ShapeFactoryBase):   # Square, Circle, Triangle seulement
    available = {"Square": Square, "Circle": Circle, "Triangle": Triangle}


class ShapeFactory_SCR(ShapeFactoryBase):   # Square, Circle, Rectangle seulement
    available = {"Square": Square, "Circle": Circle, "Rectangle": Rectangle}


# ======================================================================
# 4) APPLICATION: gestion de stock avec 3 types de comptes
#    Pattern propose: FACTORY METHOD (un createur par type de compte)
# ======================================================================
class Account(ABC):
    permissions = frozenset()

    def __init__(self, name):
        self.name = name

    def can(self, action):
        return action in self.permissions

    def __repr__(self):
        return f"{type(self).__name__}({self.name})"


class ManagerAccount(Account):
    permissions = frozenset({"manage_stock", "purchase", "order", "see_income", "sell", "view_stock"})


class SellerAccount(Account):
    permissions = frozenset({"sell", "purchase", "order", "view_stock"})


class VisitorAccount(Account):
    permissions = frozenset({"view_stock", "purchase", "order"})


class AccountCreator(ABC):
    @abstractmethod
    def create_account(self, name) -> Account:
        """Methode fabrique."""

    def open_account(self, name):
        account = self.create_account(name)
        print(f"[stock] account opened: {account} -> {sorted(account.permissions)}")
        return account


class ManagerCreator(AccountCreator):
    def create_account(self, name): return ManagerAccount(name)


class SellerCreator(AccountCreator):
    def create_account(self, name): return SellerAccount(name)


class VisitorCreator(AccountCreator):
    def create_account(self, name): return VisitorAccount(name)


def stock_demo():
    for creator, name in ((ManagerCreator(), "Karim"), (SellerCreator(), "Sara"), (VisitorCreator(), "Guest")):
        acc = creator.open_account(name)
        print("  can see income?", acc.can("see_income"))


if __name__ == "__main__":
    print("--- sans pattern ---"); without_pattern()
    print("--- simple factory ---"); simple_factory()
    print("--- factory method ---")
    ShapeFactory_SCT.createShape("Triangle").draw()
    ShapeFactory_SCR.createShape("Rectangle").draw()
    try:
        ShapeFactory_SCT.createShape("Rectangle")
    except ValueError as e:
        print("OK, refused:", e)
    print("--- stock ---"); stock_demo()
