import pygame

from constants import *

class Player:
        
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = PLAYER_COLOR
        self.speed = PLAYER_SPEED
        self.health = PLAYER_HEALTH
        self.dps = PLAYER_DPS
        self.alive = ALIVE
        self.attack_timer = None
        self.playerAttack = False
    
    def check_collision_obstacle(self, obstacles):
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                return True
        return False
    
    def check_collision_enemy(self, enemies):
        for enemy in enemies:
            if self.rect.colliderect(enemy):
                return True
        return False
    
    def draw(self, screen):
        if self.playerAttack:
            pygame.draw.rect(screen, RED, self.rect)
        else:
            pygame.draw.rect(screen, self.color, self.rect)

