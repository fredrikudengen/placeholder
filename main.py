import pygame

from player import Player
from enemy import Enemy
from power_up import *
from constants import *

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

camera_x = 0
camera_y = 0

player = Player(400, 300, 50, 50)  

speed_powerup = Speed_Powerup(210, 100, 20)
shield_powerup = Shield_Powerup(170, 100, 20)
attack_powerup = Attack_Powerup(130, 100, 20)  

enemies = [
    # Enemy(100, 100, 50, 50),
    # Enemy(500, 300, 50, 50),
    # Enemy(700, 150, 50, 50)
]

obstacles = [
    pygame.Rect(300, 200, 100, 50),
    pygame.Rect(500, 400, 50, 100)
]

speed_powerup_collected_time = None
attack_powerup_collected_time = None
invincibility = None

run = True
while run:
    screen.fill(BLACK)
    
    collision = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            
    
    keys = pygame.key.get_pressed()
    camera_x, camera_y = 0, 0

    if keys[pygame.K_w]:
        camera_y -= player.speed
        for obstacle in obstacles:
            if player.rect.colliderect(obstacle):
                collision = True
                camera_y += player.speed                    
            if not collision:
                obstacle.y -= camera_y
    if keys[pygame.K_s]:
        camera_y += player.speed
        for obstacle in obstacles:
            if player.rect.colliderect(obstacle):
                collision = True
                camera_y -= player.speed                    
            if not collision:
                obstacle.y -= camera_y
    if keys[pygame.K_a]:
        camera_x -= player.speed
        for obstacle in obstacles:
            if player.rect.colliderect(obstacle):
                collision = True
                camera_x += player.speed                    
            if not collision:
                obstacle.x -= camera_x
                
    if keys[pygame.K_d]:
        camera_x += player.speed
        for obstacle in obstacles:
            if player.rect.colliderect(obstacle):
                collision = True
                camera_x -= player.speed                    
            if not collision:
                obstacle.x -= camera_x

    player.draw(screen)
    for obstacle in obstacles:
        pygame.draw.rect(screen, (128, 128, 128), obstacle)
        
    for enemy in enemies:
        enemy.rect.x -= camera_x 
        enemy.rect.y -= camera_y
        enemy.move(player, obstacles)
        enemy.draw(screen)
    
    print(camera_x, camera_y)
    if speed_powerup:
        speed_powerup.draw(screen, camera_x, camera_y)

    if shield_powerup:
        shield_powerup.draw(screen, camera_x, camera_y)

    if attack_powerup:
        attack_powerup.draw(screen, camera_x, camera_y)

    pygame.display.update()
    clock.tick(60)

pygame.quit()
