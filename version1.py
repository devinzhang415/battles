"""
Battles v1
Devin Zhang 1/3/21 - 1/4/21
First pygame
Inspired by Right Click to Necromance
Assets by 0x72 @ https://0x72.itch.io/dungeontileset-ii?download

NOTES: learned a lot about working with pygame. See lots of room for improvement,
overall spending more time trying to make old things work with things I'm trying
to implement, decided to end project and start over after more learning. Ended on
trying to implement between two friendly units from phasing through each other (collision),
got too clunky.
"""

import math
import os
import pygame

WIDTH, HEIGHT = 500, 500
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Battles")

BG = pygame.image.load(os.path.join("assets", "floor_1.png")) # TODO PLACEHOLDER
BG = pygame.transform.scale(BG, (WIDTH, HEIGHT))

anim = [
    pygame.image.load(os.path.join("assets", "imp_idle_anim_f0.png")),
    pygame.image.load(os.path.join("assets", "imp_run_anim_f0.png")),
    pygame.image.load(os.path.join("assets", "imp_run_anim_f1.png")),
    pygame.image.load(os.path.join("assets", "imp_run_anim_f2.png")),
    pygame.image.load(os.path.join("assets", "imp_run_anim_f3.png")),
]

IMP = anim[0]

class Player():
    """
    Player class - controls player units
    """
    def __init__(self, x, y, img, vel):
        self.x = x
        self.y = y
        self.img = img
        self.rect = img
        self.vel = vel
        self.facing = "RIGHT"
        self.running = False
        self.anim_index = 0

    def draw(self, window):
        """
        Draw in updated pos
        """
        SLOWDOWN_FACTOR = 4

        if self.running:
            self.img = anim[self.anim_index // SLOWDOWN_FACTOR]
            self.anim_index += 1
            if self.anim_index >= len(anim) * SLOWDOWN_FACTOR:
                self.anim_index = 0
        else:
            self.img = anim[0]

        if self.facing == "LEFT":
            window.blit(pygame.transform.flip(self.img, True, False), (self.x, self.y))
        else:
            window.blit(self.img, (self.x, self.y))

    def move(self, x, y):
        """
        Move to (x, y) in straight line
        """
        dy = y - self.y
        dx = x - self.x
        if dx != 0:
            angle = math.atan2(dy, dx)
        else:
            angle = ((dy > 0) * math.pi/2) + ((dy < 0) * 3*math.pi/2)

        if dx == 0 and dy == 0:
            x_vel = 0
            y_vel = 0
        else:
            x_vel = math.cos(angle) * self.vel
            y_vel = math.sin(angle) * self.vel
            
        # Make sure it is facing direction it is walking
        # TODO Still buggy but works in niche positions
        if x_vel and y_vel:
            self.facing = ((x_vel < 0) * "LEFT") + ((x_vel > 0) * "RIGHT")

        # Toggle running animations
        if x_vel:
            self.running = True
        else:
            self.running = False

        # Prevents stutter-stepping when can't reach x, y because vel too high
        if abs(self.x - x) < x_vel:
            self.x = x
        else:
            self.x += x_vel
        if abs(self.y - y) < y_vel:
            self.y = y
        else:
            self.y += y_vel

def main():
    """
    Main loop of game
    """
    FPS = 60

    clock = pygame.time.Clock()

    units = []
    imp = Player(0, 0, IMP, 1.3)
    units.append(imp)

    def draw_window():
        """
        Updates window each frame
        """
        WINDOW.blit(BG, (0, 0))
        for unit in units:
            unit.draw(WINDOW)

        pygame.display.update()

    running = True
    mouse_x, mouse_y = 0, 0
    while running:
        clock.tick(FPS)
        draw_window()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
   
        if mouse_x and mouse_y:
            for unit in units:
                unit.move(mouse_x, mouse_y)
main()
