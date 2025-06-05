import pygame

from constants import *
from vector import Vector2


class Text:
    def __init__(self, text, color, x, y, size, time=None, id=None, visible=True) -> None:
        self.id = id
        self.text = text
        self.color = color
        self.size = size
        self.visible = visible
        self.position = Vector2(x, y)
        self.timer = 0
        self.lifespan = time
        self.label = None
        self.destroy = False
        self.setupFont("PressStart2P-Regular.ttf")
        self.createLabel()

    def setupFont(self, fontpath) -> None:
        self.font = pygame.font.Font(fontpath, self.size)

    def createLabel(self) -> None:
        self.label = self.font.render(self.text, 1, self.color)

    def setText(self, newtext) -> None:
        self.text = str(newtext)
        self.createLabel()

    def update(self, dt) -> None:
        if self.lifespan is not None:
            self.timer += dt
            if self.timer >= self.lifespan:
                self.timer = 0
                self.lifespan = None
                self.destroy = True

    def render(self, screen) -> None:
        if self.visible:
            x, y = self.position.asTuple()
            screen.blit(self.label, (x, y))


class TextGroup:
    def __init__(self) -> None:
        self.nextid = 10
        self.alltext = {}
        self.setupText()
        self.showText(READYTXT)

    def addText(self, text, color, x, y, size, time=None, id=None):
        self.nextid += 1
        self.alltext[self.nextid] = Text(text, color, x, y, size, time=time, id=id)
        return self.nextid

    def removeText(self, id) -> None:
        self.alltext.pop(id)

    def setupText(self) -> None:
        size = TILEHEIGHT # Default size for SCORE, LEVEL etc.
        small_size = TILEHEIGHT // 2 # Smaller size for HI-SCORE, or a fixed value like 10

        self.alltext[SCORETXT] = Text("0".zfill(8), WHITE, 0, TILEHEIGHT, size)
        self.alltext[LEVELTXT] = Text(str(1).zfill(3), WHITE, 23*TILEWIDTH, TILEHEIGHT, size)
        self.alltext[READYTXT] = Text("READY!", YELLOW, 11.25*TILEWIDTH, 20*TILEHEIGHT, size, visible=False)
        self.alltext[PAUSETXT] = Text("PAUSED!", YELLOW, 10.625*TILEWIDTH, 20*TILEHEIGHT, size, visible=False)
        self.alltext[GAMEOVERTXT] = Text("GAMEOVER!", YELLOW, 10*TILEWIDTH, 20*TILEHEIGHT, size, visible=False)
        self.addText("SCORE", WHITE, 0, 0, size)
        self.addText("LEVEL", WHITE, 23*TILEWIDTH, 0, size)

        # 移除舊的 HI-SCORE 顯示 (如果之前有)
        if HISCORELABELTXT in self.alltext:
            self.removeText(HISCORELABELTXT)
        if HISCOREVALUETXT in self.alltext:
            self.removeText(HISCOREVALUETXT)

        # 新增最高分顯示在底部中間，字型較小
        # 為了更好地居中，我們可能需要先渲染一次文字以獲取寬度，或者估算一個 X 位置
        # 估算 HI-SCORE 標籤的 X 位置使其大致居中
        # "HI-SCORE" 大約 8 個字元，小字型時寬度可能在 8 * small_size 左右
        hiscore_label_x = (SCREENWIDTH // 2) - (8 * small_size // 2) # 估算X使其居中
        hiscore_value_x = (SCREENWIDTH // 2) - (8 * small_size // 2) # 最高分值也大致居中

        self.alltext[HISCORELABELTXT] = Text("HI-SCORE", WHITE, hiscore_label_x, SCREENHEIGHT - (2 * small_size) - 10, small_size, id=HISCORELABELTXT) # HI-SCORE 標籤
        self.alltext[HISCOREVALUETXT] = Text("0".zfill(8), WHITE, hiscore_value_x, SCREENHEIGHT - small_size - 5, small_size) # HI-SCORE 值 (在標籤下方)

    def update(self, dt) -> None:
        for tkey in list(self.alltext.keys()):
            self.alltext[tkey].update(dt)
            if self.alltext[tkey].destroy:
                self.removeText(tkey)

    def showText(self, id) -> None:
        self.hideText()
        self.alltext[id].visible = True

    def hideText(self) -> None:
        self.alltext[READYTXT].visible = False
        self.alltext[PAUSETXT].visible = False
        self.alltext[GAMEOVERTXT].visible = False

    def updateScore(self, score) -> None:
        self.updateText(SCORETXT, str(score).zfill(8))

    def updateLevel(self, level) -> None:
        self.updateText(LEVELTXT, str(level + 1).zfill(3))

    def updateHighScore(self, high_score: int) -> None:
        """Updates the displayed high score."""
        self.updateText(HISCOREVALUETXT, str(high_score).zfill(8))

    def updateText(self, id, value) -> None:
        if id in self.alltext:
            self.alltext[id].setText(value)

    def render(self, screen) -> None:
        for tkey in list(self.alltext.keys()):
            self.alltext[tkey].render(screen)
