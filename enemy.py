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
        
         # --- Nytt for animasjon ---
        self.state = "idle"  # Kan være "idle", "walk", "attack", "hurt", "dead"
        self.animation_frame = 0
        self.animation_timer = pygame.time.get_ticks()

    def move(self, player, obstacles):
        now = pygame.time.get_ticks()
        
        if self.hit_timer == None: 
            self.state = "walk" 
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
            self.state = "dead"
                
        if self.hit:
            self.hit_timer = now
            self.hit = False
            self.state = "hurt"
        
        if self.hit_timer: 
            if now - self.hit_timer > 500: # 0.5 seconds
                self.hit_timer = None
        
        
        if now - self.animation_timer > 100:
            self.animation_frame = (self.animation_frame + 1) % 4  # f.eks 4 frames
            self.animation_timer = now
        
    def check_collision(self, obstacles):
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                return True
        return False

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        # Enn så lenge, bruk farger for å vise state
        if self.state == "walk":
            color = (0, 200, 0)
        elif self.state == "hurt":
            color = (255, 0, 0)
        elif self.state == "dead":
            color = (100, 100, 100)
        else:  # idle
            color = GREEN
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, color, draw_rect)
