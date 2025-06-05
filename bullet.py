import pygame

from constants import *
from vector import Vector2


class Bullet:
    """子彈物件，負責移動、繪製與碰撞。."""

    def __init__(self, position: Vector2, direction: int) -> None:
        self.position = position.copy()
        self.direction = direction
        self.speed = 400  # 子彈速度，可調整
        self.image = pygame.image.load("bullet.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILEWIDTH, TILEHEIGHT))
        self.rect = self.image.get_rect(center=self.position.asInt())
        self.active = True

    def update(self, dt: float) -> None:
        if self.direction == LEFT:
            self.position.x -= self.speed * dt
        elif self.direction == RIGHT:
            self.position.x += self.speed * dt
        elif self.direction == UP:
            self.position.y -= self.speed * dt
        elif self.direction == DOWN:
            self.position.y += self.speed * dt
        self.rect.center = self.position.asInt()
        # 只在超出畫面時消失
        if (self.position.x < 0 or self.position.x > SCREENWIDTH or
            self.position.y < 0 or self.position.y > SCREENHEIGHT):
            self.active = False

    def render(self, screen) -> None:
        screen.blit(self.image, self.rect)
