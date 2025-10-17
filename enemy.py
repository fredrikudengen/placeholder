import itertools
import random
import math
from heapq import heappush, heappop

import pygame
from pygame.math import Vector2
from collections import deque


import constants

class Enemy():
    """
    Enkel fiende-AI med tilstander, subpiksel-bevegelse, micro-wander og A* (neste-steg).

    Public API:
      - move(player, obstacles, room, dt_ms): oppdaterer fienden ett frame.
      - apply_separation(others, strength=..., radius=...): myk dytting for å redusere overlapping.
      - draw(screen, camera): tegn fienden (inkl. valgfri debug-hitbox).
      - Felter som andre systemer leser: rect, alive, health, state.

    Alt som starter med '_' regnes som internt og kan endres uten varsel.
    """

    def __init__(self, x, y, width, height):
        """
        Opprett fiende.

        Args:
            x, y: startposisjon (piksel, øverste-venstre i rect)
            width, height: størrelse på collider/tegning
        """
        self.rect = pygame.Rect(x, y, width, height)
        # Sann posisjon i float (senter), brukes til all bevegelse
        self.pos = Vector2(self.rect.center)
        
        # Combat & status
        self.health = constants.ENEMY_HEALTH
        self.alive = constants.ALIVE
        self.speed = constants.ENEMY_SPEED
        self.dps = constants.ENEMY_DPS
        self.hit = False                 # settes utenfra når fienden treffes denne framen
        self.hit_this_frame = False      # (ikke brukt her, men beholdes for kompatibilitet)
        self.hit_timer = None   # i-frames slutt-tid (ms tick)

        # Tilstandsmaske
        # Mulige states: "idle" | "chase" | "search" | "attack" | "hurt" | "dead"
        self.state = "idle"
        self.last_seen_pos = None  # pikselpos hvor spilleren sist ble sett
        self.search_started = None             # ms tick når search startet
        self.attack_cooldown_until = 0                   # ms tick før neste angrep er lov

        # Debug-vis av angrepshitbox
        self.debug_attack_rect = None
        self.debug_attack_until = 0

        # Micro-wander (små tilfeldige steg når idle)
        self.wander_goal_g = None
        now = pygame.time.get_ticks()
        self.next_wander_at: int = now + random.randint(1200, 2500)
        self.WANDER_INTERVAL_MS = constants.ENEMY_WANDER_INTERVAL_MS
        self.WANDER_RADIUS_TILES = constants.ENEMY_WANDER_RADIUS_TILES

    # ------------------------- PUBLIC API -------------------------

    def move(self, player, obstacles, room, dt_ms):
        """
        Oppdater fienden én frame: sansing, state-maskin, bevegelse, animasjon.

        Args:
            player: objekt med .rect (pygame.Rect)
            obstacles: iterable av vegg-rektangler for kollisjon
            room: GridRoom med is_blocked(...) og TILE_SIZE
            dt_ms: millisekunder siden forrige frame (fra clock.tick)
        """
        now = pygame.time.get_ticks()

        # Død short-circuit
        if self.health <= 0:
            self.alive = False
            self.state = "dead"
            self.wander_goal_g = None
            return

        # Treff / i-frames
        if self.hit:
            self.hit_timer = now
            self.hit = False
            self.state = "hurt"
            
        if self.hit_timer and (now - self.hit_timer > 500):
            self.hit_timer = None

        # Sansing: avstand + line of sight (LOS)
        player_center = player.rect.center
        enemy_center = self.rect.center
        see_player = False
        if self._dist2(*player_center, *enemy_center) <= constants.DETECTION_RADIUS * constants.DETECTION_RADIUS:            
            if self._has_los(room, *self._grid_pos(), *player._grid_pos()):
                see_player = True
                self.last_seen_pos = player_center
                self.search_started = None

        # ---------------- State-maskin ----------------
        if self.state in ("idle", "walk", "hurt"):
            if see_player:
                self.state = "chase"
            else:
                # Micro-wander
                if self.wander_goal_g is not None:
                    next_tile_g = self._micro_wander(room, self.wander_goal_g, self.WANDER_RADIUS_TILES)
                    if next_tile_g:
                        target_px = self._center_of_tile(*next_tile_g)
                        wander_end = self._move_towards(target_px, obstacles, dt_ms)
                    else:
                        wander_end = True  

                    gx, gy = self._grid_pos()
                    
                    if wander_end or (gx, gy) == self.wander_goal_g:
                        self.wander_goal_g = None
                        wait = random.randint(*self.WANDER_INTERVAL_MS)
                        self.next_wander_at = now + wait
                        
                elif now >= self.next_wander_at:
                    start_g = self._grid_pos()
                    goal = self._pick_random_free_tile(room, start_g, self.WANDER_RADIUS_TILES)
                    if goal and goal != start_g:
                        self.wander_goal_g = goal
                    else:
                        wait = random.randint(*self.WANDER_INTERVAL_MS)
                        self.next_wander_at = now + wait

        elif self.state == "chase":
            self.wander_goal_g = None
            if see_player:
                self._move_towards(player_center, obstacles, dt_ms)
                
                if now >= self.attack_cooldown_until and self._dist2(*player_center, *enemy_center) <= constants.ATTACK_RANGE * constants.ATTACK_RANGE:
                    self.state = "attack"
                    self.attack_cooldown_until = now + constants.ATTACK_COOLDOWN
                    self._spawn_debug_attack_rect_towards(player_center)
            else:
                if self.last_seen_pos:
                    self.state = "search"
                    self.search_started = now
                else:
                    self.state = "idle"
                    
        if self.state == "attack":
            player.health -= self.dps
            print("Enemy attacks")
            print(f"DPS: {self.dps}")
            print(f"Player health: {player.health}")
            self.state = "chase"
            self.attack_cooldown_until = now + constants.ATTACK_COOLDOWN

        elif self.state == "search":
            # Gå mot siste kjente posisjon via grid (A* neste-steg)
            if see_player:
                self.state = "chase"
            elif self.last_seen_pos:
                T = constants.TILE_SIZE
                goal_g = (self.last_seen_pos[0] // T, self.last_seen_pos[1] // T)
                next_tile_g = self._astar_next_step(room, goal_g, max_expansions=512)
                if next_tile_g:
                    target_px = self._center_of_tile(*next_tile_g)
                    reached = self._move_towards(target_px, obstacles, dt_ms)
                else:
                    # fallback: forsøk rett mot pikselpos (kan kile, men holder ting i bevegelse)
                    reached = self._move_towards(self.last_seen_pos, obstacles, dt_ms)

                timedout = self.search_started and (now - self.search_started > constants.LOSE_SIGHT_TIME)
                if reached or timedout:
                    self.state = "idle"
                    self.last_seen_pos = None
                    self.search_started = None   
            else:
                self.state = "idle"

        elif self.state == "dead":
            return
        
    def draw(self, screen, camera):
        """
        Tegn fienden og (valgfritt) en semitransparent debug-hitbox for angrep.

        Args:
            screen: pygame-surface
            camera: objekt med .apply(rect) -> rect (for world->screen transform)
        """
        draw_rect = camera.apply(self.rect)

        # enkel fargekode per state (nyttig for debugging/lesbarhet)
        if self.state == "idle":    color = (0, 180, 0)
        elif self.state == "chase": color = (80, 220, 80)
        elif self.state == "search":color = (200, 200, 0)
        elif self.state == "attack":color = (255, 120, 0)
        elif self.state == "hurt":  color = (255, 0, 0)
        elif self.state == "dead":  color = (100, 100, 100)
        else:                       color = constants.GREEN

        pygame.draw.rect(screen, color, draw_rect)

        if constants.DEBUG_SHOW_HITBOXES and self.debug_attack_rect:
            if pygame.time.get_ticks() <= self.debug_attack_until:
                surf = pygame.Surface(
                    (self.debug_attack_rect.width, self.debug_attack_rect.height),
                    pygame.SRCALPHA
                )
                surf.fill(constants.HITBOX_COLOR_RGBA)
                ar = camera.apply(self.debug_attack_rect)
                screen.blit(surf, (ar.x, ar.y))
            else:
                self.debug_attack_rect = None

    # ------------------------- INTERN LOGIKK -------------------------
    
    def _has_los(self, room, enemy_x, enemy_y, player_x, player_y):
        """
        Line-of-sight på GRID (Bresenham).
        Alle koordinater er grid (tiles), ikke piksler.
        Returnerer True hvis linjen fra (enemy_x, enemy_y) til (player_x, player_y)
        ikke passerer noen blokkerte tiles.
        """
        dx = abs(player_x - enemy_x)
        dy = -abs(player_y - enemy_y)
        x_steps = 1 if enemy_x < player_x else -1
        y_steps = 1 if enemy_y < player_y else -1
        err = dx + dy

        x, y = enemy_x, enemy_y
        while True:
            if (x, y) != (enemy_x, enemy_y) and room.is_blocked(x, y):
                return False
            if x == player_x and y == player_y:
                return True 
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += x_steps
            if e2 <= dx:
                err += dx
                y += y_steps
                
    def _grid_pos(self):
        """Returner grid-koordinat (gx, gy) basert på TILE_SIZE."""
        T = constants.TILE_SIZE
        return (int(self.pos.x) // T, int(self.pos.y) // T)

    def _sync_rect_from_pos(self) -> None:
        """Synkroniser heltalls-rect fra float-posisjon (senter)."""
        self.rect.centerx = int(round(self.pos.x))
        self.rect.centery = int(round(self.pos.y))

    def _dist2(self, a1: int, a2: int, b1: int, b2: int) -> int:
        """Euklidisk distanse."""
        dx, dy = a1 - b1, a2 - b2
        return dx * dx + dy * dy

    def _center_of_tile(self, gx, gy):
        """Returner piksel-senteret til grid-ruten (gx, gy)."""
        T = constants.TILE_SIZE
        return (gx * T + T // 2, gy * T + T // 2)

    def check_collision(self, obstacles):
        """Returner True hvis self.rect kolliderer med et av obstacles."""
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                return True
        return False

    def _slide_move(self, vx, vy, dt_ms, obstacles):
        dt = dt_ms / 1000.0
        dx_total = vx * dt
        dy_total = vy * dt

        steps = max(1, int(max(abs(dx_total), abs(dy_total)) // 4) )  # maks ~4 px per steg
        sdx = dx_total / steps
        sdy = dy_total / steps

        for _ in range(steps):
            if sdx:
                self.pos.x += sdx
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.x -= sdx
                    self._sync_rect_from_pos()
                    # ev. snap + EPS her

            if sdy:
                self.pos.y += sdy
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.y -= sdy
                    self._sync_rect_from_pos()
                    # ev. snap + EPS her

    def _move_towards(self, target_px, obstacles, dt_ms):
        """
        Gå mot en piksel-posisjon med normalisert fart.

        Returnerer:
            True hvis vi er 'nær nok' målet (≤ 24 px), ellers False.
        """
        direction = Vector2(target_px[0] - self.pos.x, target_px[1] - self.pos.y)
        dist = direction.length()
        if dist > 1e-6:
            direction /= dist  # normaliser
            self._slide_move(direction.x * self.speed, direction.y * self.speed, dt_ms, obstacles)
        return self._dist2(int(self.pos.x), int(self.pos.y), int(target_px[0]), int(target_px[1])) <= (24 * 24)
    
    def _apply_separation(self, others):
        """
        Myk, lokal dytting bort fra andre fiender for å redusere overlapping.

        Args:
            others: andre Enemy-objekter i nærheten
            strength: skalering av dytt (0..1 typisk)
            radius: påvirkningsradius (px)
        """
        strength=0.08
        radius=64
        self_x, self_y = self.pos.x, self.pos.y
        pushx = pushy = 0.0
        r2 = float(radius * radius)

        for other in others:
            if other is self or not other.alive:
                continue
            other_x, other_y = other.pos.x, other.pos.y
            distance_x, distance_y = self_x - other_x, self_y - other_y
            distance2 = distance_x * distance_x + distance_y * distance_y
            if 0 < distance2 < r2:
                weight = 1.0 / max(1.0, distance2)
                pushx += distance_x * weight
                pushy += distance_y * weight

        # liten flytt (float) + sync for smooth effekt
        self.pos.x += pushx * strength
        self.pos.y += pushy * strength
        self._sync_rect_from_pos()

    # ---- Grid-hjelpere ----

    def _pick_random_free_tile(self, room, center_g, radius):
        """
        Velg en tilfeldig ledig grid-rute innenfor radius.

        Returnerer (gx, gy) eller None om vi ikke fant noe på 'tries' forsøk.
        """
        tries = 7
        cx, cy = center_g
        for _ in range(tries):
            nx = cx + random.randint(-radius, radius)
            ny = cy + random.randint(-radius, radius)
            if not room.is_blocked(nx, ny):
                return (nx, ny)
        return None

    def _micro_wander(self, room, goal_g, max_depth):
        """
        BFS: finn NESTE grid-steg fra nåværende pos mot goal_g (billig og robust).

        Brukes til micro-wander. For større kart: bruk A*.
        """
        start = self._grid_pos()
        if start == goal_g:
            return None

        q = deque([start])
        came_from = {start: None}
        depth = {start: 0}
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while q:
            x, y = q.popleft()
            if (x, y) == goal_g:
                # rekonstruksjon av første steg
                cur = (x, y)
                prev = came_from[cur]
                while prev and prev != start:
                    cur = prev
                    prev = came_from[cur]
                return cur

            if depth[(x, y)] >= max_depth:
                continue

            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if (nx, ny) in came_from:
                    continue
                if room.is_blocked(nx, ny):
                    continue
                came_from[(nx, ny)] = (x, y)
                depth[(nx, ny)] = depth[(x, y)] + 1
                q.append((nx, ny))

        return None

    def _astar_next_step(self, room, goal_g, max_expansions):
        """
        A*: finn NESTE grid-steg fra nåværende pos mot goal_g (4-retninger).
        Returnerer (gx, gy) for neste steg, eller None hvis ingen rute.
        """
        start = self._grid_pos()
        if start == goal_g:
            return None
        # tidlig ut: ulovlige mål
        if room.is_blocked(*goal_g) or room.is_blocked(*start):
            return None

        def h(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        openh = []
        counter = itertools.count()
        g = {start: 0}
        came = {start: None}
        # f = g + h + liten h-vekt for penere tie-break
        f0 = 0 + h(start, goal_g) + 1e-6 * h(start, goal_g)
        heappush(openh, (f0, next(counter), start))

        closed = set()
        expansions = 0
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]

        # track best-so-far for fallback
        best_node = start
        best_f = f0

        while openh and expansions < max_expansions:
            fcur, _, cur = heappop(openh)
            if cur in closed:
                continue
            closed.add(cur)
            expansions += 1

            if fcur < best_f:
                best_f, best_node = fcur, cur

            # reconstruct hvis vi nådde mål
            if cur == goal_g:
                node = cur
                prev = came[node]
                while prev and prev != start:
                    node = prev
                    prev = came[node]
                return node

            cx, cy = cur
            for dx, dy in dirs:
                nx, ny = cx + dx, cy + dy
                if room.is_blocked(nx, ny):
                    continue

                # short-circuit: nabo er mål → finn første steg og returner
                if (nx, ny) == goal_g:
                    # første steg fra start ligger i 'cur' hvis start nabo er cur, ellers gå ett steg tilbake
                    node = (nx, ny)
                    prev = cur
                    while prev and prev != start:
                        node = prev
                        prev = came[prev]
                    return node

                ng = g[cur] + 1
                if ng < g.get((nx, ny), math.inf):
                    g[(nx, ny)] = ng
                    came[(nx, ny)] = cur
                    fh = ng + h((nx, ny), goal_g)
                    f = fh + 1e-6 * h((nx, ny), goal_g)
                    heappush(openh, (f, next(counter), (nx, ny)))

        # Fallback: gå mot best-so-far hvis den ikke er start
        if best_node != start:
            node = best_node
            prev = came[node]
            while prev and prev != start:
                node = prev
                prev = came[node]
            return node

        return None

    # ------------------------- ENKLE HJELPERE -------------------------

    def _spawn_debug_attack_rect_towards(self, target_px):
        """Lag en enkel angreps-rect i retning mål for visuell debugging."""
        ex, ey, ew, eh = self.rect
        ecx, ecy = self.rect.center
        dx = target_px[0] - ecx
        dy = target_px[1] - ecy

        if abs(dx) >= abs(dy):
            # horisontal 'swing'
            atk = pygame.Rect(ex + (ew if dx >= 0 else -ew), ey, ew, eh)
        else:
            # vertikal 'swing'
            atk = pygame.Rect(ex, ey + (eh if dy >= 0 else -eh), ew, eh)

        if constants.DEBUG_SHOW_HITBOXES:
            self.debug_attack_rect = atk
            self.debug_attack_until = pygame.time.get_ticks() + constants.DEBUG_HITBOX_MS
