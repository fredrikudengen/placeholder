import pygame
import constants
from player import Player
from camera import Camera
from gamecontroller import player_input
from world import World
from room_manager import RoomManager

pygame.init()
clock = pygame.time.Clock()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()

player = Player(screen_width // 2, screen_height // 2, 50, 50)
camera = Camera(screen_width, screen_height)

world = World()
room_manager = RoomManager(world, player, camera)

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            run = False

    # update
    player.update_buffs()
    player_input(player, world.obstacles, world.enemies)
    camera.update(player.rect)

    dt_ms = clock.get_time()
    world.update(dt_ms, player, camera)
    
    if player.health <= 0:
        pygame.quit()

    # etter verden – dørlogikk og rombytte
    room_manager.update()

    # draw
    screen.fill(constants.BLACK)
    world.draw(screen, camera)
    room_manager.draw(screen)  
    player.draw(screen, camera)

    if constants.DEBUG_SHOW_HITBOXES and getattr(player, "debug_attack_rect", None):
        if pygame.time.get_ticks() <= getattr(player, "debug_attack_until", 0):
            r = player.debug_attack_rect
            surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            surf.fill(constants.HITBOX_COLOR_RGBA)
            ar = camera.apply(r)
            screen.blit(surf, (ar.x, ar.y))
        else:
            player.debug_attack_rect = None

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
