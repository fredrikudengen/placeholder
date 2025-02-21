import pygame

def player_input(player, obstacles, enemies):
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
            
    if player.attack_timer: 
            if pygame.time.get_ticks() - player.attack_timer > 500: # 0.5 seconds
                player.attack_timer = None
                player.playerAttack = False
            
    if not player.attack_timer:
        for enemy in enemies: 
            if keys[pygame.K_UP]:
                print("Attack up\n")
                attack(player, enemy, "up")
                player.attack_timer = pygame.time.get_ticks()
                    
            elif keys[pygame.K_DOWN]:
                attack(player, enemy, "down")
                player.attack_timer = pygame.time.get_ticks()
                    
            elif keys[pygame.K_LEFT]:
                attack(player, enemy, "left")
                player.attack_timer = pygame.time.get_ticks()
                    
            elif keys[pygame.K_RIGHT]:
                attack(player, enemy, "right")
                player.attack_timer = pygame.time.get_ticks()
        
    if player.health <= 0:
        player.alive = False
            
    # player.check_out_of_bounds()
        

    # def check_out_of_bounds(player):
    #     if player.rect.x < 0:
    #         player.rect.x = 0
    #     elif player.rect.x + player.rect.width > SCREEN_WIDTH:
    #         player.rect.x = SCREEN_WIDTH - player.rect.width

    #     if player.rect.y < 0:
    #         player.rect.y = 0
    #     elif player.rect.y + player.rect.height > SCREEN_HEIGHT:
    #         player.rect.y = SCREEN_HEIGHT - player.rect.height          
            
def attack(player, enemy, direction):
    attack_rect = None
        
    if direction == "up":
        attack_rect = pygame.Rect(player.rect.x, player.rect.y - player.rect.height, player.rect.width, player.rect.height)
    elif direction == "down":
        attack_rect = pygame.Rect(player.rect.x, player.rect.y + player.rect.height, player.rect.width, player.rect.height)
    elif direction == "left":
        attack_rect = pygame.Rect(player.rect.x - player.rect.width, player.rect.y, player.rect.width, player.rect.height)
    elif direction == "right":
        attack_rect = pygame.Rect(player.rect.x + player.rect.width, player.rect.y, player.rect.width, player.rect.height)
                
    if attack_rect.colliderect(enemy.rect): 
        enemy.health -= player.dps  
        enemy.hit = True  
        player.playerAttack = True

def check_collision(player, obstacles):
    for obs in obstacles:
        if player.rect.colliderect(obs):
            return True
    return False
