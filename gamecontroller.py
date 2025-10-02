import pygame
import constants

def player_input(player, obstacles, enemies):
    keys = pygame.key.get_pressed()
    now = pygame.time.get_ticks()

    # init debug felter hvis de ikke finnes
    if not hasattr(player, "attack_timer"):
        player.attack_timer = None
    if not hasattr(player, "debug_attack_rect"):
        player.debug_attack_rect = None
    if not hasattr(player, "debug_attack_until"):
        player.debug_attack_until = 0

    # --- bevegelse ---
    old_x, old_y = player.rect.x, player.rect.y
    if keys[pygame.K_w]:
        player.rect.y -= player.speed
        if _collides(player, obstacles): player.rect.y = old_y
    if keys[pygame.K_s]:
        player.rect.y += player.speed
        if _collides(player, obstacles): player.rect.y = old_y
    if keys[pygame.K_a]:
        player.rect.x -= player.speed
        if _collides(player, obstacles): player.rect.x = old_x
    if keys[pygame.K_d]:
        player.rect.x += player.speed
        if _collides(player, obstacles): player.rect.x = old_x

    # --- cooldown slutt? ---
    if player.attack_timer and (now - player.attack_timer > 500):
        player.attack_timer = None
        player.playerAttack = False

    # --- start nytt angrep ---
    if not player.attack_timer:
        direction = _read_attack_direction(keys)
        if direction:
            attack_rect = _make_attack_rect(player, direction)

            # treff alle fiender
            for enemy in enemies:
                if attack_rect.colliderect(enemy.rect):
                    enemy.health -= player.dps
                    enemy.hit = True
                    enemy.hit_this_frame = True
                    player.playerAttack = True

            # start cooldown
            player.attack_timer = now

            # DEBUG: lagre siste attack rect til tegning
            if constants.DEBUG_SHOW_HITBOXES:
                player.debug_attack_rect = attack_rect
                player.debug_attack_until = now + constants.DEBUG_HITBOX_MS

    # død?
    if player.health <= 0:
        player.alive = False

def _collides(player, obstacles):
    for obs in obstacles:
        if player.rect.colliderect(obs):
            return True
    return False

def _read_attack_direction(keys):
    if keys[pygame.K_UP]:    return "up"
    if keys[pygame.K_DOWN]:  return "down"
    if keys[pygame.K_LEFT]:  return "left"
    if keys[pygame.K_RIGHT]: return "right"
    return None

def _make_attack_rect(player, direction):
    px, py, pw, ph = player.rect
    if direction == "up":    return pygame.Rect(px, py - ph, pw, ph)
    if direction == "down":  return pygame.Rect(px, py + ph, pw, ph)
    if direction == "left":  return pygame.Rect(px - pw, py, pw, ph)
    if direction == "right": return pygame.Rect(px + pw, py, pw, ph)
    return pygame.Rect(px, py, pw, ph)
