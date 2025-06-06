import random
import time

import pygame
from pygame.locals import *

from bullet import Bullet
from constants import *
from entity import Entity

#修改地方
from nodes import NodeGroup  # For type hinting
from sprites import PacmanGunSprites, PacmanShieldSprites, PacmanSprites


class Pacman(Entity):
    def __init__(self, node) -> None:
        Entity.__init__(self, node )
        self.name = PACMAN
        self.color = YELLOW
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanSprites(self)
        #修改地方
        # Invisibility state
        self.is_invisible: bool = False
        self.invisibility_timer: float = 0.0
        self.invisibility_duration: float = 5.0 # Default duration, can be set by pellet
        self.default_alpha: int = 255
        self.invisible_alpha: int = 128 # Alpha value for semi-transparency
        # Speed boost state
        self.base_speed_value: float = self.speed # Capture the initial calculated speed
        self.is_boosted: bool = False
        self.speed_boost_timer: float = 0.0

    def reset(self) -> None:
        Entity.reset(self)
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()
        #修改地方
        # Reset invisibility state
        self.is_invisible = False
        self.invisibility_timer = 0.0
        if self.image: # Ensure image is not None before setting alpha
            self.image.set_alpha(self.default_alpha)
        # Reset speed boost state
        self.base_speed_value = self.speed # Re-capture base speed after Entity's reset
        self.is_boosted = False
        self.speed_boost_timer = 0.0

    def die(self) -> None:
        self.alive = False
        self.direction = STOP
        #修改地方
        # Reset invisibility state
        self.is_invisible = False # Should not be invisible when dead
        self.invisibility_timer = 0.0
        if self.image: # Ensure image is not None before setting alpha
            self.image.set_alpha(self.default_alpha)
        # Reset speed boost state (speed will be whatever it was, but boost effect ends)
        if self.is_boosted:
            self.speed = self.base_speed_value # Revert to base if was boosted
        self.is_boosted = False
        self.speed_boost_timer = 0.0

    def update(self, dt) -> None:
        self.sprites.update(dt)
        self.position += self.directions[self.direction]*self.speed*dt
        direction = self.getValidKey()
        if self.overshotTarget():
            self.node = self.target
            if self.node.neighbors[PORTAL] is not None:
                self.node = self.node.neighbors[PORTAL]
            self.target = self.getNewTarget(direction)
            if self.target is not self.node:
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)

            if self.target is self.node:
                self.direction = STOP
            self.setPosition()
        elif self.oppositeDirection(direction):
            self.reverseDirection()
        #修改地方
        # Invisibility logic
        if self.is_invisible:
            self.invisibility_timer -= dt
            if self.invisibility_timer <= 0:
                self.is_invisible = False
                self.invisibility_timer = 0.0
                if self.image: # Ensure image is not None
                    self.image.set_alpha(self.default_alpha)
            elif self.image: # Ensure image is not None
                self.image.set_alpha(self.invisible_alpha)
        elif self.image and self.image.get_alpha() != self.default_alpha:
             self.image.set_alpha(self.default_alpha)
        # Speed boost logic
        if self.is_boosted:
            self.speed_boost_timer -= dt
            if self.speed_boost_timer <= 0:
                self.is_boosted = False
                self.speed = self.base_speed_value # Revert to base speed
                self.speed_boost_timer = 0.0
                # print(f"Pacman speed boost ended. Speed reverted to {self.base_speed_value}")

    def getValidKey(self):
        key_pressed = pygame.key.get_pressed()
        if key_pressed[K_UP]:
            return UP
        if key_pressed[K_DOWN]:
            return DOWN
        if key_pressed[K_LEFT]:
            return LEFT
        if key_pressed[K_RIGHT]:
            return RIGHT
        return STOP

    def eatPellets(self, pelletList):
        for pellet in pelletList:
            if self.collideCheck(pellet):
                return pellet
        return None

    def collideGhost(self, ghost):
        #修改地方
        if self.is_invisible:
            return False # No collision if invisible
        return self.collideCheck(ghost)

    def collideCheck(self, other) -> bool:
        d = self.position - other.position
        dSquared = d.magnitudeSquared()
        rSquared = (self.collideRadius + other.collideRadius)**2
        return dSquared <= rSquared
    #修改地方
    def teleport(self, node_group: NodeGroup) -> None:
        """Teleports Pacman to a random valid node on the map, excluding ghost home nodes."""
        if node_group and node_group.nodesLUT:
            # Exclude home nodes
            home_nodes = set(node_group.getHomeNodes())
            possible_nodes = [n for pos, n in node_group.nodesLUT.items() if pos not in home_nodes]
            if possible_nodes:
                new_node = random.choice(possible_nodes)
                self.node = new_node
                self.target = new_node
                self.setPosition()

    def activate_invisibility(self, duration: float) -> None:
        """Activates Pacman's invisibility for a given duration."""
        self.is_invisible = True
        self.invisibility_timer = duration
        self.invisibility_duration = duration # Store it if needed elsewhere
        if self.image: # Ensure image is not None
            self.image.set_alpha(self.invisible_alpha)

    def activate_speed_boost(self, factor: float, duration: float) -> None:
        """Activates Pacman's speed boost for a given duration."""
        # A new boost always resets the timer and applies the new factor to the original base_speed_value.
        self.is_boosted = True
        self.speed_boost_timer = duration
        self.speed = self.base_speed_value * factor # Boost from the base speed


