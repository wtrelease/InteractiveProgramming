import os, sys
import pygame
from pygame.locals import *
from helpers import *
import random
import math

if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')


BLUE = (0,0,255)
GREEN = (0, 255, 0)

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

def main(SCREEN_WIDTH, SCREEN_HEIGHT):
    """Initialize PyGame"""
    pygame.init()
    time = pygame.time.Clock()
    coin_time_past = 0
    rock_time_past = 0
    bird_time_past = 0

    pygame.font.init()
    font = pygame.font.Font(None, 36)

    """Create the Screen"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    """Create the background"""
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0,0,0))

    """Initialize Ground, Player, and Items """
    ground = Ground()

    player = Player()
    player_list = pygame.sprite.Group()
    player_list.add(player)

    coins_group = pygame.sprite.Group()
    coin = Coin()
    coins_group.add(coin)

    rocks_group = pygame.sprite.Group()
    rock = Rock()
    rocks_group.add(rock)
    rock_time = 1

    bird_list = pygame.sprite.Group()
    bird = Bird()
    bird_list.add(bird)

    """This is the Main Loop of the Game"""
    pygame.key.set_repeat(0, 30)

    Running = True
    while Running:
        """Keep track of time"""
        time.tick(60)
        frame_time = time.get_time()

        """Check for player inputs"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    player.jump(ground_height)
                if event.key == pygame.K_LEFT:
                    player.move_left(frame_time)
                elif event.key == pygame.K_RIGHT:
                    player.move_right(frame_time)
            elif player.change_x != 0:
                player.stop(frame_time)


        """Check for collisions with rocks and update health"""
        lstCols2 = pygame.sprite.spritecollide(player, rocks_group, player.rect.x < 64)
        if len(lstCols2) > 0:
            player.deflect()
            player.health = player.health - 1

        if player.health <= 0:
            Running = False

        """Check for collision with coins and update score"""
        lstCols = pygame.sprite.spritecollide(player, coins_group, True)
        player.coins = player.coins + len(lstCols)

        """Check for collision with birds and update health"""
        lstCols3 = pygame.sprite.spritecollide(player, bird_list, False)
        if len(lstCols3) > 0:
            player.deflect()
            player.health = player.health - 1

        """Advance the game"""
        ground_height = ground.advance(frame_time, player, coins_group, rocks_group, bird_list)
        ground_height_right = ground.ground_height[SCREEN_WIDTH]
        ground.build()

        if player.rect.y > ground_height:
            Running = False

        """Add new coins"""
        coin_time_past += frame_time / 1000
        if coin_time_past > 2 and ground_height_right < SCREEN_HEIGHT:
            coin_time_past = 0
            coins_group.add(Coin(ground_height_right))

        """Add new rock (s) """
        rock_threshold = 1/(1 + time.get_time()/500)
        rock_prob = random.random()
        rock_time_past += frame_time / 1000
        if rock_prob > rock_threshold  and rock_time_past > 1:
            rock_time_past = 0
            rocks_group.add(Rock(ground_height_right))

        """Add new bird"""
        bird_time_past += frame_time / 1000
        if bird_time_past > 3 and ground_height_right < SCREEN_HEIGHT:
            bird_time_past = 0
            bird_list.add(Bird())

        """Update the player """
        player.update(frame_time, ground_height)

        """Draw the game"""
        screen.blit(background, (0, 0))
        text = font.render("Score: %s" % player.coins, 1, (255, 0, 0))
        textpos = text.get_rect(centerx= SCREEN_WIDTH/2, centery = 50)
        screen.blit(text, textpos)
        fps = font.render("FPS: %.2f" % time.get_fps(), 1, (255, 0, 0))
        fpspos = fps.get_rect(centerx= 80, centery = 50)
        htext = font.render("Health: %s" % player.health, 1, (255, 0, 0))
        hpos = htext.get_rect(centerx = SCREEN_WIDTH - 80, centery = 50)
        screen.blit(htext, hpos)
        screen.blit(fps, fpspos)
        ground.draw(screen, GREEN)
        rocks_group.draw(screen)
        coins_group.draw(screen)
        bird_list.draw(screen)
        player_list.draw(screen)
        pygame.display.flip()

    score = 0
    screen.blit(background, (0, 0))
    text1 = font.render("GAME OVER", 2, (255, 0, 0))
    text2 = font.render("Score: %s" % player.coins, 2, (255, 0, 0))
    text1pos = text1.get_rect(centerx= SCREEN_WIDTH/2, centery = SCREEN_HEIGHT/2)
    text2pos = text2.get_rect(centerx= SCREEN_WIDTH/2, centery = SCREEN_HEIGHT/2 + 50)
    screen.blit(text1, text1pos)
    screen.blit(text2, text2pos)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
                if event.key == pygame.K_p:
                    main(SCREEN_WIDTH, SCREEN_HEIGHT)

