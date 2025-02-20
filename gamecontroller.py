import pygame

def player_input(player, obstacles):
    keys = pygame.key.get_pressed()
    
    old_x, old_y = player.rect.x, player.rect.y

    if keys[pygame.K_w]:
        player.rect.y -= player.speed
        if check_collision(player, obstacles):
            player.rect.y = old_y

    if keys[pygame.K_s]:
        player.rect.y += player.speed
        if check_collision(player, obstacles):
            player.rect.y = old_y

    if keys[pygame.K_a]:
        player.rect.x -= player.speed
        if check_collision(player, obstacles):
            player.rect.x = old_x

    if keys[pygame.K_d]:
        player.rect.x += player.speed
        if check_collision(player, obstacles):
            player.rect.x = old_x

def check_collision(player, obstacles):
    for obs in obstacles:
        if player.rect.colliderect(obs):
            return True
    return False
