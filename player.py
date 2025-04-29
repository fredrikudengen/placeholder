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
        self.buff_timers = {}
    
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
    
    def apply_buff(self, powerup):
        if powerup == 'speed_boost':
            self.speed += 3
            self.buff_timers[powerup] = pygame.time.get_ticks()
        elif powerup == 'shield_boost':
            self.health += 2
            self.buff_timers[powerup] = pygame.time.get_ticks()
        elif powerup == 'attack_boost':
            self.dps += 1
            self.buff_timers[powerup] = pygame.time.get_ticks()
            
    def update_buffs(self):
        now = pygame.time.get_ticks()
        expired = []
        # list lager en kopi, god stil når man itererer og muterer samtidig
        for name, start in list(self.buff_timers.items()):
            duration = BUFF_DURATIONS.get(name, 0)
            if now - start >= duration:
                expired.append(name)

        # Fjern effekt
        for name in expired:
            if name == 'speed_boost':
                self.speed -= 3
            elif name == 'attack_boost':
                self.dps -= 1
            elif name == 'shield_boost':
                self.health -= 2
                
            self.buff_timers.pop(name)

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        color = RED if self.playerAttack else self.color
        pygame.draw.rect(screen, color, draw_rect)

