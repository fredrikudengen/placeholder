import pygame
import constants

class Enemy:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = constants.GREEN

        # Combat & status
        self.health = constants.ENEMY_HEALTH
        self.alive = constants.ALIVE
        self.hit = False
        self.hit_this_frame = False
        self.hit_timer = None

        # State & behavior
        # "patrol" | "chase" | "search" | "attack" | "hurt" | "dead"
        self.state = "patrol"
        self.last_seen_pos = None
        self.search_started = None
        self.attack_cooldown_until = 0

        # Animation
        self.animation_frame = 0
        self.animation_timer = pygame.time.get_ticks()

        # Patrol
        self.waypoints = [(100, 200), (300, 200), (300, 400), (100, 400)]
        self.patrol_index = 0
        
        # Debug attack vis
        self.debug_attack_rect = None
        self.debug_attack_until = 0


    # -------------------------
    # Helpers
    # -------------------------
    def _dist2(self, a, b):
        dx, dy = a[0] - b[0], a[1] - b[1]
        return dx*dx + dy*dy

    def _has_los(self, start, end, obstacles, step=12):
        """Sample langs linjen start->end; stopp om vi treffer et hinder."""
        sx, sy = start
        ex, ey = end
        dx, dy = ex - sx, ey - sy
        L = max(1, int((abs(dx) + abs(dy)) // step))
        for i in range(1, L + 1):
            t = i / L
            x = sx + dx * t
            y = sy + dy * t
            probe = pygame.Rect(x - 2, y - 2, 4, 4)
            for ob in obstacles:
                if probe.colliderect(ob):
                    return False
        return True

    def _slide_move(self, vx, vy, obstacles):
        """Forsøk X, så Y for å 'gli' langs vegger."""
        if vx:
            self.rect.x += vx
            if self.check_collision(obstacles):
                self.rect.x -= vx
        if vy:
            self.rect.y += vy
            if self.check_collision(obstacles):
                self.rect.y -= vy

    def _move_towards(self, target, obstacles):
        """
        Beveg et ENEMY_SPEED-steg mot target (x,y) med slide.
        Returnerer True hvis vi er 'nær nok' (24 px).
        """
        ex, ey = self.rect.center
        tx, ty = target
        vx = constants.ENEMY_SPEED if tx > ex else -constants.ENEMY_SPEED if tx < ex else 0
        vy = constants.ENEMY_SPEED if ty > ey else -constants.ENEMY_SPEED if ty < ey else 0
        self._slide_move(vx, vy, obstacles)
        return self._dist2(self.rect.center, target) <= (24 * 24)

    # -------------------------
    # Public API
    # -------------------------
    def move(self, player, obstacles):
        now = pygame.time.get_ticks()

        # Død?
        if self.health <= 0:
            self.alive = False
            self.state = "dead"
            return

        # Treffer/iframes-håndtering
        if self.hit:
            self.hit_timer = now
            self.hit = False
            self.state = "hurt"

        if self.hit_timer and (now - self.hit_timer > 500):  # 0.5s i-frames
            self.hit_timer = None

        # Sansing
        pc = player.rect.center
        ec = self.rect.center
        see_player = False
        if self._dist2(pc, ec) <= constants.DETECTION_RADIUS * constants.DETECTION_RADIUS:
            if self._has_los(ec, pc, obstacles):
                see_player = True
                self.last_seen_pos = pc
                self.search_started = None

        # State machine
        if self.state in ("idle", "patrol", "walk"):
            if see_player:
                self.state = "chase"
            else:
                self.state = "patrol"
                if self.waypoints:
                    target = self.waypoints[self.patrol_index]
                    if self._move_towards(target, obstacles):
                        self.patrol_index = (self.patrol_index + 1) % len(self.waypoints)

        elif self.state == "chase":
            if see_player:
                vx = constants.ENEMY_SPEED if pc[0] > ec[0] else -constants.ENEMY_SPEED if pc[0] < ec[0] else 0
                vy = constants.ENEMY_SPEED if pc[1] > ec[1] else -constants.ENEMY_SPEED if pc[1] < ec[1] else 0
                self._slide_move(vx, vy, obstacles)

                if now >= self.attack_cooldown_until and \
                   self._dist2(pc, ec) <= constants.ATTACK_RANGE * constants.ATTACK_RANGE:
                    self.state = "attack"
                    self.attack_cooldown_until = now + constants.ATTACK_COOLDOWN
            else:
                if self.last_seen_pos:
                    self.state = "search"
                    self.search_started = now
                else:
                    self.state = "patrol"
                    
            if now >= self.attack_cooldown_until and \
                self._dist2(pc, ec) <= constants.ATTACK_RANGE * constants.ATTACK_RANGE:
                self.state = "attack"
                self.attack_cooldown_until = now + constants.ATTACK_COOLDOWN

                # LAG ENKELT ANGREPSREKTANGEL I RETNING MOT SPILLER (debug)
                ex, ey, ew, eh = self.rect
                dx = pc[0] - ec[0]
                dy = pc[1] - ec[1]
                # prioriter akse med størst absoluttverdi
                if abs(dx) >= abs(dy):
                    # horisontal swing
                    if dx >= 0:
                        atk = pygame.Rect(ex + ew, ey, ew, eh)
                    else:
                        atk = pygame.Rect(ex - ew, ey, ew, eh)
                else:
                    # vertikal swing
                    if dy >= 0:
                        atk = pygame.Rect(ex, ey + eh, ew, eh)
                    else:
                        atk = pygame.Rect(ex, ey - eh, ew, eh)

                if constants.DEBUG_SHOW_HITBOXES:
                    self.debug_attack_rect = atk
                    self.debug_attack_until = now + constants.DEBUG_HITBOX_MS


        elif self.state == "search":
            if see_player:
                self.state = "chase"
            elif self.last_seen_pos:
                reached = self._move_towards(self.last_seen_pos, obstacles)
                timedout = self.search_started and (now - self.search_started > constants.LOSE_SIGHT_TIME)
                if reached or timedout:
                    self.state = "patrol"
                    self.last_seen_pos = None
                    self.search_started = None
            else:
                self.state = "patrol"

        elif self.state == "attack":
            # Her kan du gjøre skade / hitbox-logikk
            self.state = "chase" if see_player else "patrol"

        elif self.state == "hurt":
            # Valgfritt: liten "stun" – vi lar state flyte neste frame
            pass

        elif self.state == "dead":
            return

        # Animasjon
        if now - self.animation_timer > 100:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = now

    def apply_separation(self, others, strength=0.4, radius=40):
        ex, ey = self.rect.center
        pushx = pushy = 0
        r2 = radius * radius
        for o in others:
            if o is self or not o.alive:
                continue
            ox, oy = o.rect.center
            dx, dy = ex - ox, ey - oy
            d2 = dx * dx + dy * dy
            if 0 < d2 < r2:
                inv = 1.0 / max(1, d2)
                pushx += dx * inv
                pushy += dy * inv
        # Ikke sjekk vegger her – separasjon er myk dytting
        self._slide_move(int(pushx * strength), int(pushy * strength), [])

    def check_collision(self, obstacles):
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                return True
        return False

    def draw(self, screen, camera):
        # fiendens egen kropp
        draw_rect = camera.apply(self.rect)
        if self.state == "patrol":   color = (0, 180, 0)
        elif self.state == "chase":  color = (80, 220, 80)
        elif self.state == "search": color = (200, 200, 0)
        elif self.state == "attack": color = (255, 120, 0)
        elif self.state == "hurt":   color = (255, 0, 0)
        elif self.state == "dead":   color = (100, 100, 100)
        else:                        color = constants.GREEN
        pygame.draw.rect(screen, color, draw_rect)

        # DEBUG: tegn fiendens angrepshitbox (kort tid)
        if constants.DEBUG_SHOW_HITBOXES and self.debug_attack_rect:
            if pygame.time.get_ticks() <= self.debug_attack_until:
                # lag en liten surface med alpha, tegn rekt, blit til skjerm
                surf = pygame.Surface((self.debug_attack_rect.width, self.debug_attack_rect.height), pygame.SRCALPHA)
                surf.fill(constants.HITBOX_COLOR_RGBA)
                ar = camera.apply(self.debug_attack_rect)
                screen.blit(surf, (ar.x, ar.y))
            else:
                self.debug_attack_rect = None