class Player(pygame.sprite.Sprite):
    """Class representing the player"""
    def __init__(self):
        super().__init__()
        pygame.sprite.Sprite.__init__(self)
        self.image = (pygame.image.load('data/images/runningman.png'))
        self.rect = self.image.get_rect()
        self.acceleration_y = .007
        self.acceleration_x = .02
        self.jump_power = 1.5
        self.speed_limit = 4
        self.change_x = 0
        self.change_y = 0
        self.coins = 0
        self.jumping =  0
        self.health = 10

    """Update player location and speed from previous frame to current frame"""
    def update(self, t, ground_height):
        self.calc_grav(t, ground_height)

        self.rect.y += self.change_y * t
        self.rect.x += self.change_x * t

        if self.rect.x < 0:
            self.rect.x = 0
            self.change_x = 0
        elif self.rect.x + self.rect.width > SCREEN_WIDTH/1.2:
            self.rect.x = SCREEN_WIDTH/1.2 - self.rect.width
            self.change_x = 0

    """Determine change to players y velocity"""
    def calc_grav(self, t, ground_height):
        bottom = self.rect.y + self.rect.height
        if bottom < ground_height:
            self.change_y += self.acceleration_y * t

        if bottom >= ground_height - 10 and self.change_y >= 0:
            self.change_y = 0
            self.rect.y = ground_height - self.rect.height

    """Make the player jump by increasing y velocity"""
    def jump(self, height):
        bottom = self.rect.y + self.rect.height
        threshold = height - 10
        if bottom > threshold:
            self.change_y = -self.jump_power

    """Accelerate right"""
    def move_right(self, t):
        self.change_x += self.acceleration_x * t
        if self.change_x > self.speed_limit:
            self.change_x = self.speed_limit

    """Accelerate left"""
    def move_left(self, t):
         self.change_x -= self.acceleration_x * t
         if self.change_x < -self.speed_limit:
             self.change_x = -self.speed_limit

    """Stop the player"""
    def stop(self, t):
        self.change_x = 0

    """Deflect player off an object"""
    def deflect(self):
        if self.rect.x <= 64:
            self.rect.x = 0
            self.rect.y += 64
        else:
            self.rect.x -= 64
            self.change_x = -self.jump_power

        self.change_y = -self.jump_power

