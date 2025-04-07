"""
Battles v2
Devin Zhang 1/5/21 - 1/19/21
First pygame
Inspired by Right Click to Necromance
Character and Background Assets by 0x72 @ https://0x72.itch.io/dungeontileset-ii?download
Boss Character Assets by Superdark @ https://superdark.itch.io/enchanted-forest-characters
Blood Assets by XYEzawr @ https://xyezawr.itch.io/gif-free-pixel-effects-pack-5-blood-effects
Font Asset by Poppy Works @ https://poppyworks.itch.io/silver?download
Particle Assets by Will Tice @ https://untiedgames.itch.io/five-free-pixel-explosions
"""

import math
import os
import random
import pygame

WIDTH, HEIGHT = 512, 512
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Battles")

PLACEHOLDER = pygame.image.load(os.path.join("assets", "crate.png")).convert_alpha()
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "dungeon.png")).convert_alpha(), (WIDTH, HEIGHT))
COIN = pygame.transform.scale(pygame.image.load(os.path.join("assets", "coin.png")).convert_alpha(), (12, 15))
IMP = pygame.image.load(os.path.join("assets", "imp_idle_anim_f0.png")).convert_alpha()
WOGOL = pygame.image.load(os.path.join("assets", "wogol_idle_anim_f0.png")).convert_alpha()
CHORT = pygame.image.load(os.path.join("assets", "chort_idle_anim_f0.png")).convert_alpha()
BIG_DEMON = pygame.image.load(os.path.join("assets", "big_demon_idle_anim_f0.png")).convert_alpha()

coins = 0
difficulty = 1.0
FPS = 60

all_sprites = []
ally_sprites = []
enemy_sprites = []

