# colors
BLACK  = (0, 0, 0)
RED    = (255, 0, 0)
GREEN  = (0, 255, 0)
BLUE   = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
ORANGE = (255, 128, 0)

PLAYER_COLOR = (255, 255, 255)

# gameplay – player
PLAYER_SPEED   = 5
PLAYER_DPS     = 1
PLAYER_HEALTH  = 5
ALIVE          = True

# gameplay – enemy
ENEMY_SPEED        = 2
ENEMY_HEALTH       = 3
DETECTION_RADIUS   = 350          # px
LOSE_SIGHT_TIME    = 1200         # ms i search før patrol
ATTACK_RANGE       = 40           # px (nærkamp)
ATTACK_COOLDOWN    = 500          # ms

# buffs (varighets-tabell)
BUFF_DURATIONS = {
    'speed_boost':  5000,  # 5s
    'attack_boost': 7000,  # 7s
    'shield_boost': 10000, # 10s
}

# constants.py
TILE_SIZE = 64

# terrain tiles
TILE_FLOOR = 0
TILE_WALL  = 1

# debug
DEBUG_SHOW_HITBOXES = True
DEBUG_HITBOX_MS     = 120   # hvor lenge (ms) et angrep vises
HITBOX_COLOR_RGBA   = (255, 60, 0, 120)   # semi-transparent oransje/rød
HURTBOX_COLOR_RGBA  = (0, 200, 255, 80)   # semi-transparent cyan (om du vil vise hurtbox)

