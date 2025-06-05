import sys

import pygame
from pygame.locals import *

from constants import *
from fruit import Fruit
from ghosts import GhostGroup
from mazedata import MazeData
from nodes import NodeGroup
from pacman import Pacman, PacmanGun, PacmanShield
from pauser import Pause
from pellets import PelletGroup
from sound import SoundController
from sprites import LifeSprites, MazeSprites
from text import TextGroup


class GameController:
    # Define game states
    START_MENU = "START_MENU"
    CHARACTER_SELECTING = "CHARACTER_SELECTING" # State while character_select() is active
    PLAYING = "PLAYING"
    PAUSED = "PAUSED" # If you want a dedicated pause state distinct from Pause object
    GAME_OVER = "GAME_OVER" # If you plan for a game over screen
    BACK_FROM_CHAR_SELECT = -99 # Special value for returning from character select

    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode(SCREENSIZE, 0, 32)
        self.font_credit = pygame.font.Font("PressStart2P-Regular.ttf", 10) # 初始化 credit 字型
        self.background = None
        self.background_norm = None
        self.background_flash = None
        self.clock = pygame.time.Clock()
        self.fruit = None
        self.level = 0
        self.lives = 5
        self.score = 0
        self.textgroup = TextGroup()
        self.lifesprites = LifeSprites(self.lives)
        self.flashBG = False
        self.flashTime = 0.2
        self.flashTimer = 0
        self.fruitCaptured = []
        self.fruitNode = None
        self.mazedata = MazeData()
        self.sound_controller = SoundController()
        self.selected_character = 0 # Default character, will be set by character_select
        self.extra_life_score_threshold: int = 10000
        self.extra_life_awarded: bool = False
        self.default_background_music: str = "pacman_beginning" # 設定預設背景音樂

        self.high_score: int = 0
        self.high_score_filepath: str = "highscore.txt"
        self.load_high_score() # 載入最高分
        self.textgroup.updateHighScore(self.high_score) # 更新顯示的最高分

        # Start Menu Setup
        self.game_state = GameController.START_MENU
        try:
            self.start_menu_image = pygame.image.load("start_menu.png").convert()
            self.start_menu_image = pygame.transform.scale(self.start_menu_image, SCREENSIZE)
        except pygame.error as e:
            print(f"Error loading start_menu.png: {e}")
            # Create a fallback surface if image loading fails
            self.start_menu_image = pygame.Surface(SCREENSIZE)
            self.start_menu_image.fill(BLACK)
            font = pygame.font.Font("PressStart2P-Regular.ttf", 20)
            text_surface = font.render("Start Menu Error", True, RED)
            text_rect = text_surface.get_rect(center=(SCREENWIDTH // 2, SCREENHEIGHT // 2))
            self.start_menu_image.blit(text_surface, text_rect)

        # Initialize Pause object here, assuming it's needed for PLAYING state
        self.pause = Pause(paused=True) # Start paused to show "Ready!" text initially

        # Start background music for the start menu
        self.sound_controller.play_background_music(self.default_background_music, loops=-1)

    def load_high_score(self) -> None:
        """Loads the high score from the highscore.txt file."""
        try:
            with open(self.high_score_filepath) as f:
                score_str = f.read().strip()
                if score_str.isdigit():
                    self.high_score = int(score_str)
                else:
                    print(f"Warning: Invalid content in {self.high_score_filepath}. Starting high score at 0.")
                    self.high_score = 0 # Reset if content is not a digit
        except FileNotFoundError:
            print(f"Info: {self.high_score_filepath} not found. Starting high score at 0.")
            self.high_score = 0 # File not found, start at 0
        except Exception as e:
            print(f"Error loading high score from {self.high_score_filepath}: {e}. Starting high score at 0.")
            self.high_score = 0 # Other errors, start at 0

    def save_high_score(self) -> None:
        """Saves the current high score to the highscore.txt file."""
        try:
            with open(self.high_score_filepath, "w") as f:
                f.write(str(self.high_score))
            print(f"High score ({self.high_score}) saved to {self.high_score_filepath}")
        except Exception as e:
            print(f"Error saving high score to {self.high_score_filepath}: {e}")

    def character_select(self) -> int:
        """顯示角色選擇畫面，回傳選擇的角色編號"""
        font_en = pygame.font.Font("PressStart2P-Regular.ttf", 16)  # 英文名稱字型（小一點）
        # font_credit = pygame.font.Font("PressStart2P-Regular.ttf", 10) # Credit 文字字型 - 改為在 __init__ 中初始化
        #font_zh = pygame.font.SysFont("Microsoft JhengHei", 20)  # 中文描述字型

        self.sound_controller.play_background_music("intermission", loops=-1) # 播放角色選擇背景音樂

        options = [
            {"name": "CLASSIC", "img": pygame.image.load("spritesheet_mspacman.png").convert(), "desc": "經典吃豆人"},
            {"name": "GUNNER", "img": pygame.image.load("pacman_gun.png").convert_alpha(), "desc": "Gun Pacman"},
            {"name": "SHIELD", "img": pygame.image.load("pacman_shield.png").convert_alpha(), "desc": "Shield Pacman"},
        ]
        # 縮放角色圖示
        options[0]["img"] = pygame.transform.scale(options[0]["img"].subsurface(pygame.Rect(8*TILEWIDTH, 0, 2*TILEWIDTH, 2*TILEHEIGHT)), (64, 64))
        options[1]["img"] = pygame.transform.scale(options[1]["img"], (64, 64))
        options[2]["img"] = pygame.transform.scale(options[2]["img"], (64, 64))
        selected = 0
        clock = pygame.time.Clock()
        while True:
            self.screen.fill(BLACK)
            title = font_en.render("Select Character", True, YELLOW)
            title2 = font_en.render(" (← → switch, Enter)", True, YELLOW)
            self.screen.blit(title, (SCREENWIDTH//2 - title.get_width()//2, 100))
            self.screen.blit(title2, (SCREENWIDTH//2 - title2.get_width()//2, 150))
            for i, opt in enumerate(options):
                x = SCREENWIDTH//2 - 160 + i*120
                y = 200
                border_color = YELLOW if i == selected else WHITE
                pygame.draw.rect(self.screen, border_color, (x-8, y-8, 80, 80), 4)
                self.screen.blit(opt["img"], (x, y))
                # 角色名稱（英文）
                name = font_en.render(opt["name"], True, WHITE)
                self.screen.blit(name, (x-10, y+70))
                # 角色描述（中文或英文）
                #desc = font_zh.render(opt["desc"], True, (200, 200, 200))
                #self.screen.blit(desc, (x-10, y+100))
            # 在角色選擇畫面也顯示 credit
            credit_text_surface = self.font_credit.render("by 404 not found", True, WHITE)
            credit_text_rect = credit_text_surface.get_rect(center=(SCREENWIDTH // 2, SCREENHEIGHT - 20))
            self.screen.blit(credit_text_surface, credit_text_rect)
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.save_high_score() # 遊戲退出前儲存最高分
                    pygame.quit() # Pygame quit should be called before sys.exit for proper cleanup
                    sys.exit()
                elif event.type == KEYDOWN:
                    if event.key == K_LEFT:
                        selected = (selected - 1) % len(options)
                        self.sound_controller.play_sound("munch_1") # 切換音效
                    elif event.key == K_RIGHT:
                        selected = (selected + 1) % len(options)
                        self.sound_controller.play_sound("munch_1") # 切換音效
                    elif event.key in (K_RETURN, K_KP_ENTER):
                        self.sound_controller.play_sound("credit") # 確認選擇音效
                        self.sound_controller.stop_music() # 停止角色選擇背景音樂
                        return selected
                    elif event.key == K_q: # Back to start menu
                        self.sound_controller.play_sound("munch_1") # Optional: back sound
                        self.sound_controller.stop_music() # Stop character selection music
                        return GameController.BACK_FROM_CHAR_SELECT
            clock.tick(30)

    def setBackground(self) -> None:
        self.background_norm = pygame.surface.Surface(SCREENSIZE).convert()
        self.background_norm.fill(BLACK)
        self.background_flash = pygame.surface.Surface(SCREENSIZE).convert()
        self.background_flash.fill(BLACK)
        self.background_norm = self.mazesprites.constructBackground(self.background_norm, self.level%5)
        self.background_flash = self.mazesprites.constructBackground(self.background_flash, 5)
        self.flashBG = False
        self.background = self.background_norm

    def startGame(self) -> None:
        self.sound_controller.play_sound("game_start") # 播放遊戲開始音效 (一次性)
        # 停止任何可能正在播放的背景音樂，讓 manage_background_sounds 來決定新的背景音
        self.sound_controller.stop_music()
        self.mazedata.loadMaze(self.level)
        self.mazesprites = MazeSprites(self.mazedata.obj.name+".txt", self.mazedata.obj.name+"_rotation.txt")
        self.setBackground()
        self.nodes = NodeGroup(self.mazedata.obj.name+".txt")
        self.mazedata.obj.setPortalPairs(self.nodes)
        self.mazedata.obj.connectHomeNodes(self.nodes)
        # 根據選擇建立角色
        if self.selected_character == 0:
            self.pacman = Pacman(self.nodes.getNodeFromTiles(*self.mazedata.obj.pacmanStart))
        elif self.selected_character == 1:
            self.pacman = PacmanGun(self.nodes.getNodeFromTiles(*self.mazedata.obj.pacmanStart))
        elif self.selected_character == 2:
            self.pacman = PacmanShield(self.nodes.getNodeFromTiles(*self.mazedata.obj.pacmanStart))
        self.pacman.game = self  # <--- 新增這行，讓pacman能取得game controller
        self.pellets = PelletGroup(self.mazedata.obj.name+".txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)
        self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(0, 3)))
        self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(4, 3)))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 0)))
        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.mazedata.obj.denyGhostsAccess(self.ghosts, self.nodes)

    def startGame_old(self) -> None:
        self.mazedata.loadMaze(self.level)#######
        self.mazesprites = MazeSprites("maze1.txt", "maze1_rotation.txt")
        self.setBackground()
        self.nodes = NodeGroup("maze1.txt")
        self.nodes.setPortalPair((0,17), (27,17))
        homekey = self.nodes.createHomeNodes(11.5, 14)
        self.nodes.connectHomeNodes(homekey, (12,14), LEFT)
        self.nodes.connectHomeNodes(homekey, (15,14), RIGHT)
        self.pacman = Pacman(self.nodes.getNodeFromTiles(15, 26))
        self.pellets = PelletGroup("maze1.txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)
        self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 0+14))
        self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))
        self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(0+11.5, 3+14))
        self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(4+11.5, 3+14))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, LEFT, self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, RIGHT, self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.nodes.denyAccessList(12, 14, UP, self.ghosts)
        self.nodes.denyAccessList(15, 14, UP, self.ghosts)
        self.nodes.denyAccessList(12, 26, UP, self.ghosts)
        self.nodes.denyAccessList(15, 26, UP, self.ghosts)



    def update(self) -> None:
        dt = self.clock.tick(30) / 1250.0 # Ensure dt is calculated regardless of state for clock.tick
        events = pygame.event.get() # Get events once per frame

        self.check_general_events(events) # Pass events

        if self.game_state == GameController.START_MENU:
            self.update_start_menu(events) # Handles K_SPACE to go to CHARACTER_SELECTING
        elif self.game_state == GameController.CHARACTER_SELECTING:
            # This state is now triggered from START_MENU (K_SPACE) or PLAYING (K_q)
            # Call character_select and handle its outcome directly here.
            selection_result = self.character_select()

            if selection_result == GameController.BACK_FROM_CHAR_SELECT:
                self.game_state = GameController.START_MENU
                self.sound_controller.play_background_music(self.default_background_music, loops=-1)
            else:
                self.selected_character = selection_result
                self.sound_controller.stop_music() # Ensure character select music is stopped
                self.game_state = GameController.PLAYING
                self.pause.setPause(should_be_paused=True, pauseTime=None) # Set to be paused for "Ready!"
                self.startGame()
                self.textgroup.updateLevel(self.level)
                self.textgroup.showText(READYTXT)

        elif self.game_state == GameController.PLAYING:
            self.textgroup.update(dt) # Keep text updates if they are general (like score)
            self.pellets.update(dt)
            if not self.pause.paused:
                self.ghosts.update(dt)
                if self.fruit is not None:
                    self.fruit.update(dt)
                self.checkPelletEvents()
                self.checkGhostEvents()
                self.checkFruitEvents()

            if self.pacman.alive:
                if not self.pause.paused:
                    self.pacman.update(dt)
            else:
                # This handles pacman death animation
                self.pacman.update(dt)

            self.manage_background_sounds() # Manage background sounds based on game situation

            if self.flashBG:
                self.flashTimer += dt
                if self.flashTimer >= self.flashTime:
                    self.flashTimer = 0
                    if self.background == self.background_norm:
                        self.background = self.background_flash
                    else:
                        self.background = self.background_norm

            # Specific PLAYING state events (like pausing the game)
            self.check_playing_events(events) # Pass events

            afterPauseMethod = self.pause.update(dt) # Pause object update
            if afterPauseMethod is not None:
                afterPauseMethod()
        # Add other game states like GAME_OVER if needed
        # elif self.game_state == GameController.GAME_OVER:
        #     self.update_game_over()


        self.render() # Call render at the end of update

    def update_start_menu(self, events: list[pygame.event.Event]) -> None:
        """Handles logic for the start menu state."""
        for event in events:
            if event.type == QUIT:
                self.quit_game()
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    self.sound_controller.play_sound("credit")
                    self.game_state = GameController.CHARACTER_SELECTING
                    # No longer call character_select directly here, update() will handle it.
                    # self.sound_controller.stop_music() # Music stop handled when CHARACTER_SELECTING starts or ends
                    return # Exit event loop for start menu, next update cycle will handle CHARACTER_SELECTING
                if event.key == K_q and self.game_state == GameController.START_MENU:
                    self.quit_game()

    def check_general_events(self, events: list[pygame.event.Event]) -> None:
        """Handles events that should be checked in all game states, like QUIT."""
        for event in events: # Iterate over passed events
            if event.type == QUIT:
                self.quit_game()

    def check_playing_events(self, events: list[pygame.event.Event]) -> None:
        """Handles events specific to the PLAYING state, e.g., pausing."""
        for event in events: # Iterate over passed events
            if event.type == QUIT:
                self.quit_game()
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    ready_text_obj = self.textgroup.alltext.get(READYTXT)
                    if self.pause.paused and ready_text_obj and ready_text_obj.visible:
                        self.pause.setPause(should_be_paused=False)  # Unpause to start the game
                        if ready_text_obj:
                            ready_text_obj.visible = False
                    elif self.pacman.alive:
                        current_pause_state = self.pause.paused
                        self.pause.setPause(should_be_paused=not current_pause_state)
                        if self.pause.paused:
                            self.textgroup.showText(PAUSETXT)
                        else:
                            pause_text_obj = self.textgroup.alltext.get(PAUSETXT)
                            if pause_text_obj:
                                pause_text_obj.visible = False
                            self.showEntities()

                elif event.key == K_q: # Back to character selection from playing state
                    self.sound_controller.play_sound("munch_1")
                    self.sound_controller.stop_music()
                    self.textgroup.hideText()
                    if self.pause.paused:
                        self.pause.setPause(should_be_paused=False) # Explicitly unpause before leaving screen
                        self.showEntities()

                    self.game_state = GameController.CHARACTER_SELECTING
                    return

                #技能啟動與射擊
                elif hasattr(self.pacman, "ability"):
                    if event.key == pygame.K_j:
                        # 只有有shoot方法的才呼叫shoot，否則只呼叫activate
                        if hasattr(self.pacman.ability, "shoot") and self.pacman.ability.state == "active":
                            self.pacman.ability.shoot()
                        elif self.pacman.ability.state == "ready":
                            self.pacman.ability.activate()
                    elif event.key == pygame.K_k and hasattr(self.pacman, "secondary_ability"):
                         if self.pacman.secondary_ability.state == "ready":
                            self.pacman.secondary_ability.activate()
                         elif self.pacman.secondary_ability.state == "active" and hasattr(self.pacman.secondary_ability, "shoot"):
                             self.pacman.secondary_ability.shoot()


    def quit_game(self) -> None:
        """Handles quitting the game cleanly."""
        self.save_high_score()
        pygame.quit()
        sys.exit()

    def checkEvents(self) -> None: # This method is now split into check_general_events and check_playing_events
        pass # Keep the original checkEvents if it's called from somewhere else, or remove if fully replaced.
             # For now, making it a no-op to avoid breaking calls if they exist.
             # Better to refactor calls to use the new specific event handlers.

    def checkPelletEvents(self) -> None:
        pellet = self.pacman.eatPellets(self.pellets.pelletList)
        if pellet:
            self.pellets.numEaten += 1
            self.updateScore(pellet.points)

            if pellet.name == PELLET: # 普通豆子
                self.sound_controller.play_sound("munch_1") # 播放咀嚼音效
            elif pellet.name == TELEPORTPELLET:
                self.pacman.teleport(self.nodes)
            elif pellet.name == POWERPELLET:
                self.ghosts.startFreight()
                self.sound_controller.play_sound("power_pellet") # 播放吃到大力丸音效
            elif pellet.name == INVISIBILITYPELLET:
                invisibility_duration = 5.0
                self.pacman.activate_invisibility(invisibility_duration)
            elif pellet.name == SPEEDBOOSTPELLET:
                boost_factor = 1.5
                boost_duration = 8.0
                self.pacman.activate_speed_boost(boost_factor, boost_duration)
            elif pellet.name == SCOREMAGNETPELLET:
                magnet_radius_squared = (TILEWIDTH * 4)**2 # Radius of 4 tiles
                pellets_absorbed_in_event = 0

                # Iterate over a copy of the pellet list for safe removal
                for other_pellet in list(self.pellets.pelletList):
                    if other_pellet is pellet: # Don't absorb the magnet pellet itself (it's handled by the main removal)
                        continue

                    # Absorb only normal pellets and power pellets
                    if other_pellet.name in (PELLET, POWERPELLET):
                        if other_pellet.visible: # Check if it's an active pellet
                            dist_sq = (self.pacman.position - other_pellet.position).magnitudeSquared()
                            if dist_sq <= magnet_radius_squared:
                                self.updateScore(other_pellet.points)
                                self.pellets.numEaten += 1 # Increment for game progression logic
                                pellets_absorbed_in_event +=1
                                self.pellets.pelletList.remove(other_pellet)
                                if other_pellet.name == POWERPELLET and other_pellet in self.pellets.powerpellets:
                                    self.pellets.powerpellets.remove(other_pellet)
                # if pellets_absorbed_in_event > 0:
                #     print(f"ScoreMagnet absorbed {pellets_absorbed_in_event} pellets.")
            # Standard game logic dependent on numEaten (e.g., releasing ghosts)

            # This will now correctly account for pellets eaten by the magnet

            if self.pellets.numEaten == 30:
                self.ghosts.inky.startNode.allowAccess(RIGHT, self.ghosts.inky)
            if self.pellets.numEaten == 70:
                self.ghosts.clyde.startNode.allowAccess(LEFT, self.ghosts.clyde)
            #這是原本的
            # self.pellets.pelletList.remove(pellet)
            # if pellet.name == POWERPELLET:
            #     self.ghosts.startFreight()
            #修改後
            # Remove the originally eaten pellet (teleport, power, invisibility, speed, or magnet itself)
            if pellet in self.pellets.pelletList: # It might have been absorbed if it was another magnet (unlikely setup)
                self.pellets.pelletList.remove(pellet)
            if pellet.name == POWERPELLET and pellet in self.pellets.powerpellets:
                 self.pellets.powerpellets.remove(pellet) # Ensure the main power pellet is removed if it was one
            if self.pellets.isEmpty():
                self.sound_controller.play_sound("pacman_extrapac") # 立即播放通關音效
                self.flashBG = True
                self.hideEntities()
                self.pause.setPause(should_be_paused=True, pauseTime=3, func=self.nextLevel)

    def checkGhostEvents(self) -> None:
        for ghost in self.ghosts:
            # 子彈碰撞
            if hasattr(self.pacman, "ability") and hasattr(self.pacman.ability, "bullets"):
                for bullet in self.pacman.ability.bullets:
                    if ghost.visible and bullet.rect.colliderect(ghost.image.get_rect(center=ghost.position.asInt())) and ghost.mode.current is not SPAWN:
                        self.sound_controller.play_sound("eat_ghost") # 假設子彈擊中鬼效果類似吃鬼
                        ghost.startFreight()  # 先進入可吃狀態
                        ghost.visible = False
                        self.updateScore(ghost.points)
                        self.textgroup.addText(str(ghost.points), WHITE, ghost.position.x, ghost.position.y, 8, time=1)
                        self.ghosts.updatePoints()
                        self.pause.setPause(should_be_paused=True, pauseTime=1, func=self.showEntities)
                        ghost.startSpawn()
                        self.nodes.allowHomeAccess(ghost)
                        bullet.active = False
            # 盾牌技能碰撞（只有技能啟動時才特殊處理）
            if hasattr(self.pacman, "ability") and hasattr(self.pacman.ability, "on_ghost_collide") and self.pacman.ability.state == "active":
                if self.pacman.collideGhost(ghost) and ghost.mode.current is not SPAWN:
                    self.pacman.ability.on_ghost_collide(ghost)
                    self.updateScore(ghost.points)
                    self.textgroup.addText(str(ghost.points), WHITE, ghost.position.x, ghost.position.y, 8, time=1)
                    self.ghosts.updatePoints()
                    self.pause.setPause(should_be_paused=True, pauseTime=1, func=self.showEntities)
                    continue  # 技能啟動時不再進行下方一般碰撞判斷
            # 一般Pacman碰撞（包含PacmanShield未開技能時）
            if self.pacman.collideGhost(ghost):
                if ghost.mode.current is FREIGHT:
                    self.sound_controller.play_sound("eat_ghost") # 播放吃到鬼音效
                    self.pacman.visible = False
                    ghost.visible = False
                    self.updateScore(ghost.points)
                    self.textgroup.addText(str(ghost.points), WHITE, ghost.position.x, ghost.position.y, 8, time=1)
                    self.ghosts.updatePoints()
                    self.pause.setPause(should_be_paused=True, pauseTime=1, func=self.showEntities)
                    ghost.startSpawn()
                    self.nodes.allowHomeAccess(ghost)
                elif ghost.mode.current is not SPAWN:
                    if self.pacman.alive:
                        self.lives -=  1
                        self.lifesprites.removeImage()
                        self.pacman.die() # pacman.die() 內部可能有動畫計時器
                        self.sound_controller.stop_music() # Pacman 死亡，停止所有背景音樂
                        self.sound_controller.play_sound("pacman_death") # 播放 Pacman 死亡音效 (一次性)
                        self.ghosts.hide()
                        if self.lives <= 0:
                            self.textgroup.showText(GAMEOVERTXT)
                            self.save_high_score() # 遊戲結束時儲存最高分
                            # 遊戲結束，準備重新開始，此時應已停止背景音樂
                            self.pause.setPause(should_be_paused=True, pauseTime=3, func=self.restartGame)
                        else:
                            # 僅重置關卡，死亡音樂播放後，manage_background_sounds 會在下一幀處理警笛
                            self.pause.setPause(should_be_paused=True, pauseTime=3, func=self.resetLevel)

    def checkFruitEvents(self) -> None:
        if self.pellets.numEaten in {50, 140} and self.fruit is None:
            self.fruit = Fruit(self.nodes.getNodeFromTiles(9, 20), self.level)
        if self.fruit is not None:
            if self.pacman.collideCheck(self.fruit):
                self.sound_controller.play_sound("eat_fruit") # 播放吃到水果音效
                self.updateScore(self.fruit.points)
                self.textgroup.addText(str(self.fruit.points), WHITE, self.fruit.position.x, self.fruit.position.y, 8, time=1)
                fruitCaptured = False
                for fruit in self.fruitCaptured:
                    if fruit.get_offset() == self.fruit.image.get_offset():
                        fruitCaptured = True
                        break
                if not fruitCaptured:
                    self.fruitCaptured.append(self.fruit.image)
                self.fruit = None
            elif self.fruit.destroy:
                self.fruit = None

    def showEntities(self) -> None:
        self.pacman.visible = True
        self.ghosts.show()

    def hideEntities(self) -> None:
        self.pacman.visible = False
        self.ghosts.hide()

    def nextLevel(self) -> None:
        self.sound_controller.play_sound("pacman_intermission") # 播放調整後的過關音效 (一次性)
        self.sound_controller.stop_music() # 停止舊的背景音樂，讓 manage_background_sounds 在下一關開始時選擇新的
        self.showEntities()
        self.level += 1
        self.pause.paused = True
        self.startGame()
        self.textgroup.updateLevel(self.level)

    def restartGame(self) -> None:
        # game_start 音效會在 startGame() 中播放
        # 在重新開始遊戲前，確保之前的分數（可能是新的最高分）已被保存
        # self.save_high_score() # 移至 GAMEOVERTXT 處保存，避免每次 resetLevel 都保存
        self.lives = 5
        self.level = 0
        self.pause.paused = True
        self.fruit = None
        self.sound_controller.stop_music() # 停止任何音樂，startGame 會處理開始音樂和後續的背景音
        self.startGame()
        self.score = 0
        self.textgroup.updateScore(self.score)
        self.textgroup.updateLevel(self.level)
        self.textgroup.showText(READYTXT)
        self.lifesprites.resetLives(self.lives)
        self.fruitCaptured = []
        self.extra_life_awarded = False # 重置額外生命旗標

    def resetLevel(self) -> None:
        self.pause.paused = True
        self.pacman.reset()
        self.ghosts.reset()
        self.fruit = None
        self.textgroup.showText(READYTXT)
        # Pacman 重生，背景音樂（警笛）應恢復，manage_background_sounds() 會處理
        # 如果之前有 stop_music(), 這裡不需要特別再 stop/start，交給 update 中的 manage_background_sounds

    def updateScore(self, points) -> None:
        self.score += points
        self.textgroup.updateScore(self.score)
        if self.score > self.high_score:
            self.high_score = self.score
            self.textgroup.updateHighScore(self.high_score)
            # 不需要在此處立即 save_high_score()，等到遊戲結束或退出時再統一儲存

        # 檢查是否達到獲得額外生命的分數門檻
        if not self.extra_life_awarded and self.score >= self.extra_life_score_threshold:
            self.lives += 1
            self.lifesprites.addImage() # 假設 LifeSprites 有此方法來增加一個生命圖示
            self.sound_controller.play_sound("extend") # 播放獲得額外生命音效
            self.extra_life_awarded = True
            # 如果希望在更高分數再次獎勵生命，可以擴展此邏輯
            # 例如： self.extra_life_score_threshold += 10000 或設定多個門檻

    def render(self) -> None:
        if self.game_state == GameController.START_MENU:
            self.render_start_menu()
        elif self.game_state == GameController.CHARACTER_SELECTING:
            # character_select() handles its own rendering loop, so screen is updated there.
            # No explicit render call needed here for this state.
            pass
        elif self.game_state == GameController.PLAYING or self.game_state == GameController.PAUSED: # Assuming PAUSED might have similar render
            self.screen.blit(self.background, (0, 0))
            #self.nodes.render(self.screen)
            self.pellets.render(self.screen)
            if self.fruit is not None:
                self.fruit.render(self.screen)
            self.pacman.render(self.screen)
            self.ghosts.render(self.screen)
            self.textgroup.render(self.screen)

            for i in range(len(self.lifesprites.images)):
                x = self.lifesprites.images[i].get_width() * i
                y = SCREENHEIGHT - self.lifesprites.images[i].get_height()
                self.screen.blit(self.lifesprites.images[i], (x, y))

            for i in range(len(self.fruitCaptured)):
                x = SCREENWIDTH - self.fruitCaptured[i].get_width() * (i+1)
                y = SCREENHEIGHT - self.fruitCaptured[i].get_height()
                self.screen.blit(self.fruitCaptured[i], (x, y))

            # 顯示技能圖示與倒數
            if hasattr(self.pacman, "ability"):
                self.pacman.ability.render(self.screen)

            pygame.display.update() # This should be the only display.update() call in the main loop ideally

    def render_start_menu(self) -> None:
        """Renders the start menu."""
        self.screen.blit(self.start_menu_image, (0, 0))
        # Optionally, add any text or animations to the start menu here
        # Example: self.textgroup.render(self.screen) if you have start menu text
        pygame.display.update() # Start menu has its own update for now

    def manage_background_sounds(self) -> None:
        """Manages playing continuous background sounds like retreating sounds or default background music."""
        # Do not play sounds if in start menu or character selection, as they have their own music.
        if self.game_state == GameController.START_MENU or self.game_state == GameController.CHARACTER_SELECTING:
            return

        if not self.pacman.alive or self.pause.paused:
            # 如果Pacman死亡、遊戲暫停，或者在某些特殊過場（如果有的話），則可能停止背景音
            # 但Pacman死亡時，死亡音效播放後，若遊戲未結束（resetLevel），則背景音樂應恢復
            # GAMEOVERTXT 顯示時，背景音應該是停止的，直到 restartGame
            if not self.pacman.alive and self.lives > 0: # Pacman 死亡但遊戲未結束 (等待resetLevel)
                 pass # 背景音樂已在 die() 事件中停止，等待 resetLevel 後恢復
            elif self.textgroup.alltext[GAMEOVERTXT].visible:
                 self.sound_controller.stop_music()
            # elif self.pause.paused and not self.textgroup.alltext[PAUSETXT].visible: # 遊戲內部邏輯暫停（如過關）
                 # self.sound_controller.stop_music() # 可能需要，取決於是否希望過關音效後立即停止所有聲音
            return

        if self.ghosts.is_any_ghost_frightened():
            self.sound_controller.play_background_music("retreating", loops=-1)
        else:
            # 播放預設的背景音樂
            self.sound_controller.play_background_music(self.default_background_music, loops=-1)


if __name__ == "__main__":
    game = GameController()
    # game.startGame() # startGame is now called after character selection
    while True:
        game.update()



