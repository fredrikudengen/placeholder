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

    def move(self, obstacles, enemies):
        keys = pygame.key.get_pressed()
        
        # if keys[pygame.K_w]:
        #     self.rect.y -= self.speed
        #     if self.check_collision_obstacle(obstacles): 
        #         self.rect.y += self.speed    
                           
        # if keys[pygame.K_s]: 
        #     self.rect.y += self.speed
        #     if self.check_collision_obstacle(obstacles):
        #         self.rect.y -= self.speed
                
        # if keys[pygame.K_a]:
        #     self.rect.x -= self.speed
        #     if self.check_collision_obstacle(obstacles): 
        #         self.rect.x += self.speed
                
        # if keys[pygame.K_d]:
        #     self.rect.x += self.speed
        #     if self.check_collision_obstacle(obstacles):
        #         self.rect.x -= self.speed
                
        if self.attack_timer: 
            if pygame.time.get_ticks() - self.attack_timer > 500: # 0.5 seconds
                self.attack_timer = None
                self.playerAttack = False
            
        if not self.attack_timer:
            for enemy in enemies: 
                if keys[pygame.K_UP]:
                    self.attack(enemy, "up")
                    self.attack_timer = pygame.time.get_ticks()
                    
                elif keys[pygame.K_DOWN]:
                    self.attack(enemy, "down")
                    self.attack_timer = pygame.time.get_ticks()
                    
                elif keys[pygame.K_LEFT]:
                    self.attack(enemy, "left")
                    self.attack_timer = pygame.time.get_ticks()
                    
                elif keys[pygame.K_RIGHT]:
                    self.attack(enemy, "right")
                    self.attack_timer = pygame.time.get_ticks()
        
        if self.health <= 0:
            self.alive = False
            
        self.check_out_of_bounds()
        

    # def check_out_of_bounds(self):
    #     if self.rect.x < 0:
    #         self.rect.x = 0
    #     elif self.rect.x + self.rect.width > SCREEN_WIDTH:
    #         self.rect.x = SCREEN_WIDTH - self.rect.width

    #     if self.rect.y < 0:
    #         self.rect.y = 0
    #     elif self.rect.y + self.rect.height > SCREEN_HEIGHT:
    #         self.rect.y = SCREEN_HEIGHT - self.rect.height          
            
    def attack(self, enemy, direction):
        attack_rect = None
        
        if direction == "up":
            attack_rect = pygame.Rect(self.rect.x, self.rect.y - self.rect.height, self.rect.width, self.rect.height)
        elif direction == "down":
            attack_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height, self.rect.width, self.rect.height)
        elif direction == "left":
            attack_rect = pygame.Rect(self.rect.x - self.rect.width, self.rect.y, self.rect.width, self.rect.height)
        elif direction == "right":
            attack_rect = pygame.Rect(self.rect.x + self.rect.width, self.rect.y, self.rect.width, self.rect.height)
                
        if attack_rect.colliderect(enemy.rect): 
            enemy.health -= self.dps  
            enemy.hit = True  
            self.playerAttack = True
    
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

