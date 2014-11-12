#!/usr/bin/env python2
# vim: set fileencoding=utf-8

import os.path
import sys
import webbrowser

from copy import copy
from math import ceil
from random import randint

import pixelperfect
import pygame

IMG_PATH = "img2"
EV_OOB = pygame.USEREVENT + 1

def irnd(n):
    """Rounds `n' and returns an integer."""
    return int(round(n))

def load_image(path):
    """Loads an image and returns a pygame.Surface."""
    img = pygame.image.load(path)
    img = img.convert_alpha()
    return img

class Animation(object):
    def __init__(self, imgs, ticks):
        """
        Inititalizes the Animation instance. Arguments:
        imgs  = list of `pygame.Surface`s of the frames. Need to be same
                size
        ticks = How often a frame gets rendered before switching to the
                next image
        """
        self.imgs = imgs
        self.img = 0
        self.ticks = ticks
        self.tick = self.ticks

    def render(self, surface, *args):
        """Renders the image onto `surface`."""
        surface.blit(self.imgs[self.img], *args)
        self.tick -= 1
        if self.tick == 0:
            print self.img
            self.img = (self.img + 1) % len(self.imgs)
            self.tick = self.ticks

    def get_rect(self):
        return self.imgs[0].get_rect()

class Image(object):
    def __init__(self, img):
        """Initializes the Image instance with `img`."""
        self.img = img

    def render(self, surface, *args):
        """
        Renders the Image onto `surface`.
        """
        surface.blit(self.img, *args)

    def get_rect(self):
        """Return pygame.Rect of the Image."""
        return self.img.get_rect()


class Entity(object):
    def __init__(self, bounds, game_speed):
        """
        Initializes the Entity instance. Arguments:
        bounds     = pygame.Rect of the bounds to move in
        game_speed = Game speed
        """
        self.bounds = bounds
        self.game_speed = game_speed

    def _up(self, amount):
        """Moves the Entity up."""
        if self.bounds.top > self.rect.top - amount:
            self.rect.y = 0
        else:
            self.rect.move_ip(0, -amount)

    def _down(self, amount):
        """Moves the Entity down."""
        if self.bounds.bottom < self.rect.bottom + amount:
            self.rect.y = self.bounds.bottom
        else:
            self.rect.move_ip(0, amount)

    def _left(self, amount):
        """Moves the Entity left."""
        if self.bounds.left > self.rect.left - amount:
            self.rect.x = 0
        else:
            self.rect.move_ip(-amount, 0)

    def _right(self, amount):
        """Moves the Entity right."""
        if self.bounds.right < self.rect.right + amount:
            self.rect.x = self.bounds.right
        else:
            self.rect.move_ip(amount, 0)

class Player(Entity):

    def __init__(self, img, *args):
        """
        Initializes the Player instance. Arguments:
        img        = pygame.Surface of the Player
        bounds     = pygame.Rect of the bounds to move in
        game_speed = Speed of the street
        """
        super(Player, self).__init__(*args)
        self.img = img
        self.rect = self.img.get_rect()
        self.hitmask = pixelperfect.get_alpha_hitmask(self.img, self.rect)
        self.speed = self.bounds.height / 40

    def up(self):
        """Moves the Player up."""
        super(Player, self)._up(self.speed)

    def down(self):
        """Moves the Player down."""
        self._down(self.speed)

    def accelerate(self):
        """Accelerates the Player."""
        self._right(self.speed)

    def decelerate(self):
        """Decelerates the Player."""
        self._left(self.speed)

    def render(self, surface):
        """Blits the Player on `surface`."""
        surface.blit(self.img, self.rect)

