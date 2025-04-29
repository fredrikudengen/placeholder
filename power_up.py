import pygame
from constants import *

class BasePowerup:
    def __init__(self, x, y, size, color):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = color

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, self.color, draw_rect)

class Speed_Powerup(BasePowerup):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, YELLOW)
    def apply(self, player):
        player.apply_buff('speed_boost')
        
class Attack_Powerup(BasePowerup):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, RED)
    def apply(self, player):
        player.apply_buff('attack_boost')

class Shield_Powerup(BasePowerup):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, BLUE)
    def apply(self, player):
        player.apply_buff('shield_boost')
