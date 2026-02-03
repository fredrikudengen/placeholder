import pygame
import constants
from grid_room import GridRoom
from door import Door
from power_up import Speed_Powerup, Attack_Powerup, Shield_Powerup
from enemy import Enemy
import random
import copy


class RoomManager:
    def __init__(self, world, player, camera):
        self.world = world
        self.player = player
        self.camera = camera

        self.rooms = []
        self.doors = []

        self._build_demo_grid_rooms()
        self.current_room_type = "start"
        self._load_room(self.rooms[self.current_room_type][0])

    def update(self):
        cleared = (len(self.world.enemies) == 0)
        for d in self.doors:
            d.set_open(cleared)
        self._sync_door_blockers()

        if cleared:
            for d in self.doors:
                if self.player.rect.colliderect(d.rect):
                    self._go_to_next_room()
                    break

    def draw(self, screen):
        for d in self.doors:
            d.draw(screen, self.camera)

    def _go_to_next_room(self):
        if self.current_room_type == "reward":
            candidates = self.rooms["combat"]
        else:
            candidates = (
                self.rooms["reward"]
                if random.random() < 0.25
                else self.rooms["combat"]
            )

        nxt = random.choice(candidates)
        self._load_room(nxt)


    def _load_room(self, room):
        self.current_room_type = room
        self.world.clear()
        room.reset_spawns()

        for gy in range(room.rows):
            for gx in range(room.cols):
                if room.terrain[gy][gx] == constants.TILE_WALL:
                    self.world.add_obstacle(room.tile_rect(gx, gy))

        self.doors = []
        for gy in range(room.rows):
            for gx in range(room.cols):
                tag = room.spawns[gy][gx]
                if not tag: 
                    continue
                x, y = gx * constants.TILE_SIZE, gy * constants.TILE_SIZE
                if tag == 'enemy':
                    self.world.add_enemy(x, y)
                elif tag == 'speed_powerup':
                    self.world.add_powerup(Speed_Powerup(x, y, 20))
                elif tag == 'attack_powerup':
                    self.world.add_powerup(Attack_Powerup(x, y, 20))
                elif tag == 'shield_powerup':
                    self.world.add_powerup(Shield_Powerup(x, y, 20))
                elif tag == 'door':
                    drect = pygame.Rect(x, y, constants.TILE_SIZE, constants.TILE_SIZE)
                    self.doors.append(Door(drect))
                room.spawns[gy][gx] = None  # tøm markør

        # 4) Player spawn: finn første floor nær venstre kant (enkelt)
        self.player.rect.topleft = (constants.TILE_SIZE * 2, constants.TILE_SIZE * 2)

        # 5) Lukk dører i starten
        for d in self.doors:
            d.set_open(False)
        self._sync_door_blockers()
        
        self.world.current_room = room


    def _rect_key(self, r: pygame.Rect):
        return (r.x, r.y, r.w, r.h)

    def _sync_door_blockers(self):
        # Fjern alle dør-blockers
        door_keys = {self._rect_key(d.rect) for d in self.doors}
        self.world.obstacles = [
            r for r in self.world.obstacles
            if self._rect_key(r) not in door_keys
        ]
        # Legg til blockers for lukka dører
        existing = {self._rect_key(r) for r in self.world.obstacles}
        for d in self.doors:
            if not d.is_open:
                k = self._rect_key(d.rect)
                if k not in existing:
                    self.world.add_obstacle(d.rect)
                    existing.add(k)

    def _build_demo_grid_rooms(self):
        r1 = GridRoom([
            "###################D##############",
            "#....E.......P..................#",
            "#..###......###.................#",
            "#..#........#...................#",
            "#..###..E...###.................#",
            "D...............................D",
            "#...............................#",
            "#...............................#",
            "#...............................#",
            "#.........................E.....#",
            "#...................E...........#",
            "#################D################",
        ])
        r2 = GridRoom([
            "########################",
            "#D...............E....#",
            "#..######.............#",
            "#..#....#.....P.......#",
            "#..#....#.............#",
            "#..######.............#",
            "########################",
        ])
        r3 = GridRoom([
            "########################",
            "#....E...............D#",
            "#..###......###.......#",
            "#..#........#.........#",
            "#..###......###...P...#",
            "#.....................#",
            "########################",
        ])
        r_start = GridRoom([
            "#####",
            "#...#",
            "#...#",
            "#...#",
            "##D##"
        ])
        r_reward = GridRoom([
            ".......",
            ".......",
            ".......",
            "...D..."
        ])
        self.rooms = {
                "combat": [r1, r2, r3],
                "start":  [r_start],
                "reward": [r_reward]
                }

