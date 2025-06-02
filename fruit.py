from constants import *
from entity import Entity
from sprites import FruitSprites


class Fruit(Entity):
    def __init__(self, node, level=0) -> None:
        Entity.__init__(self, node)
        self.name = FRUIT
        self.color = GREEN
        self.lifespan = 5
        self.timer = 0
        self.destroy = False
        self.points = 100 + level*20
        self.setBetweenNodes(RIGHT)
        self.sprites = FruitSprites(self, level)

    def update(self, dt) -> None:
        self.timer += dt
        if self.timer >= self.lifespan:
            self.destroy = True
