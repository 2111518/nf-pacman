import pygame
from pygame.locals import *
import random # Import random for teleportation

from constants import *
from entity import Entity
from sprites import PacmanSprites
from nodes import NodeGroup # For type hinting
# Assuming Pellet class is in pellets.py, needed for type hint if strict
# from pellets import Pellet


class Pacman(Entity):
    def __init__(self, node) -> None:
        Entity.__init__(self, node) # Sets initial speed via self.setSpeed(100)
        self.name = PACMAN
        self.color = YELLOW
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanSprites(self)
        
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
        Entity.reset(self) # Resets speed to default (100) via self.setSpeed()
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()
        
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

    def update(self, dt: float) -> None:
        #print(f"Pacman.update START - Pos: {self.position}, Dir: {self.direction}, Alive: {self.alive}, Node: {self.node.position if self.node else 'None'}, Target: {self.target.position if self.target else 'None'}") # DEBUG LINE
        # Invisibility logic
        if self.is_invisible:
            self.invisibility_timer -= dt
            if self.invisibility_timer <= 0:
                self.is_invisible = False
                self.invisibility_timer = 0.0
                if self.image: # Ensure image is not None
                    self.image.set_alpha(self.default_alpha)
            else:
                if self.image: # Ensure image is not None
                    self.image.set_alpha(self.invisible_alpha)
        else: # Ensure alpha is reset if not invisible (e.g. after freight mode, etc.)
            if self.image and self.image.get_alpha() != self.default_alpha:
                 self.image.set_alpha(self.default_alpha)
        
        # Speed boost logic
        if self.is_boosted:
            self.speed_boost_timer -= dt
            if self.speed_boost_timer <= 0:
                self.is_boosted = False
                self.speed = self.base_speed_value # Revert to base speed
                self.speed_boost_timer = 0.0
                # print(f"Pacman speed boost ended. Speed reverted to {self.base_speed_value}")

        self.sprites.update(dt)
        #print(f"Pacman.update MID - Pos after sprite update: {self.position}, Dir: {self.direction}") # DEBUG LINE
        
        old_pos = self.position.copy() # DEBUG LINE
        self.position += self.directions[self.direction]*self.speed*dt
        #print(f"Pacman.update MID2 - Pos after movement: {self.position} (moved from {old_pos}), Dir: {self.direction}, Current Speed: {self.speed}, dt: {dt}") # DEBUG LINE
        #print(f"Pacman.update PRE-KEY-CHECK - Current self.direction: {self.direction}") # DEBUG LINE

        direction_from_key = self.getValidKey()
        #print(f"Pacman.update POST-KEY-CHECK - Current self.direction: {self.direction}, Key Press: {direction_from_key}") # DEBUG LINE
        
        is_overshot = self.overshotTarget()
        #print(f"Pacman.update OVERSHOT_CHECK: {is_overshot}, Target is None: {self.target is None}") # DEBUG LINE
        if self.target is not None: # Add detailed check for overshotTarget components
            vec1 = self.target.position - self.node.position
            vec2 = self.position - self.node.position
            node2Target_sq = vec1.magnitudeSquared()
            node2Self_sq = vec2.magnitudeSquared()
            #print(f"  Overshot details: node2Target_sq={node2Target_sq}, node2Self_sq={node2Self_sq}, node_pos={self.node.position}, target_pos={self.target.position}, self_pos={self.position}")

        if is_overshot: # Original: if self.overshotTarget():
            #print(f"Pacman.update OVERSHOT_TRUE_BLOCK - Current Dir Before Logic: {self.direction}, Player Key: {direction_from_key}") # DEBUG LINE
            self.node = self.target
            if self.node.neighbors[PORTAL] is not None:
                self.node = self.node.neighbors[PORTAL]
            
            # Attempt with player's key first
            self.target = self.getNewTarget(direction_from_key)
            if self.target is not self.node:
                self.direction = direction_from_key
            else:
                # Attempt with Pacman's current direction (before this block)
                # This 'self.direction' is the one Pacman had *before* trying the player_key.
                # We need to be careful if 'self.direction' was already STOP here.
                # Let's use a variable to store the direction Pacman was moving with *before* overshotTarget logic
                # However, the current code structure uses self.direction directly.
                # The print "Current Dir Before Logic" should tell us this.
                self.target = self.getNewTarget(self.direction)
                # If self.direction was already STOP, and player key was STOP,
                # and getNewTarget(STOP) fails, then this self.target will be self.node.

            if self.target is self.node: # Both attempts failed or led to no change
                self.direction = STOP
                
            self.setPosition()
            #print(f"Pacman.update OVERSHOT_TRUE_BLOCK - New Dir After Logic: {self.direction}") # DEBUG LINE
        elif self.oppositeDirection(direction_from_key): # Use direction_from_key here
            self.reverseDirection()
            #print(f"Pacman.update REVERSED_DIRECTION - New Dir: {self.direction}") # DEBUG LINE

    def getValidKey(self) -> int: # Return type is int based on constants
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

    def eatPellets(self, pelletList: list) -> 'Pellet | None': # Forward reference for Pellet
        for pellet in pelletList:
            if self.collideCheck(pellet):
                return pellet
        return None

    def collideGhost(self, ghost) -> bool: # Assuming ghost is of Ghost type
        if self.is_invisible:
            return False # No collision if invisible
        return self.collideCheck(ghost)

    def collideCheck(self, other) -> bool:
        d = self.position - other.position
        dSquared = d.magnitudeSquared()
        rSquared = (self.collideRadius + other.collideRadius)**2
        return dSquared <= rSquared

    def teleport(self, node_group: NodeGroup) -> None:
        """
        Teleports Pacman to a random valid node on the map.

        Args:
            node_group: The NodeGroup object containing all nodes in the current maze.
        """
        if node_group and node_group.nodesLUT:
            possible_nodes = list(node_group.nodesLUT.values())
            if possible_nodes:
                new_node = random.choice(possible_nodes)
                self.node = new_node
                self.target = new_node
                self.setPosition()
                print(f"Pacman teleported to node at {new_node.position}") # For debugging

    def activate_invisibility(self, duration: float) -> None:
        """Activates Pacman's invisibility for a given duration."""
        self.is_invisible = True
        self.invisibility_timer = duration
        self.invisibility_duration = duration # Store it if needed elsewhere
        if self.image: # Ensure image is not None
            self.image.set_alpha(self.invisible_alpha)
        print(f"Pacman invisible for {duration} seconds.") # For debugging

    def activate_speed_boost(self, factor: float, duration: float) -> None:
        """Activates Pacman's speed boost for a given duration."""
        # A new boost always resets the timer and applies the new factor to the original base_speed_value.
        self.is_boosted = True
        self.speed_boost_timer = duration
        self.speed = self.base_speed_value * factor # Boost from the base speed
        print(f"Pacman speed boosted to {self.speed} (factor {factor} on base {self.base_speed_value}) for {duration}s.")