class PacmanGun(Pacman):
    def __init__(self, node) -> None:
        super().__init__(node)
        self.name = PACMAN
        self.color = (255, 255, 255)
        self.sprites = PacmanGunSprites(self)
        self.character_type = "gun"
        self.ability = GunAbility(self)

    def update(self, dt) -> None:
        super().update(dt)
        self.ability.update(dt)

    def render(self, screen) -> None:
        super().render(screen)
        self.ability.render(screen)

#射擊子彈技能
class GunAbility:
    """管理槍技能的啟動、冷卻、子彈發射與顯示."""

    def __init__(self, pacman) -> None:
        self.pacman = pacman
        self.state = "ready"  # ready, active, cooldown
        self.timer = 0.0
        self.cooldown = 10.0
        self.duration = 5.0
        self.bullets: list[Bullet] = []
        self.icon = pygame.image.load("ability_gun.png").convert_alpha()
        self.icon = pygame.transform.scale(self.icon, (48, 48))
        self.last_shot_time = 0.0

    def activate(self) -> None:
        if self.state == "ready":
            self.state = "active"
            self.timer = 0.0

    def update(self, dt: float) -> None:
        if self.state == "active":
            self.timer += dt
            if self.timer >= self.duration:
                self.state = "cooldown"
                self.timer = 0.0
        elif self.state == "cooldown":
            self.timer += dt
            if self.timer >= self.cooldown:
                self.state = "ready"
                self.timer = 0.0
        # 更新子彈
        for bullet in self.bullets:
            bullet.update(dt)
        self.bullets = [b for b in self.bullets if b.active]

    def shoot(self) -> None:
        if self.state == "active":
            now = time.time()
            # 可加射速限制
            if now - self.last_shot_time > 0.15:
                bullet = Bullet(self.pacman.position.copy(), self.pacman.direction)
                self.bullets.append(bullet)
                self.last_shot_time = now

    def render(self, screen) -> None:
        # 畫圖示
        x = SCREENWIDTH // 2 - 24
        y = 10
        screen.blit(self.icon, (x, y))
        # 畫倒數
        font = pygame.font.Font("PressStart2P-Regular.ttf", 18)
        if self.state == "cooldown":
            cd = int(self.cooldown - self.timer) + 1
            text = font.render(str(cd), True, (255, 0, 0))
            screen.blit(text, (x + 54, y + 8))
        # 畫子彈
        for bullet in self.bullets:
            bullet.render(screen)

class PacmanShield(Pacman):
    def __init__(self, node) -> None:
        super().__init__(node)
        self.name = PACMAN
        self.color = (0, 255, 255)
        self.sprites = PacmanShieldSprites(self)
        self.character_type = "shield"
        self.ability = ShieldAbility(self)

    def update(self, dt) -> None:
        super().update(dt)
        self.ability.update(dt)

    def render(self, screen) -> None:
        super().render(screen)
        self.ability.render(screen)

class ShieldAbility:
    """管理盾牌技能的啟動、冷卻、圖片切換、鬼魂碰撞等."""

    def __init__(self, pacman) -> None:
        self.pacman = pacman
        self.state = "ready"  # ready, active, cooldown
        self.timer = 0.0
        self.cooldown = 5.0
        self.duration = 3.0
        self.icon = pygame.image.load("ability_shield.png").convert_alpha()
        self.icon = pygame.transform.scale(self.icon, (48, 48))
        self.withshield_img = pygame.image.load("withshield.png").convert_alpha()
        self.withshield_img = pygame.transform.scale(self.withshield_img, (2*TILEWIDTH, 2*TILEHEIGHT))
        self.font = pygame.font.Font("PressStart2P-Regular.ttf", 18)
        self.active = False

    def activate(self) -> None:
        if self.state == "ready":
            self.state = "active"
            self.timer = 0.0
            self.active = True
            self.pacman.image = self.withshield_img

    def update(self, dt: float) -> None:
        if self.state == "active":
            self.timer += dt
            self.pacman.image = self.withshield_img
  # 持續顯示盾牌圖
            if self.timer >= self.duration:
                self.state = "cooldown"
                self.timer = 0.0
                self.active = False
                self.pacman.image = self.pacman.sprites.getStartImage()
        elif self.state == "cooldown":
            self.timer += dt
            if self.timer >= self.cooldown:
                self.state = "ready"
                self.timer = 0.0

    def render(self, screen) -> None:
        # 畫技能圖示
        x = SCREENWIDTH // 2 - 24
        y = 10
        screen.blit(self.icon, (x, y))
        # 畫倒數
        if self.state == "cooldown":
            cd = int(self.cooldown - self.timer) + 1
            text = self.font.render(str(cd), True, (0, 191, 255))
            screen.blit(text, (x + 54, y + 8))

    def on_ghost_collide(self, ghost) -> None:
        # 技能啟動時，碰到鬼魂自動吃掉
        if self.state == "active" and ghost.mode.current is not SPAWN:
            ghost.startFreight()
            ghost.visible = False
            # 這裡分數與顯示由主流程處理
            ghost.startSpawn()
            self.pacman.game.nodes.allowHomeAccess(ghost)
