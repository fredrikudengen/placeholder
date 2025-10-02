# grid_room.py
import pygame
import constants

CHAR_TO_TILE = {
    '.': constants.TILE_FLOOR,
    '#': constants.TILE_WALL,
}

class GridRoom:
    def __init__(self, lines):
        """
        lines: list[str], like:
        "####################",
        "#......E.......P...#",
        "#..###......###....#",
        "#..#..D.....#......#",
        "#..###......###..E.#",
        "#..................#",
        "####################",
        """
        self.h = len(lines)
        self.w = max(len(row) for row in lines)

        self.terrain = [[constants.TILE_FLOOR for _ in range(self.w)] for _ in range(self.h)]
        self.spawns  = [[None for _ in range(self.w)] for _ in range(self.h)]
        self.doors   = []  # list of (gx, gy)

        for y, row in enumerate(lines):
            for x, ch in enumerate(row):
                if ch in ('.', '#'):
                    self.terrain[y][x] = CHAR_TO_TILE[ch]
                elif ch == 'E':
                    self.terrain[y][x] = constants.TILE_FLOOR
                    self.spawns[y][x] = 'enemy'
                elif ch == 'P':
                    self.terrain[y][x] = constants.TILE_FLOOR
                    self.spawns[y][x] = 'powerup'
                elif ch == 'D':
                    self.terrain[y][x] = constants.TILE_FLOOR
                    self.spawns[y][x] = 'door'

    def is_blocked(self, gx, gy):
        if gx < 0 or gy < 0 or gx >= self.w or gy >= self.h:
            return True
        return self.terrain[gy][gx] == constants.TILE_WALL

    def tile_rect(self, gx, gy):
        x, y = gx * constants.TILE_SIZE, gy * constants.TILE_SIZE
        return pygame.Rect(x, y, constants.TILE_SIZE, constants.TILE_SIZE)
