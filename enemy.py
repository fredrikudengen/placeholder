import itertools
import random
from heapq import heappush, heappop
from typing import List, Tuple, Optional, Iterable, Any, Dict, Set

import pygame
from pygame.math import Vector2

import constants

from typing import TYPE_CHECKING

from grid_room import GridRoom

class Enemy:
    """
    Enkel fiende-AI med tilstander, subpiksel-bevegelse, micro-wander og A* (neste-steg).

    Public API:
      - move(player, obstacles, room, dt_ms): oppdaterer fienden ett frame.
      - apply_separation(others, strength=..., radius=...): myk dytting for å redusere overlapping.
      - draw(screen, camera): tegn fienden (inkl. valgfri debug-hitbox).
      - Felter som andre systemer leser: rect, alive, health, state.

    Alt som starter med '_' regnes som internt og kan endres uten varsel.
    """

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        """
        Opprett fiende.

        Args:
            x, y: startposisjon (piksel, øverste-venstre i rect)
            width, height: størrelse på collider/tegning
        """
        self.rect = pygame.Rect(x, y, width, height)
        # Sann posisjon i float (senter), brukes til all bevegelse
        self.pos: Vector2 = Vector2(self.rect.center)

        # Combat & status
        self.health: int = constants.ENEMY_HEALTH
        self.alive: bool = constants.ALIVE
        self.hit: bool = False                 # settes utenfra når fienden treffes denne framen
        self.hit_this_frame: bool = False      # (ikke brukt her, men beholdes for kompatibilitet)
        self.hit_timer: Optional[int] = None   # i-frames slutt-tid (ms tick)

        # Tilstandsmaske
        # Mulige states: "idle" | "chase" | "search" | "attack" | "hurt" | "dead"
        self.state: str = "idle"
        self.last_seen_pos: Optional[Tuple[int, int]] = None  # pikselpos hvor spilleren sist ble sett
        self.search_started: Optional[int] = None             # ms tick når search startet
        self.attack_cooldown_until: int = 0                   # ms tick før neste angrep er lov

        # Debug-vis av angrepshitbox
        self.debug_attack_rect: Optional[pygame.Rect] = None
        self.debug_attack_until: int = 0

        # Micro-wander (små tilfeldige steg når idle)
        self.wander_goal_g: Optional[Tuple[int, int]] = None
        now = pygame.time.get_ticks()
        self.next_wander_at: int = now + random.randint(1200, 2500)
        self.WANDER_INTERVAL_MS = constants.ENEMY_WANDER_INTERVAL_MS
        self.WANDER_RADIUS_TILES = constants.ENEMY_WANDER_RADIUS_TILES

    # ------------------------- PUBLIC API -------------------------

    def move(
        self,
        player: Any,
        obstacles: Iterable[pygame.Rect],
        room: GridRoom,
        dt_ms: int,
    ) -> None:
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
        if self.hit_timer and (now - self.hit_timer > 500):  # 0.5s i-frames
            self.hit_timer = None

        # Sansing: avstand + line of sight (LOS)
        player_center: Tuple[int, int] = player.rect.center
        enemy_center: Tuple[int, int] = (int(round(self.pos.x)), int(round(self.pos.y)))
        see_player = False
        if self._dist2(player_center, enemy_center) <= constants.DETECTION_RADIUS * constants.DETECTION_RADIUS:
            T = constants.TILE_SIZE
            gx0, gy0 = int(self.pos.x) // T, int(self.pos.y) // T
            gx1, gy1 = player.rect.centerx // T, player.rect.centery // T
            if self._has_los(room, gx0, gy0, gx1, gy1):
                see_player = True
                self.last_seen_pos = player_center
                self.search_started = None

        # ---------------- State-maskin ----------------
        if self.state in ("idle", "walk", "hurt"):
            if see_player:
                self.state = "chase"
            else:
                # Micro-wander: korte, sjeldne forflytninger på grid
                if self.wander_goal_g is not None:
                    next_tile_g = self._micro_wander(room, self.wander_goal_g, self.WANDER_RADIUS_TILES)
                    if next_tile_g:
                        target_px = self._center_of_tile(*next_tile_g)
                        reached = self._move_towards(target_px, obstacles, dt_ms)
                    else:
                        reached = True  # ga opp denne runden

                    gx, gy = self._grid_pos()
                    if reached or (gx, gy) == self.wander_goal_g:
                        self.wander_goal_g = None
                        wait = random.randint(*self.WANDER_INTERVAL_MS)
                        self.next_wander_at = now + wait
                elif now >= self.next_wander_at:
                    start_g = self._grid_pos()
                    goal = self._pick_random_free_tile(room, start_g, self.WANDER_RADIUS_TILES)
                    if goal and goal != start_g:
                        self.wander_goal_g = goal
                    else:
                        # prøv igjen senere hvis vi ikke fant noe
                        wait = random.randint(*self.WANDER_INTERVAL_MS)
                        self.next_wander_at = now + wait

        elif self.state == "chase":
            # mist LOS → over i search (med siste kjente pos), ellers jag direkte
            self.wander_goal_g = None
            if see_player:
                self._move_towards(player_center, obstacles, dt_ms)

                # Én samlet attack-sjekk
                if now >= self.attack_cooldown_until and \
                   self._dist2(player_center, enemy_center) <= constants.ATTACK_RANGE * constants.ATTACK_RANGE:
                    self.state = "attack"
                    self.attack_cooldown_until = now + constants.ATTACK_COOLDOWN
                    self._spawn_debug_attack_rect_towards(player_center)
            else:
                if self.last_seen_pos:
                    self.state = "search"
                    self.search_started = now
                else:
                    self.state = "idle"

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

        elif self.state == "attack":
            # Plass for faktisk skade/hitbox-kollisjon mot player.rect
            self.state = "chase" if see_player else "idle"

        elif self.state == "dead":
            return
        
    def draw(self, screen: pygame.Surface, camera: Any) -> None:
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

        # valgfri debug-hitbox for angrep
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

    def _dist2(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        """Euklidsk distanse."""
        dx, dy = a[0] - b[0], a[1] - b[1]
        return dx * dx + dy * dy

    def _has_los(
        self,
        room: GridRoom,
        x0: int,
        y0: int,
        x1: int,
        y1: int
    ) -> bool:
        """
        Line-of-sight på GRID ved Bresenham.
        room.is_blocked(gx, gy) må finnes.
        (x0,y0) og (x1,y1) er grid-koordinater (ikke piksler).
        """
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy  # 'feil'

        x, y = x0, y0
        while True:
            # hopp gjerne over startcella hvis du ikke vil at egen celle skal blokkere:
            if (x, y) != (x0, y0) and room.is_blocked(x, y):
                return False
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy
        return True


    def _sync_rect_from_pos(self) -> None:
        """Synkroniser heltalls-rect fra float-posisjon (senter)."""
        self.rect.centerx = int(round(self.pos.x))
        self.rect.centery = int(round(self.pos.y))

    def _slide_move(
        self,
        vx: float,
        vy: float,
        dt_ms: int,
        obstacles: Iterable[pygame.Rect]
    ) -> None:
        """
        Bevegelse med subpiksel-presisjon og 'slide' langs vegger.

        Flytt X, sjekk kollisjon (reverter hvis treff), deretter Y.

        Args:
            vx, vy: hastighet i piksler/sekund
            dt_ms: millisekunder siden forrige frame
            obstacles: vegger for kollisjon
        """
        dt = dt_ms / 1000.0

        # X-aksen
        if vx:
            self.pos.x += vx * dt
            self._sync_rect_from_pos()
            if self.check_collision(obstacles):
                self.pos.x -= vx * dt
                self._sync_rect_from_pos()

        # Y-aksen
        if vy:
            self.pos.y += vy * dt
            self._sync_rect_from_pos()
            if self.check_collision(obstacles):
                self.pos.y -= vy * dt
                self._sync_rect_from_pos()

    def _move_towards(
        self,
        target_px: Tuple[float, float],
        obstacles: Iterable[pygame.Rect],
        dt_ms: int
    ) -> bool:
        """
        Gå mot en piksel-posisjon med normalisert fart.

        Returnerer:
            True hvis vi er 'nær nok' målet (≤ 24 px), ellers False.
        """
        direction = Vector2(target_px[0] - self.pos.x, target_px[1] - self.pos.y)
        dist = direction.length()
        if dist > 1e-6:
            direction /= dist  # normaliser
            speed = constants.ENEMY_SPEED  # px/s
            self._slide_move(direction.x * speed, direction.y * speed, dt_ms, obstacles)
        return self._dist2((int(self.pos.x), int(self.pos.y)), (int(target_px[0]), int(target_px[1]))) <= (24 * 24)
    
    def _apply_separation(
        self,
        others: Iterable["Enemy"],
        strength: float = 0.4,
        radius: int = 40
    ) -> None:
        """
        Myk, lokal dytting bort fra andre fiender for å redusere overlapping.

        Args:
            others: andre Enemy-objekter i nærheten
            strength: skalering av dytt (0..1 typisk)
            radius: påvirkningsradius (px)
        """
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

    def _grid_pos(self) -> Tuple[int, int]:
        """Returner nåværende grid-posisjon (gx, gy) basert på TILE_SIZE og self.pos."""
        T = constants.TILE_SIZE
        return (int(self.pos.x) // T, int(self.pos.y) // T)

    def _center_of_tile(self, gx: int, gy: int) -> Tuple[int, int]:
        """Returner piksel-senteret til grid-ruten (gx, gy)."""
        T = constants.TILE_SIZE
        return (gx * T + T // 2, gy * T + T // 2)

    def _pick_random_free_tile(
        self,
        room: "GridRoom",
        center_g: Tuple[int, int],
        radius: int,
        tries: int = 24
    ) -> Optional[Tuple[int, int]]:
        """
        Velg en tilfeldig ledig grid-rute innenfor radius.

        Returnerer (gx, gy) eller None om vi ikke fant noe på 'tries' forsøk.
        """
        cx, cy = center_g
        for _ in range(tries):
            nx = cx + random.randint(-radius, radius)
            ny = cy + random.randint(-radius, radius)
            if not room.is_blocked(nx, ny):
                return (nx, ny)
        return None

    def _micro_wander(
        self,
        room: "GridRoom",
        goal_g: Tuple[int, int],
        max_depth: int
    ) -> Optional[Tuple[int, int]]:
        """
        BFS: finn NESTE grid-steg fra nåværende pos mot goal_g (billig og robust).

        Brukes til micro-wander. For større kart: bruk A*.
        """
        from collections import deque

        start = self._grid_pos()
        if start == goal_g:
            return None

        q = deque([start])
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        depth: Dict[Tuple[int, int], int] = {start: 0}
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

    def _astar_next_step(
        self,
        room: "GridRoom",
        goal_g: Tuple[int, int],
        max_expansions: int = 512
    ) -> Optional[Tuple[int, int]]:
        """
        A*: finn NESTE grid-steg fra nåværende pos mot goal_g (raskere enn BFS på store kart).

        Returnerer (gx, gy) for neste steg, eller None hvis ingen rute.
        """
        start = self._grid_pos()
        if start == goal_g:
            return None

        def h(a: Tuple[int, int], b: Tuple[int, int]) -> int:
            # Manhattan-heuristikk (4-retninger)
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        openh: List[Tuple[int, int, Tuple[int, int]]] = []
        counter = itertools.count()  # stabil tie-breaker for heap
        g: Dict[Tuple[int, int], int] = {start: 0}
        came: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        heappush(openh, (h(start, goal_g), next(counter), start))

        expansions = 0
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while openh and expansions < max_expansions:
            _, _, cur = heappop(openh)
            expansions += 1

            if cur == goal_g:
                # første steg fra start
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
                ng = g[cur] + 1
                if ng < g.get((nx, ny), 1_000_000_000):
                    g[(nx, ny)] = ng
                    came[(nx, ny)] = cur
                    f = ng + h((nx, ny), goal_g)
                    heappush(openh, (f, next(counter), (nx, ny)))

        return None

    # ------------------------- ENKLE HJELPERE -------------------------

    def _spawn_debug_attack_rect_towards(self, target_px: Tuple[int, int]) -> None:
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

    def check_collision(self, obstacles: Iterable[pygame.Rect]) -> bool:
        """Returner True hvis self.rect kolliderer med et av obstacles."""
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                return True
        return False