class Enemy(Entity):
    def __init__(self, move_type, img, *args):
        """
        Initializes the Enemy instance. Arguments:
        move_type  = Movement type of the Enemy. See Enemy.move
        img        = pygame.Surface of the Enemy
        bounds     = pygame.Rect of the bounds to move in
        game_speed = Speed of the street
        """
        super(Enemy, self).__init__(*args)
        self.move_type = move_type
        self.img = img
        self.rect = img.get_rect()
        self.hitmask = pixelperfect.get_alpha_hitmask(self.img, self.rect)

        if move_type < 2:
            x = self.bounds.right
            y = randint(self.bounds.top, self.bounds.bottom)
        elif move_type < 4:
            x = randint(self.bounds.right / 2, self.bounds.right)
            if move_type == 2: y = self.bounds.bottom
            else: y = self.bounds.top
        else:
            print "MOVE_TYPE > 3"

        self.rect.move_ip(x, y)

    def move(self):
        """
        Moves the Enemy according to its move_type. The movements are:
        0 = Moves to the left at Game.speed
        1 = Moves to the left at half Game.speed
        2 = Walks to the left and up
        3 = Walks to the left and down
        
        6 = moves up
        7 = moves down
        8 = moves up to the player
        9 = moves down to the player
        10 = moves left and meanwhile up and down
        11 = moves left and meanwhile down and up
        """
        if self.move_type == 0:
            self.rect.move_ip(-self.game_speed, 0)
        elif self.move_type == 1:
            self.rect.move_ip(-self.game_speed / 2, 0)
        elif self.move_type == 2:
            self.rect.move_ip(-self.game_speed, -self.game_speed)
        elif self.move_type == 3:
            self.rect.move_ip(-self.game_speed, self.game_speed)
        else:
            print "MOVE_TYPE > 3"
        if not self.rect.colliderect(self.bounds):
            pygame.event.post(pygame.event.Event(
                EV_OOB, instance=self
            ))

    def render(self, surface):
        """Blits the Enemy on `surface`."""
        surface.blit(self.img, self.rect)

