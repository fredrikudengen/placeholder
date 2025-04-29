import pygame

from constants import *

class Enemy:
    
    hit_timer = None

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GREEN
        self.health = ENEMY_HEALTH
        self.alive = ALIVE
        self.hit = False
        self.hit_this_frame = False

    def move(self, player, obstacles):
        if self.hit_timer == None:  
            x_needed_to_move = player.rect.x - self.rect.x
            y_needed_to_move = player.rect.y - self.rect.y

            if x_needed_to_move > 0:
                self.rect.x += ENEMY_SPEED
                if self.check_collision(obstacles):
                    self.rect.x -= ENEMY_SPEED
                    
            if x_needed_to_move < 0:
                self.rect.x -= ENEMY_SPEED
                if self.check_collision(obstacles):
                    self.rect.x += ENEMY_SPEED
                    
            if y_needed_to_move > 0:
                self.rect.y += ENEMY_SPEED
                if self.check_collision(obstacles):
                    self.rect.y -= ENEMY_SPEED
                    
            if y_needed_to_move < 0:
                self.rect.y -= ENEMY_SPEED
                if self.check_collision(obstacles):
                    self.rect.y += ENEMY_SPEED

        if self.health <= 0:
            self.alive = False
                
        if self.hit:
            self.hit_timer = pygame.time.get_ticks()
            self.hit = False
        
        if self.hit_timer: 
            if pygame.time.get_ticks() - self.hit_timer > 500: # 0.5 seconds
                self.hit_timer = None
        
    def check_collision(self, obstacles):
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                return True
        return False

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, self.color, draw_rect)