class Ground():
    """Class representing the ground """
    def __init__(self):
        self.speed = .5
        self.ground_min = .9 * SCREEN_HEIGHT
        self.ground_max = .45 * SCREEN_HEIGHT
        self.ground_height = [.75 * SCREEN_HEIGHT] * (2 * SCREEN_WIDTH)

    """Update ground from previous frame to current frame"""
    def advance(self, t, player, coin_list, rock_list, bird_list):
        start = player.rect.x
        end = start + player.rect.width
        height = min(self.ground_height[start:end])
        distance = int(t * self.speed)
        del self.ground_height[:distance]
        [coin.update(t, distance) for coin in coin_list]
        [rock.update(distance) for rock in rock_list]
        [bird.update(t, distance) for bird in bird_list]
        return height

    """Draw the ground"""
    def draw(self, screen, color):
        for x in range(1, SCREEN_WIDTH):
            y = int(self.ground_height[x-1])
            pygame.draw.line(screen, color, (x, y), (x, y+5))

    """Build additional ground"""
    def build(self, score = 0):
        if len(self.ground_height) > 1.1 * SCREEN_WIDTH:
            return

        pick = random.random()
        if pick > .9:
            self.gap()
        elif pick > .5:
            self.slope()
        else:
            self.flat()

    """Create section of sloped ground"""
    def slope(self):
        start = self.ground_height[-1]
        space_below = self.ground_min - start
        space_above = self.ground_max - start

        rise = random.randint(space_above, space_below)
        run = random.randint(abs(rise) * 2, SCREEN_WIDTH)
        slope = rise/ run

        for x in range(run):
            y = int(slope * x) + start
            self.ground_height.append(y)

    """Create flat section of ground"""
    def flat(self):
        length = random.randint(20, SCREEN_WIDTH/2)
        height = self.ground_height[-1]
        self.ground_height.extend([height] * length)

    """Create a gap in the ground"""
    def gap(self):
        length = 300
        height = self.ground_height[-1]
        self.ground_height.extend([SCREEN_HEIGHT] * length)
        self.ground_height.extend([height] * 100)

class Coin(pygame.sprite.Sprite):
    """ Class representing a coin"""
    def __init__(self, height = 0.75 * SCREEN_HEIGHT):
        pygame.sprite.Sprite.__init__(self)
        super().__init__()
        self.image = (pygame.image.load('data/images/coin.png'))
        self.rect = self.image.get_rect()
        self.ground = height
        self.rect.y = self.ground - self.rect.height
        self.rect.x = SCREEN_WIDTH - self.rect.width
        self.change_y = 0
        self.y_speed = .1* (random.random() + 1)

    """Update coin location and speed from previous frame to current frame"""
    def update(self, t, distance):
        self.rect.x -= distance
        self.rect.y += self.change_y * t
        if self.rect.y + self.rect.height >= self.ground:
            self.change_y = -self.y_speed
        elif self.rect.y <= self.ground - self.rect.height - .25 * SCREEN_HEIGHT:
            self.change_y = self.y_speed

class Rock(pygame.sprite.Sprite):
    """ Class representing a rock"""
    def __init__(self, height = .75 * SCREEN_HEIGHT):
        pygame.sprite.Sprite.__init__(self)
        super().__init__()
        self.image = (pygame.image.load('data/images/boulder.png'))
        self.rect = self.image.get_rect()
        self.rect.y = height- self.rect.height
        self.rect.x = SCREEN_WIDTH + self.rect.width/2
        self.ground = height

    """Update rock location across screen"""
    def update(self, distance):
        self.rect.x -= distance

class Bird(pygame.sprite.Sprite):
    """Class representing a bird"""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        super().__init__()
        self.image = (pygame.image.load('data/images/bird.png'))
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH - self.rect.width
        self.rect.y = .2 * SCREEN_HEIGHT
        self.change_y = .2
        self.speed = (random.random() + .5) * .3

    """Update birdlocation and speed from previous frame to current frame"""
    def update(self, t, distance):
        self.rect.x -= t * self.speed

        self.rect.y += self.change_y * t

        if self.rect.y <= 0.1 * SCREEN_HEIGHT:
            self.change_y = .2
        elif self.rect.y >= 0.3 * SCREEN_HEIGHT:
            self.change_y = -.2

if __name__ == "__main__":
    # MainWindow = RunRunMain()
    # MainWindow.MainLoop()
    main(SCREEN_WIDTH, SCREEN_HEIGHT)
