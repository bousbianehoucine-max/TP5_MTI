"""TP5 - Partie 2: Abstract Factory (formes 2D et 3D)."""
from abc import ABC, abstractmethod


class Circle(ABC):
    @abstractmethod
    def draw(self): ...
    @abstractmethod
    def erase(self): ...


class Square(ABC):
    @abstractmethod
    def draw(self): ...
    @abstractmethod
    def erase(self): ...


# 1) sous-classes
class Circle2D(Circle):
    def draw(self): print("Circle.draw2D")
    def erase(self): print("Circle.erase2D")


class Square2D(Square):
    def draw(self): print("Square.draw2D")
    def erase(self): print("Square.erase2D")


class Circle3D(Circle):
    def draw(self): print("Circle.draw3D")
    def erase(self): print("Circle.erase3D")


class Square3D(Square):
    def draw(self): print("Square.draw3D")
    def erase(self): print("Square.erase3D")


# 2) fabrique abstraite
class ShapeFactory(ABC):
    @staticmethod
    @abstractmethod
    def createShape(type):
        pass


# 3) fabriques concretes
class ShapeFactory2D(ShapeFactory):
    @staticmethod
    def createShape(type):
        if type == "Circle": return Circle2D()
        elif type == "Square": return Square2D()
        return None


class ShapeFactory3D(ShapeFactory):
    @staticmethod
    def createShape(type):
        if type == "Circle": return Circle3D()
        elif type == "Square": return Square3D()
        return None


# 4) utilisation: le client ne depend que de ShapeFactory
def render(factory: type[ShapeFactory]):
    for type_ in ("Circle", "Square", "Circle", "Square"):
        shape = factory.createShape(type_)
        shape.draw()
        shape.erase()


if __name__ == "__main__":
    print("--- 2D ---"); render(ShapeFactory2D)
    print("--- 3D ---"); render(ShapeFactory3D)
