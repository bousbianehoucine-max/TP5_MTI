"""TP5 - Partie 4: Builder (Story, Sandwich, Car)."""
from dataclasses import dataclass, field


# ======================================================================
# Stories (Facebook / Instagram / Youtube)
# ======================================================================
class Story:
    def __init__(self):
        self.parts = []

    def add(self, part):
        self.parts.append(part)

    def show(self):
        print(self.parts)


class Builder:
    def __init__(self):
        self.story = Story()

    def _build_image(self): pass
    def _build_music(self): pass
    def _build_effet(self): pass
    def _build_video(self): pass


class StoryDirector:
    def __init__(self):
        self._builder = None

    def construct(self, builder):
        self._builder = builder

    def basic_story(self):
        print("*** create basic story ***")
        self._builder._build_image()

    def photo_music_story(self):
        print("*** create photo + music story ***")
        self._builder._build_image()
        self._builder._build_music()
        self._builder._build_effet()

    def video_story(self):
        print("*** create video story ***")
        self._builder._build_video()
        self._builder._build_effet()


class _NamedBuilder(Builder):
    network = ""

    def _build_image(self): self.story.add(f"image {self.network}")
    def _build_music(self): self.story.add(f"music {self.network}")
    def _build_effet(self): self.story.add(f"effect {self.network}")
    def _build_video(self): self.story.add(f"video {self.network}")


class FacebookConcreteBuilder(_NamedBuilder):
    network = "facebook"


class InstagramConcreteBuilder(_NamedBuilder):
    network = "Instagram"


class YoutubeConcreteBuilder(_NamedBuilder):
    network = "Youtube"


def main():
    fb = FacebookConcreteBuilder()
    director = StoryDirector()
    director.construct(fb)
    director.basic_story()
    fb.story.show()

    insta = InstagramConcreteBuilder()
    director = StoryDirector()
    director.construct(insta)
    director.video_story()
    insta.story.show()


# ======================================================================
# Question 1-2: Sandwich + configurations nommees
# ======================================================================
@dataclass
class Sandwich:
    bread: str = "baguette"
    ingredients: list = field(default_factory=list)
    sauces: list = field(default_factory=list)

    def __str__(self):
        return f"Sandwich({self.bread}: {', '.join(self.ingredients)} | sauces: {', '.join(self.sauces) or 'none'})"


class SandwichBuilder:
    def __init__(self):
        self.reset()

    def reset(self):
        self._s = Sandwich()
        return self

    def bread(self, b): self._s.bread = b; return self
    def add(self, *items): self._s.ingredients += items; return self
    def sauce(self, *items): self._s.sauces += items; return self

    def build(self):
        s, self._s = self._s, Sandwich()
        return s


class SandwichDirector:
    """Les configurations nommees."""

    def __init__(self, builder):
        self.b = builder

    def shawarma(self):
        return self.b.bread("pita").add("chicken", "pickles", "fries").sauce("garlic").build()

    def ground_meat(self):
        return self.b.bread("baguette").add("ground meat", "tomato", "onion").sauce("harissa").build()

    def fried_with_omelet(self):
        return self.b.bread("baguette").add("fries", "omelet", "olives").sauce("mayonnaise").build()


# ======================================================================
# Question 3: Voiture selon les options commandees
# ======================================================================
@dataclass
class Car:
    model: str = "basic"
    engine: str = "1.2"
    options: list = field(default_factory=list)

    def __str__(self):
        return f"Car({self.model}, engine {self.engine}, options: {', '.join(self.options) or 'none'})"


class CarBuilder:
    def __init__(self):
        self._c = Car()

    def model(self, m): self._c.model = m; return self
    def engine(self, e): self._c.engine = e; return self
    def with_ac(self): self._c.options.append("air conditioning"); return self
    def with_gps(self): self._c.options.append("GPS"); return self
    def with_sunroof(self): self._c.options.append("sunroof"); return self
    def with_leather(self): self._c.options.append("leather seats"); return self
    def build(self): return self._c


class CarDirector:
    @staticmethod
    def basic():
        return CarBuilder().build()

    @staticmethod
    def full():
        return (CarBuilder().model("full").engine("1.6 turbo")
                .with_ac().with_gps().with_sunroof().with_leather().build())


if __name__ == "__main__":
    main()
    d = SandwichDirector(SandwichBuilder())
    print(d.shawarma()); print(d.ground_meat()); print(d.fried_with_omelet())
    print(CarDirector.basic()); print(CarDirector.full())
    print(CarBuilder().model("city").with_ac().with_gps().build())     # a la carte