class Game(object):
    def __init__(self, width=1200, height=800, player="email.png", virus=(
                 "virus_{}.png", (1, 2, 3, 4)), street="matrix.png",
                 game_over="game_over.png"):
        """
        Initializes the Game instance. Arguments:
        width      = window width
        height     = window height
        player     = name of image file for player
        virus      = name(s) of image files in format (fmt, (numbers))
        street     = name of image file for street (matrix)
        """
        # Initialisierung
        self.width = width
        self.height = height

        self.bounds = pygame.Rect(0, 0, self.width, self.height)

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("E-Mail")
        pygame.mouse.set_visible(1)

        pygame.font.init()

        self.player_img = load_image(os.path.join(IMG_PATH, player))
        scale = self.player_img.get_height() * 10.0 / self.height
        self.player_img = pygame.transform.scale(
                self.player_img, (irnd(self.player_img.get_width() / scale),
                irnd(self.player_img.get_height() / scale))
        )
        self.virus_img = [load_image(os.path.join(IMG_PATH, virus[0].format(i)))
                      for i in virus[1]]
        self.virus_img = [
            pygame.transform.scale(i, (irnd(i.get_width() / (i.get_height() *
                5.0 / self.height)), irnd(i.get_height() / (i.get_height() *
                5.0 / self.height)))) for i in self.virus_img
        ]
        print(self.virus_img)
        self.street_img = load_image(os.path.join(IMG_PATH, street))

        self.game_over_img = load_image(os.path.join(IMG_PATH, game_over))
        self.game_over_img = pygame.transform.scale(
                self.game_over_img, (self.width, self.height)
        )

        self.speed = 10

        self.player = Player(self.player_img, self.bounds, self.speed)

        self.enemies = []
        self.next_enemy = 60
        self.next_enemy_max = 60
        self.next_enemy_min = 30

        # Tastendruck wiederholt senden, falls nicht losgelassen
        pygame.key.set_repeat(1, 30)
        self.clock = pygame.time.Clock()
        self.running = False

        self.score = 0
        self.score_font = pygame.font.match_font("couriernew", bold=True)
        self.score_font = pygame.font.Font(self.score_font, 70)

    #def set_street_img(self, path):
        #img = pygame.image.load(path)
        #img = img.convert()
        #self.street_img = img

        #self.scaled_street = self.scale_street_img()

    #def scale_street_img(self):
        #width = self.street_img.get_width()
        #height = self.street_img.get_height()
        #scale = height // self.height
        #img = pygame.transform.scale(self.street_img,
                #(width // scale, self.height))
        #return img

    def get_street_img(self, hpos, vpos):
        surf = pygame.Surface((self.width, self.height))
        for x in range(-hpos, self.width, self.street_img.get_width()):
            for y in range(-vpos, self.height, self.street_img.get_height()):
                surf.blit(self.street_img, (x, y))
        return surf

    #def set_player_img(self, path):
        #img = pygame.image.load(path)
        #img = img.convert_alpha()
        #scale = img.get_height() / (self.height / 5.0)
        #img = pygame.transform.scale(img, (int(round(img.get_width() / scale)),
            #int(round(img.get_height() / scale))))
        #self.player.set_img(Image(img))

    #def set_deer_img(self, paths):
        #imgs = [pygame.image.load(path).convert_alpha() for path in paths]
        #scale = imgs[0].get_height() / (self.height / 5.0)
        #imgs = [pygame.transform.scale(img, (int(round(img.get_width() / scale)),
            #int(round(img.get_height() / scale)))) for img in imgs]
        #self.deer_anim = Animation(imgs, 3)
        #self.deer_height = self.deer_anim.get_rect().height
        #for deer in self.deer:
            #deer.set_img(copy(self.deer_anim))

    def spawn_enemy(self):
        if randint(0, 1):
            # Laters
            #if self.speed < 20:
                #move_type = randint(0, 2)
            #elif self.speed < 30:
                #move_type = randint(0, 4)
            #else:
                #move_type = randint(0, 7)
            i = randint(0, 3)
            self.enemies.append(Enemy(i, self.virus_img[i], self.bounds, self.speed))

    def run(self):
        self.running = True
        pos = 0
        tick = 0
        while self.running:
            self.clock.tick(30)
            tick += 1

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    sys.exit()
                elif ev.type == EV_OOB:
                    self.enemies.remove(ev.dict["instance"])
                    self.score += 10

            keys = pygame.key.get_pressed()

            if keys[pygame.K_RIGHT]:
                self.player.accelerate()
            else:
                self.player.decelerate()
            if keys[pygame.K_LEFT]:
                self.player.decelerate()
            if keys[pygame.K_UP]:
                self.player.up()
            if keys[pygame.K_DOWN]:
                self.player.down()
            if keys[pygame.K_ESCAPE]:
                sys.exit()

            for enemy in self.enemies:
                enemy.move()
                if pixelperfect.check_collision(self.player, enemy):
                    print "GAME OVER"
                    self.running = False

            if tick % 30 == 0:
                if self.next_enemy_max > 30:
                    self.next_enemy_max -= 1
                if self.next_enemy_min > 15:
                    self.next_enemy_min -= 1
            if tick % 75 == 0 and self.speed < 35:
                self.speed += 1
                for enemy in self.enemies:
                    enemy.game_speed = self.speed
                self.player.game_speed = self.speed

            if self.next_enemy == 0:
                self.spawn_enemy()
                self.next_enemy = randint(self.next_enemy_min, self.next_enemy_max)
            else:
                self.next_enemy -= 1

            for enemy in self.enemies:
                enemy.move

            pos += self.speed
            pos %= self.street_img.get_height()
            self.screen.blit(self.get_street_img(0, pos), (0, 0))

            score = self.score_font.render("Points: {}".format(self.score),
                                           True, (255, 255, 255))
            self.screen.blit(score, (0, 0))

            self.player.render(self.screen)

            for enemy in self.enemies:
                enemy.render(self.screen)
            #for deer in self.deer:
                #deer.render(self.screen)

            pygame.display.flip()

        self.game_over()

    def game_over(self):
        """Displays the Game over screen."""
        print self.score
        while True:
            self.clock.tick(30)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    webbrowser.open_new_tab("http://goo.gl/yuXawT")
            
            if pygame.key.get_pressed()[pygame.K_ESCAPE]:
                sys.exit()

            self.screen.blit(self.game_over_img, (0, 0))
            score = self.score_font.render("Points: {}".format(self.score),
                                           True, (255, 255, 255))
            self.screen.blit(score, (0, 0))
            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()
