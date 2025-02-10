import pygame
from constants import *

class Speed_Powerup:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = YELLOW

    def draw(self, screen, camera_x, camera_y):
        self.rect.x -= camera_x
        self.rect.y -= camera_y
        pygame.draw.rect(screen, self.color, pygame.Rect(
            self.rect.x - camera_x, self.rect.y - camera_y, self.rect.width, self.rect.height))

class Attack_Powerup:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = RED

    def draw(self, screen, camera_x, camera_y):
        self.rect.x -= camera_x
        self.rect.y -= camera_y
        pygame.draw.rect(screen, self.color, pygame.Rect(
            self.rect.x - camera_x, self.rect.y - camera_y, self.rect.width, self.rect.height))

class Shield_Powerup:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = BLUE

    def draw(self, screen, camera_x, camera_y):
        self.rect.x -= camera_x
        self.rect.y -= camera_y
        pygame.draw.rect(screen, self.color, pygame.Rect(
            self.rect.x - camera_x, self.rect.y - camera_y, self.rect.width, self.rect.height))
