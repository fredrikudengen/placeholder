import pygame
from player import Player
from enemy import Enemy
from power_up import *
from constants import *
from gamecontroller import player_input

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

player = Player(400, 300, 50, 50)

obstacles = [
    pygame.Rect(300, 200, 100, 50),
    pygame.Rect(500, 400, 50, 100)
]

enemies = []
speed_powerup = Speed_Powerup(210, 100, 20)
shield_powerup = Shield_Powerup(170, 100, 20)
attack_powerup = Attack_Powerup(130, 100, 20)

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

    player_input(player, obstacles)

    for enemy in enemies:
        enemy.move(player, obstacles)

    camera_offset = get_camera_offset(player.rect)

    for obstacle in obstacles:
        draw_with_offset(obstacle, (128, 128, 128), camera_offset, screen)

    for enemy in enemies:
        draw_with_offset(enemy.rect, enemy.color, camera_offset, screen)

    if speed_powerup:
        offset_rect = pygame.Rect(
            speed_powerup.rect.x - camera_offset[0],
            speed_powerup.rect.y - camera_offset[1],
            speed_powerup.rect.width,
            speed_powerup.rect.height
        )
        pygame.draw.rect(screen, speed_powerup.color, offset_rect)

    if attack_powerup:
        offset_rect = pygame.Rect(
            attack_powerup.rect.x - camera_offset[0],
            attack_powerup.rect.y - camera_offset[1],
            attack_powerup.rect.width,
            attack_powerup.rect.height
        )
        pygame.draw.rect(screen, attack_powerup.color, offset_rect)
    
    if shield_powerup:
        offset_rect = pygame.Rect(
            shield_powerup.rect.x - camera_offset[0],
            shield_powerup.rect.y - camera_offset[1],
            shield_powerup.rect.width,
            shield_powerup.rect.height
        )
        pygame.draw.rect(screen, shield_powerup.color, offset_rect)

    draw_with_offset(player.rect, player.color, camera_offset, screen)

    pygame.display.update()
    clock.tick(60)

pygame.quit()