class Sprite(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, speed: float = 1.0, hp: float = 1.0, atk: float = 1.0, image: pygame.Surface = PLACEHOLDER):
        pygame.sprite.Sprite.__init__(self)
        self.pos = pygame.math.Vector2(x, y)
        self.speed = speed
        self.hp = hp * FPS # 1 HP = 1 second of survival when attacked at 1 atk
        self.atk = atk
        self.image = image
        self.rect = self.image.get_rect()
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.dir = 0.0 # radians
        self.target_x = self.pos.x
        self.target_y = self.pos.y

        self.taking_damage = False

        self.idle_anim_index = 0
        self.run_anim_index = 0
        self.idle_anims = []
        self.run_anims = []

    def update(self):
        """
        Behavior function meant to be overridden
        """
        pass

    def move(self, x, y):
        x += -self.image.get_width()//2
        y += -self.image.get_height()//2

        dy = y - self.pos.y
        dx = x - self.pos.x

        # Prevent divide by 0 error
        if dx != 0:
            self.dir = math.atan2(dy, dx)
        else:
            self.dir = ((dy > 0) * math.pi/2) + ((dy < 0) * 3*math.pi/2)

        if abs(dx) > self.speed and abs(dy) > self.speed:
            self.acc = pygame.math.Vector2(1, 0).rotate_rad(self.dir)
            self.social_distance()
            try:
                self.acc.scale_to_length(self.speed)
            except:
                pass
            self.acc += -self.vel
            self.vel += self.acc
            self.pos += self.vel
        else:
            try:
                self.vel.scale_to_length(0)
                self.acc.scale_to_length(0)
            except:
                pass

        self.rect.update(self.pos.x, self.pos.y, self.rect.width, self.rect.height)

    def draw(self):
        """
        Handles animation and which direction sprite is facing
        """
        def idle_animations():
            SLOWDOWN_FACTOR = 6 # How much to slow the animation down by

            self.image = self.idle_anims[self.idle_anim_index // SLOWDOWN_FACTOR]
            self.idle_anim_index += 1
            if self.idle_anim_index >= len(self.idle_anims) * SLOWDOWN_FACTOR:
                    self.idle_anim_index = 0

        def run_animations():
            SLOWDOWN_FACTOR = 6 # How much to slow the animation down by

            self.image = self.run_anims[self.run_anim_index // SLOWDOWN_FACTOR]
            self.run_anim_index += 1
            if self.run_anim_index >= len(self.run_anims) * SLOWDOWN_FACTOR:
                    self.run_anim_index = 0

        def damage_animations():
            image_copy = self.image.copy()
            image_copy.fill((255, 0, 0), special_flags = pygame.BLEND_MULT)
            self.image = image_copy
            WINDOW.blit(image_copy, (self.pos.x, self.pos.y))
            self.taking_damage = False

        if self.vel.magnitude() == 0:
            idle_animations()
        else:
            run_animations()
        if self.taking_damage:
            damage_animations()

        # Facing left or right
        if self.dir < math.pi/2 and self.dir > -math.pi/2:
            WINDOW.blit(self.image, (self.pos.x, self.pos.y))
        else:
            WINDOW.blit(pygame.transform.flip(self.image, True, False), (self.pos.x, self.pos.y))

    def social_distance(self):
        """
        Prevent sprites from bunching up
        """
        AVOID_RADIUS = 15 # Lower number for more dense crowds

        for sprite in all_sprites:
            if sprite != self:
                if (self in ally_sprites and sprite in ally_sprites) or (self in enemy_sprites and sprite in enemy_sprites):
                    dist = self.pos - sprite.pos
                    if 0 < dist.length() < AVOID_RADIUS:
                        self.acc += dist.normalize()

    def attack(self):
        for sprite in all_sprites:
            if (self in ally_sprites and sprite in enemy_sprites) or (self in enemy_sprites and sprite in ally_sprites):
                if pygame.sprite.collide_rect(self, sprite):
                    sprite.taking_damage = True
                    sprite.hp += -self.atk
class Ally(Sprite):
    def __init__(self, x: int, y: int, speed: float = 2.0, hp: float = 1.0, atk: float = 1.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, hp, atk, image)

    def update(self):
        if self.hp <= 0:
            all_sprites.remove(self)
            ally_sprites.remove(self)
        self.move(self.target_x, self.target_y)
        self.attack()
        self.draw()
class Enemy(Sprite):
    def __init__(self, x: int, y: int, speed: float = 2.0, hp: float = 1.0, atk: float = 1.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, hp, atk, image)

    def update(self):
        global coins
        global difficulty

        if ally_sprites:
            self.target_x, self.target_y = self.find_ally()

        if self.hp <= 0:
            all_sprites.remove(self)
            enemy_sprites.remove(self)
            coins += 1
            difficulty += .1 # Increase to change how fast difficulty ramps up
        self.move(self.target_x, self.target_y)
        self.attack()
        self.draw()

    def find_ally(self):
        distances = []
        for ally in ally_sprites:
            distances.append((ally.pos, self.pos.distance_to(ally.pos)))
        return (min(distances, key = lambda x: x[1])[0])

class Imp(Ally):
    def __init__(self, x: int, y: int, speed: float = 2.0, hp: float = 2.0, atk: float = 1.0, image: pygame.Surface = IMP):
        super().__init__(x, y, speed, hp, atk, image)

        self.idle_anims = [pygame.image.load(os.path.join("assets", "imp_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "imp_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "imp_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "imp_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "imp_run_anim_f0.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "imp_run_anim_f1.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "imp_run_anim_f2.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "imp_run_anim_f3.png")).convert_alpha()]
class Wogol(Ally):
    def __init__(self, x: int, y: int, speed: float = 4.0, hp: float = 4.0, atk: float = 1.0, image: pygame.Surface = WOGOL):
        super().__init__(x, y, speed, hp, atk, image)

        self.idle_anims = [pygame.image.load(os.path.join("assets", "wogol_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "wogol_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "wogol_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "wogol_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "wogol_run_anim_f0.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "wogol_run_anim_f1.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "wogol_run_anim_f2.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "wogol_run_anim_f3.png")).convert_alpha()]
class Chort(Ally):
    def __init__(self, x: int, y: int, speed: float = 3.0, hp: float = 6.0, atk: float = 2.0, image: pygame.Surface = CHORT):
        super().__init__(x, y, speed, hp, atk, image)

        self.idle_anims = [pygame.image.load(os.path.join("assets", "chort_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "chort_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "chort_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "chort_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "chort_run_anim_f0.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "chort_run_anim_f1.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "chort_run_anim_f2.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "chort_run_anim_f3.png")).convert_alpha()]
class Big_Demon(Ally):
    def __init__(self, x: int, y: int, speed: float = 1.0, hp: float = 10.0, atk: float = 3.0, image: pygame.Surface = BIG_DEMON):
        super().__init__(x, y, speed, hp, atk, image)

        self.idle_anims = [pygame.image.load(os.path.join("assets", "big_demon_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "big_demon_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "big_demon_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "big_demon_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "big_demon_run_anim_f0.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "big_demon_run_anim_f1.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "big_demon_run_anim_f2.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "big_demon_run_anim_f3.png")).convert_alpha()]
class Elf(Enemy):
    def __init__(self, x: int, y: int, speed: float = 1.0, hp: float = 1.0, atk: float = 1.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, hp, atk, image)
        self.idle_anim_index = 0
        self.run_anim_index = 0

        self.idle_anims = [pygame.image.load(os.path.join("assets", "elf_m_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "elf_m_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "elf_m_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "elf_m_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "elf_m_run_anim_f0.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "elf_m_run_anim_f1.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "elf_m_run_anim_f2.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "elf_m_run_anim_f3.png")).convert_alpha()]

    def attack(self):
        prob = random.randint(1, 2 * FPS)
        if prob == 1:
            all_sprites.append(Arrow(self.pos.x, self.pos.y, 3.0, self.dir, 1.0))
class Knight(Enemy):
    def __init__(self, x: int, y: int, speed: float = 1.5, hp: float = 2.0, atk: float = 1.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, hp, atk, image)
        self.idle_anim_index = 0
        self.run_anim_index = 0

        self.idle_anims = [pygame.image.load(os.path.join("assets", "knight_m_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "knight_m_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "knight_m_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "knight_m_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "knight_m_run_anim_f0.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "knight_m_run_anim_f1.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "knight_m_run_anim_f2.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "knight_m_run_anim_f3.png")).convert_alpha()]
class Wizard(Enemy):
    def __init__(self, x: int, y: int, speed: float = 1.0, hp: float = 1.0, atk: float = 1.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, hp, atk, image)
        self.idle_anim_index = 0
        self.run_anim_index = 0

        self.idle_anims = [pygame.image.load(os.path.join("assets", "wizard_m_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "wizard_m_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "wizard_m_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "wizard_m_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "wizard_m_run_anim_f0.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "wizard_m_run_anim_f1.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "wizard_m_run_anim_f2.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "wizard_m_run_anim_f3.png")).convert_alpha()]
    
    def attack(self):
        prob = random.randint(1, 4 * FPS)
        if prob == 1:
            all_sprites.append(Fireball(self.pos.x, self.pos.y, 3.0, self.dir, 5.0))
class Necromancer(Enemy):
    def __init__(self, x: int, y: int, speed: float = 1.0, hp: float = 1.0, atk: float = 1.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, hp, atk, image)
        self.idle_anim_index = 0
        self.run_anim_index = 0

        self.idle_anims = [pygame.image.load(os.path.join("assets", "necromancer_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "necromancer_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "necromancer_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "necromancer_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "necromancer_run_anim_f0.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "necromancer_run_anim_f1.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "necromancer_run_anim_f2.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "necromancer_run_anim_f3.png")).convert_alpha()]

    def attack(self):
        """
        Summon skeletons
        """
        prob = random.randint(1, 3 * FPS)
        if prob == 1:
            random_nearby_x = random.randint(int(self.pos.x) - 5, int(self.pos.x) + 5)
            random_nearby_y = random.randint(int(self.pos.y) - 5, int(self.pos.y) + 5)
            skeleton = Skeleton(random_nearby_x, random_nearby_y)
            enemy_sprites.append(skeleton)
            all_sprites.append(skeleton)
class Skeleton(Enemy):
    def __init__(self, x: int, y: int, speed: float = 1.0, hp: float = 1.0, atk: float = 1.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, hp, atk, image)
        self.idle_anim_index = 0
        self.run_anim_index = 0

        self.idle_anims = [pygame.image.load(os.path.join("assets", "skeleton_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "skeleton_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "skeleton_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "skeleton_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "skeleton_run_anim_f0.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "skeleton_run_anim_f1.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "skeleton_run_anim_f2.png")).convert_alpha(),
                          pygame.image.load(os.path.join("assets", "skeleton_run_anim_f3.png")).convert_alpha()]
class Elven_Knight(Enemy):
    def __init__(self, x: int, y: int, speed: float = 2.0, hp: float = 10.0, atk: float = 3.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, hp, atk, image)
        self.idle_anim_index = 0
        self.run_anim_index = 0

        self.idle_anims = [pygame.image.load(os.path.join("assets", "elven_knight_idle_anim_f0.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "elven_knight_idle_anim_f1.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "elven_knight_idle_anim_f2.png")).convert_alpha(),
                           pygame.image.load(os.path.join("assets", "elven_knight_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "elven_knight_idle_anim_f1.png")).convert_alpha()]
class Kingsguard(Enemy):
    def __init__(self, x: int, y: int, speed: float = 1, hp: float = 20.0, atk: float = 5.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, hp, atk, image)
        self.idle_anim_index = 0
        self.run_anim_index = 0

        self.idle_anims = [pygame.image.load(os.path.join("assets", "kingsguard_idle_anim_f0.png")).convert_alpha(),
                            pygame.image.load(os.path.join("assets", "kingsguard_idle_anim_f1.png")).convert_alpha(),
                            pygame.image.load(os.path.join("assets", "kingsguard_idle_anim_f2.png")).convert_alpha(),
                            pygame.image.load(os.path.join("assets", "kingsguard_idle_anim_f3.png")).convert_alpha()]
        self.run_anims = [pygame.image.load(os.path.join("assets", "kingsguard_run_anim_f0.png")).convert_alpha(),
                            pygame.image.load(os.path.join("assets", "kingsguard_run_anim_f1.png")).convert_alpha(),
                            pygame.image.load(os.path.join("assets", "kingsguard_run_anim_f2.png")).convert_alpha(),
                            pygame.image.load(os.path.join("assets", "kingsguard_run_anim_f3.png")).convert_alpha()]

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, speed: float = 1.0, dirr: float = 0.0, atk: float = 1.0):
        pygame.sprite.Sprite.__init__(self)
        self.pos = pygame.math.Vector2(x, y)
        self.speed = speed
        self.dir = dirr # radians
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.atk = atk
        self.rect = pygame.Rect(self.pos.x, self.pos.y, 6, 6)
        self.colliding = False

    def update(self):
        """
        Behavior function meant to be overridden
        """
        pass

    def draw(self):
        """
        Behavior function meant to be overridden
        """
        pass

    def move(self):
        self.acc = pygame.math.Vector2(1, 0).rotate_rad(self.dir)
        try:
            self.acc.scale_to_length(self.speed)
        except:
            pass
        self.acc += -self.vel
        self.vel += self.acc
        self.pos += self.vel
        
        self.rect.update(self.pos.x, self.pos.y, self.rect.width, self.rect.height)

    def attack(self):
        self.colliding = False

        if self.pos.x < 0 or self.pos.x > WIDTH or self.pos.y < 0 or self.pos.y > HEIGHT:
            all_sprites.remove(self)
        else:
            for sprite in ally_sprites:
                if pygame.sprite.collide_rect(self, sprite):
                    self.colliding = True
                    sprite.taking_damage = True
                    sprite.hp += -self.atk
class Arrow(Projectile):
    def __init__(self, x: int, y: int, speed: float = 1.0, dirr: float = 0.0, atk: float = 1.0):
        super().__init__(x, y, speed, dirr, atk)
        self.color = (192, 192, 192)

    def update(self):
        if not self.colliding:
            self.move()
        self.attack()
        self.draw()

    def draw(self):
        pygame.draw.ellipse(WINDOW, self.color, self.rect)
class Fireball(Projectile):
    def __init__(self, x: int, y: int, speed: float = 1.0, dirr: float = 0.0, atk: float = 1.0, image: pygame.Surface = PLACEHOLDER):
        super().__init__(x, y, speed, dirr, atk)
        self.anim_index = 0
        self.image = pygame.image.load(os.path.join("assets/explosion_frames", "explosion_f0.png")).convert_alpha()
        self.rect = self.image.get_rect()
        self.exploding = False

    def update(self):
        if not self.exploding:
            self.move()
        if self.colliding:
            self.exploding = True
        self.attack()
        self.draw()
            
    def draw(self):
        self.image = pygame.image.load(os.path.join("assets/explosion_frames", "explosion_f" + str(self.anim_index) + ".png")).convert_alpha()
        WINDOW.blit(self.image, (self.pos.x, self.pos.y))
        if self.exploding:
            self.anim_index += 1
        if self.anim_index > 63:
            all_sprites.remove(self)

def main():
    pygame.init()
    pygame.font.init()
    clock = pygame.time.Clock()
    running = True
    main_font = pygame.font.Font(os.path.join("assets", "Silver.ttf"), 25)

    imp_button = pygame.Rect(10, HEIGHT - 50, 25, 25)
    wogol_button = pygame.Rect(40, HEIGHT - 50, 25, 25)
    chort_button = pygame.Rect(70, HEIGHT - 50, 25, 25)
    big_demon_button = pygame.Rect(100, HEIGHT - 50, 25, 25)

    begin_imps = [Imp(WIDTH//2 - IMP.get_width()//2, HEIGHT//2 - IMP.get_height()//2),
                  Imp(WIDTH//2 - IMP.get_width()//2 - 10, HEIGHT//2 - IMP.get_height()//2),
                  Imp(WIDTH//2 - IMP.get_width()//2 + 10, HEIGHT//2 - IMP.get_height()//2),
                  Imp(WIDTH//2 - IMP.get_width()//2, HEIGHT//2 - IMP.get_height()//2 - 10),
                  Imp(WIDTH//2 - IMP.get_width()//2, HEIGHT//2 - IMP.get_height()//2 + 10)]
    for imp in begin_imps:
        ally_sprites.append(imp)
        all_sprites.append(imp)

    def draw_ui():
        # Coins
        coins_label = main_font.render(str(coins), 1, (255, 255, 255))
        WINDOW.blit(COIN, (10, 27))
        WINDOW.blit(coins_label, (25, 24))

        # Sprite Summon Art
        WINDOW.blit(IMP, (imp_button.x + 4, imp_button.y + 2))
        WINDOW.blit(WOGOL, (wogol_button.x + 4, wogol_button.y))
        WINDOW.blit(CHORT, (chort_button.x + 4, chort_button.y - 3))
        WINDOW.blit(BIG_DEMON, (big_demon_button.x - 4, big_demon_button.y - 9))

        # Sprite Summon Box
        pygame.draw.rect(WINDOW, (180, 180, 180), imp_button, 1)
        pygame.draw.rect(WINDOW, (180, 180, 180), wogol_button, 1)
        pygame.draw.rect(WINDOW, (180, 180, 180), chort_button, 1)
        pygame.draw.rect(WINDOW, (180, 180, 180), big_demon_button, 1)

        # Sprite Summon Cost
        WINDOW.blit(COIN, (imp_button.x + 15, imp_button.y + 15))
        WINDOW.blit(main_font.render("1", 1, (0, 0, 0)), (imp_button.x + 17, imp_button.y + 15))
        WINDOW.blit(COIN, (wogol_button.x + 15, wogol_button.y + 15))
        WINDOW.blit(main_font.render("3", 1, (0, 0, 0)), (wogol_button.x + 17, wogol_button.y + 15))
        WINDOW.blit(COIN, (chort_button.x + 15, chort_button.y + 15))
        WINDOW.blit(main_font.render("5", 1, (0, 0, 0)), (chort_button.x + 17, chort_button.y + 15))
        WINDOW.blit(COIN, (big_demon_button.x + 15, big_demon_button.y + 15))
        WINDOW.blit(main_font.render("9", 1, (0, 0, 0)), (big_demon_button.x + 17, big_demon_button.y + 15))

    def button_event(mouse_pos, spawn):
        """
        Performs the behavior of buttons. Returns True if button is pressed
        """
        global coins
        sprite = None
        center_x = WIDTH//2
        center_y = HEIGHT//2

        if imp_button.collidepoint(mouse_pos) or spawn == Imp:
            cost = 1
            if coins >= cost:
                coins += -cost
                sprite = Imp(center_x - IMP.get_width()//2, center_y - IMP.get_height()//2)
        elif wogol_button.collidepoint(mouse_pos) or spawn == Wogol:
            cost = 3
            if coins >= cost:
                coins += -cost
                sprite = Wogol(center_x - WOGOL.get_width()//2, center_y - WOGOL.get_height()//2)
        elif chort_button.collidepoint(mouse_pos) or spawn == Chort:
            cost = 5
            if coins >= cost:
                coins += -cost
                sprite = Chort(center_x - CHORT.get_width()//2, center_y - CHORT.get_height()//2)
        elif big_demon_button.collidepoint(mouse_pos) or spawn == Big_Demon:
            cost = 9
            if coins >= cost:
                coins += -cost
                sprite = Big_Demon(center_x - BIG_DEMON.get_width()//2, center_y - BIG_DEMON.get_height()//2)
        else:
            sprite = None

        if sprite:
            ally_sprites.append(sprite)
            all_sprites.append(sprite)
            return True
        else:
            return False

    def trigger_wave():
        global difficulty

        if len(enemy_sprites) < round(difficulty):
            random_type = random.choice([Elf, Knight, Wizard, Necromancer])
            if difficulty >= 3.0:
                prob = random.randint(1, 3 * FPS)
                if difficulty >= 5.0 and prob == 1:
                    random_type = Kingsguard
                elif prob == 1 or prob == 2:
                    random_type = Elven_Knight

            # Set spawn at border
            random_x = random.randint(0, WIDTH)
            if random_x <= 10:
                random_y = random.randint(0, HEIGHT)
            elif random_x > 10 and random_x < WIDTH:
                random_y1 = random.randint(0, 10)
                random_y2 = random.randint(HEIGHT - 10, HEIGHT)
                random_y = random.choice([random_y1, random_y2])
            elif random_x >= HEIGHT - 10:
                random_y = random.randint(0, HEIGHT)

            random_enemy = random_type(random_x, random_y)
            enemy_sprites.append(random_enemy)
            all_sprites.append(random_enemy)

    def update():
        WINDOW.blit(BG, (0, 0))

        # Draw shadows
        for sprite in all_sprites:
            if Projectile not in type(sprite).__bases__:
                pygame.draw.ellipse(WINDOW, (45, 45, 45), pygame.Rect(sprite.pos.x, sprite.pos.y + sprite.image.get_height(), sprite.image.get_width(), 5))

        trigger_wave()
        for sprite in all_sprites:
            sprite.update()
        draw_ui()
        pygame.display.update()

    while running:
        clock.tick(FPS)
        update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]: # Left click, (leftclick, middleclick, rightclick)
                    mouse_pos = pygame.mouse.get_pos()
                    if not button_event(mouse_pos, None):
                        for sprite in ally_sprites:
                            sprite.target_x, sprite.target_y = mouse_pos
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        button_event(mouse_pos, Imp)
                    elif event.key == pygame.K_2:
                        button_event(mouse_pos, Wogol)
                    elif event.key == pygame.K_3:
                        button_event(mouse_pos, Chort)
                    elif event.key == pygame.K_4:
                        button_event(mouse_pos, Big_Demon)
main()
