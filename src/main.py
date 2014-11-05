#!/usr/bin/env python2
# vim: set fileencoding=utf-8

import os.path
import sys

from math import ceil
from random import randint

import pygame

class Entity(object):
    def __init__(self, x, y, street, game_speed):
        """
        Initializes the Entity instance. Arguments:
        x          = The initial x coordinate of the Entity
        y          = The initial y coordinate of the Entity
        street     = pygame.Rect of the Street
        game_speed = Speed of the street
        """
        self.x = x
        self.y = y
        self.street = street
        self.game_speed = game_speed

class Player(Entity):

    def __init__(self, *args):
        """
        Initializes the Player instance. Arguments:
        x          = The initial x coordinate of the Player
        y          = The initial y coordinate of the Player
        street     = pygame.Rect of the Street
        game_speed = Speed of the street
        """
        super(Player, self).__init__(*args)

    def up(self):
        """Moves the Player up."""
        if self.hitbox.top > self.street.top:
            self.hitbox = self.hitbox.move(0, -self.street.height / 30)

    def down(self):
        """Moves the Player down."""
        if self.hitbox.bottom < self.street.bottom:
            self.hitbox = self.hitbox.move(0, self.street.height / 30)

    def accelerate(self):
        """Accelerates the Player."""
        if self.hitbox.right < self.street.right:
            print "ACC"
            self.hitbox = self.hitbox.move(self.street.width / 120, 0)
        else:
            print self.hitbox.right, self.street.right

    def decelerate(self):
        """Decelerates the Player."""
        if self.hitbox.left > self.street.left:
            print "DEC"
            self.hitbox = self.hitbox.move(-self.street.width / 120, 0)

    def set_img(self, img):
        """
        Sets the image (and hitbox) of the Player. Argument:
        img = pygame.Surface containing the image for the Enity.
        """
        self.img = img
        self.hitbox = self.img.get_rect().move(self.x, self.y)

    def render(self, surface):
        """Blits the Player on `surface`."""
        surface.blit(self.img, self.hitbox)

class Deer(Entity):
    def __init__(self, move_type, *args):
        """
        Initializes the Deer instance. Arguments:
        move_type
        x          = The initial x coordinate of the Deer
        y          = The initial y coordinate of the Deer
        street     = pygame.Rect of the Street
        game_speed = Speed of the street
        """
        self.move_type = move_type
        super(Deer, self).__init__(*args)
        print "DEER CREATED"
        self.img = 0

    def move(self):
        """
        Moves the Deer according to its move_type. The movements are:
        0 = Moves to the left at Game.speed
        1 = Moves to the left at half Game.speed
        2 = Walks to the left and up
        3 = Walks to the left and down
        4 = Like 2, but aims for player's car at spawn time
        5 = Like 3, but aims for player's car at spawn time
        ...
        """
        if self.move_type == 0:
            self.hitbox = self.hitbox.move(-self.game_speed, 0)
            print "MOVED %s" % self.hitbox

    def set_imgs(self, imgs):
        """
        Sets the image (and hitbox) of the Deer. Argument:
        imgs = List of `pygame.Surface`s containing the image
               for the Enity.
        """
        self.imgs = imgs
        self.hitbox = self.imgs[0].get_rect().move(self.x, self.y)

    def next_img(self):
        self.img += 1
        self.img %= len(self.imgs)

    def render(self, surface):
        """Blits the Deer on `surface`."""
        surface.blit(self.imgs[self.img], self.hitbox)

class Game(object):
    def __init__(self, width=1200, height=400):
        """
        Initializes the Game instance. Arguments:
        width      = window width
        height     = window height
        """
        # Initialisierung
        self.width = width
        self.height = height

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Passée")
        pygame.mouse.set_visible(1)

        self.speed = 10

        self.player = Player(0, self.height//2, self.screen.get_rect(),
                             self.speed)

        self.deer = []
        self.next_deer = 30
        self.next_deer_max = 90
        self.next_deer_min = 70

        # Tastendruck wiederholt senden, falls nicht losgelassen
        pygame.key.set_repeat(1, 30)
        self.clock = pygame.time.Clock()
        self.running = False

    def set_street_img(self, path):
        img = pygame.image.load(path)
        img = img.convert()
        self.street_img = img

        self.scaled_street = self.scale_street_img()

    def scale_street_img(self):
        width = self.street_img.get_width()
        height = self.street_img.get_height()
        scale = height // self.height
        img = pygame.transform.scale(self.street_img,
                (width // scale, self.height))
        return img

    def get_street_img(self, pos):
        surf = pygame.Surface((self.width, self.height))
        for x in range(-pos, self.width, self.scaled_street.get_width()):
            surf.blit(self.scaled_street, (x, 0))
        return surf

    def set_player_img(self, path):
        img = pygame.image.load(path)
        img = img.convert_alpha()
        scale = img.get_height() / (self.height / 5.0)
        img = pygame.transform.scale(img, (int(round(img.get_width() / scale)),
            int(round(img.get_height() / scale))))
        self.player.set_img(img)

    def set_deer_img(self, paths):
        imgs = [pygame.image.load(path).convert_alpha() for path in paths]
        scale = imgs[0].get_height() / (self.height / 5.0)
        imgs = [pygame.transform.scale(img, (int(round(img.get_width() / scale)),
            int(round(img.get_height() / scale)))) for img in imgs]
        self.deer_imgs = imgs
        for deer in self.deer:
            deer.set_imgs(imgs)

    def spawn_deer(self):
        if randint(0, 1):
            # Laters
            #if self.speed < 20:
                #move_type = randint(0, 2)
            #elif self.speed < 30:
                #move_type = randint(0, 4)
            #else:
                #move_type = randint(0, 7)
            self.deer.append(Deer(
                0, self.width, randint(0,
                    self.height - self.deer_imgs[0].get_height()
                ), self.scaled_street.get_rect(), self.speed
            ))
            self.deer[-1].set_imgs(self.deer_imgs)

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

            if tick % 90 == 0:
                if self.next_deer_max > 30:
                    self.next_deer_max -= 1
                if self.next_deer_min > 15:
                    self.next_deer_min -= 1
            if tick % 75 == 0 and self.speed < 50:
                self.speed += 1
                for deer in self.deer:
                    deer.game_speed = self.speed
                self.player.game_speed = self.speed

            if self.next_deer == 0:
                self.spawn_deer()
                self.next_deer = randint(self.next_deer_min, self.next_deer_max)
            else:
                self.next_deer -= 1
 
            for deer in self.deer:
                deer.move()

            pos += self.speed
            pos %= self.scaled_street.get_width()
            self.screen.blit(self.get_street_img(pos), (0, 0))

            self.player.render(self.screen)

            for deer in self.deer:
                deer.render(self.screen)

            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.set_street_img(os.path.join("img", "rue_n_clip.png"))
    game.set_player_img(os.path.join("img", "voiture_r2.png"))
    game.set_deer_img([os.path.join("img", "chevreuil_m_gif%i.png" % i)
        for i in [1, 2, 3, 2]])
    game.run()
