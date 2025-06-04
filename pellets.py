import numpy as np
import pygame

from constants import *
from vector import Vector2


class Pellet:
    def __init__(self, row: int, column: int) -> None:
        self.name = PELLET
        self.position = Vector2(column*TILEWIDTH, row*TILEHEIGHT)
        self.color = WHITE
        self.radius = int(2 * TILEWIDTH / 16)
        self.collideRadius = 2 * TILEWIDTH / 16
        self.points = 10
        self.visible = True

    def render(self, screen) -> None:
        if self.visible:
            adjust = Vector2(TILEWIDTH, TILEHEIGHT) / 2
            p = self.position + adjust
            pygame.draw.circle(screen, self.color, p.asInt(), self.radius)


class PowerPellet(Pellet):
    def __init__(self, row: int, column: int) -> None:
        super().__init__(row, column)
        self.name = POWERPELLET
        self.radius = int(8 * TILEWIDTH / 16)
        self.points = 50
        self.flashTime = 0.2
        self.timer= 0

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.timer >= self.flashTime:
            self.visible = not self.visible
            self.timer = 0


class TeleportPellet(Pellet):
    def __init__(self, row: int, column: int) -> None:
        super().__init__(row, column)
        self.name = TELEPORTPELLET
        self.color = CYAN
        self.points = 20


class InvisibilityPellet(Pellet):
    def __init__(self, row: int, column: int) -> None:
        super().__init__(row, column)
        self.name = INVISIBILITYPELLET
        self.color = GREY
        self.points = 30


# New Pellet Type: SpeedBoostPellet
class SpeedBoostPellet(Pellet):
    def __init__(self, row: int, column: int) -> None:
        super().__init__(row, column)
        self.name = SPEEDBOOSTPELLET
        self.color = LIMEGREEN
        self.points = 25


# New Pellet Type: ScoreMagnetPellet
class ScoreMagnetPellet(Pellet):
    def __init__(self, row: int, column: int) -> None:
        super().__init__(row, column)
        self.name = SCOREMAGNETPELLET
        self.color = PURPLE
        self.points = 15


class PelletGroup:
    def __init__(self, pelletfile: str) -> None:
        self.pelletList: list[Pellet] = []
        self.powerpellets: list[PowerPellet] = []
        self.createPelletList(pelletfile)
        self.numEaten = 0

    def update(self, dt: float) -> None:
        for powerpellet in self.powerpellets:
            powerpellet.update(dt)

    def createPelletList(self, pelletfile: str) -> None:
        data = self.readPelletfile(pelletfile)
        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                if data[row][col] in [".", "+"]:
                    self.pelletList.append(Pellet(row, col))
                elif data[row][col] in ["P", "p"]:
                    pp = PowerPellet(row, col)
                    self.pelletList.append(pp)
                    self.powerpellets.append(pp)
                elif data[row][col] == "T":
                    tp = TeleportPellet(row, col)
                    self.pelletList.append(tp)
                elif data[row][col] == "I":
                    ip = InvisibilityPellet(row, col)
                    self.pelletList.append(ip)
                elif data[row][col] == "S":
                    sp = SpeedBoostPellet(row, col)
                    self.pelletList.append(sp)
                elif data[row][col] == "M":
                    mp = ScoreMagnetPellet(row, col)
                    self.pelletList.append(mp)

    def readPelletfile(self, textfile: str) -> np.ndarray:
        return np.loadtxt(textfile, dtype="<U1")

    def isEmpty(self) -> bool:
        return len(self.pelletList) == 0

    def render(self, screen) -> None:
        for pellet in self.pelletList:
            pellet.render(screen)
