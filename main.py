import pygame
from player import Player
from enemy import Enemy
from power_up import *
from constants import *
from gamecontroller import player_input
from camera import Camera


pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

player = Player(400, 300, 50, 50)
camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

obstacles = [
    pygame.Rect(300, 200, 100, 50),
    pygame.Rect(500, 400, 50, 100)
]

enemies = [Enemy(200, 200, 50, 50)]

powerups = [
    Speed_Powerup(210, 100, 20), 
    Shield_Powerup(170, 100, 20),
    Attack_Powerup(130, 100, 20)
]

def draw_with_offset(rect, color, offset, surface):
    draw_rect = pygame.Rect(
        rect.x - offset[0],
        rect.y - offset[1],
        rect.width,
        rect.height
    )
    pygame.draw.rect(surface, color, draw_rect)

def get_camera_offset(player_rect):
    offset_x = player_rect.centerx - SCREEN_WIDTH // 2
    offset_y = player_rect.centery - SCREEN_HEIGHT // 2
    return (offset_x, offset_y)

run = True
while run:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    player.update_buffs()

    player_input(player, obstacles, enemies)
    
    camera.update(player.rect)

    for enemy in enemies:
        enemy.move(player, obstacles)
        enemy.draw(screen, camera)
        if not enemy.alive:
            enemies.remove(enemy)

    for obstacle in obstacles:
        screen_rect = camera.apply(obstacle)
        pygame.draw.rect(screen, (128,128,128), screen_rect)
        
    for pu in powerups:
        if player.rect.colliderect(pu.rect):
            pu.apply(player)
            powerups.remove(pu)
        else:
            pu.draw(screen, camera)

    player.draw(screen, camera)
    
    pygame.display.update()
    clock.tick(60)

pygame.quit()
