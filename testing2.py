import math
import random
import sys
import pygame
import pygame.gfxdraw

# -----------------------------
# Constants
# -----------------------------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 900
FPS = 60
ROAD_WIDTH = 420
ROAD_BORDER = 80
LANE_COUNT = 8
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT
LINE_HEIGHT = 40
PLAYER_WIDTH = 80
PLAYER_HEIGHT = 130
ENEMY_WIDTH = 80
ENEMY_HEIGHT = 130
SPAWN_INTERVAL = 1100

# Colors
COLOR_SKY_TOP = (8, 12, 28)
COLOR_SKY_BOT = (18, 30, 60)
COLOR_GRASS_A = (15, 55, 25)
COLOR_GRASS_B = (22, 75, 35)
COLOR_ROAD = (28, 28, 32)
COLOR_ROAD_LINE = (60, 60, 68)
COLOR_CURB_A = (220, 60, 60)
COLOR_CURB_B = (240, 240, 240)
COLOR_LANE = (200, 200, 210)
COLOR_LANE_DIM = (80, 80, 90)
COLOR_TEXT = (230, 240, 255)
COLOR_ACCENT = (255, 210, 40)
COLOR_ACCENT2 = (80, 200, 255)
COLOR_PANEL_BG = (10, 14, 30, 200)

# Player car palette
PLAYER_BODY = (220, 30, 60)
PLAYER_ROOF = (180, 20, 45)
PLAYER_GLASS = (120, 190, 255)
PLAYER_GLASS_SHEEN = (200, 230, 255)
PLAYER_WHEEL = (20, 20, 24)
PLAYER_RIM = (160, 160, 175)
PLAYER_HEADLIGHT = (255, 245, 180)
PLAYER_TAILLIGHT = (255, 60, 60)

# Enemy car palettes (multiple)
ENEMY_PALETTES = [
    ((30, 140, 210), (20, 100, 170), (120, 190, 255)),   # blue
    ((30, 170, 100), (20, 120, 70),  (140, 230, 180)),   # green
    ((180, 120, 20), (140, 90, 10),  (255, 210, 100)),   # gold
    ((120, 40, 200), (80, 20, 160),  (200, 140, 255)),   # purple
    ((200, 80, 20), (160, 50, 10),   (255, 160, 80)),    # orange
]

# -----------------------------
# Utility
# -----------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def lerp(a, b, t):
    return a + (b - a) * t

def alpha_surface(w, h, color, alpha):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((*color[:3], alpha))
    return s

def draw_text(surface, text, size, x, y, color=COLOR_TEXT, center=False, shadow=True, font_name=None):
    font = pygame.font.SysFont(font_name or "Consolas", size, bold=True)
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        sr = sh.get_rect()
        if center:
            sr.center = (x + 2, y + 2)
        else:
            sr.topleft = (x + 2, y + 2)
        surface.blit(sh, sr)
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)

def glow_circle(surface, color, pos, radius, layers=6):
    for i in range(layers, 0, -1):
        alpha = int(55 * (i / layers))
        r = radius + (layers - i) * 4
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha), (r, r), r)
        surface.blit(s, (pos[0] - r, pos[1] - r))

def glow_rect(surface, color, rect, radius=8, layers=5):
    for i in range(layers, 0, -1):
        alpha = int(60 * (i / layers))
        exp = (layers - i) * 3
        r = pygame.Rect(rect.x - exp, rect.y - exp, rect.width + exp * 2, rect.height + exp * 2)
        s = pygame.Surface((r.width + radius * 2, r.height + radius * 2), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (radius, radius, r.width, r.height), border_radius=radius)
        surface.blit(s, (r.x - radius, r.y - radius))

# -----------------------------
# Particle System
# -----------------------------
class Particle:
    def __init__(self, x, y, vx, vy, color, life, size=3):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12  # gravity
        self.life -= 1

    def draw(self, surface):
        t = self.life / self.max_life
        alpha = int(255 * t)
        size = max(1, int(self.size * t))
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color[:3], alpha), (size, size), size)
        surface.blit(s, (int(self.x) - size, int(self.y) - size))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_exhaust(self, x, y, speed):
        for _ in range(2):
            vx = random.uniform(-1.0, 1.0)
            vy = random.uniform(1.5, 3.5) + speed * 0.2
            color = random.choice([(180, 180, 200), (120, 120, 140), (200, 200, 220)])
            self.particles.append(Particle(x + random.uniform(-6, 6), y, vx, vy, color, random.randint(18, 32), random.uniform(2, 5)))

    def emit_sparks(self, x, y, count=18):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 9)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice([(255, 220, 60), (255, 140, 30), (255, 80, 30), (255, 255, 200)])
            self.particles.append(Particle(x, y, vx, vy, color, random.randint(22, 40), random.uniform(2, 5)))

    def emit_debris(self, x, y):
        for _ in range(10):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 2
            color = random.choice([(180, 60, 60), (120, 30, 30), (200, 200, 200), (80, 80, 100)])
            self.particles.append(Particle(x, y, vx, vy, color, random.randint(30, 55), random.uniform(3, 7)))

    def update(self):
        for p in self.particles:
            p.update(1)
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)


# -----------------------------
# Road
# -----------------------------
class Road:
    def __init__(self, screen):
        self.screen = screen
        self.offset = 0
        self.curb_offset = 0
        self._bg = self._make_bg()

    def _make_bg(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        # Sky gradient
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(lerp(COLOR_SKY_TOP[0], COLOR_SKY_BOT[0], t))
            g = int(lerp(COLOR_SKY_TOP[1], COLOR_SKY_BOT[1], t))
            b = int(lerp(COLOR_SKY_TOP[2], COLOR_SKY_BOT[2], t))
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        road_x = (SCREEN_WIDTH - ROAD_WIDTH) // 2

        # Grass
        for side in [(0, road_x - ROAD_BORDER), (road_x + ROAD_WIDTH + ROAD_BORDER, SCREEN_WIDTH)]:
            for y in range(SCREEN_HEIGHT):
                t = y / SCREEN_HEIGHT
                r = int(lerp(COLOR_GRASS_A[0], COLOR_GRASS_B[0], t))
                g = int(lerp(COLOR_GRASS_A[1], COLOR_GRASS_B[1], t))
                b = int(lerp(COLOR_GRASS_A[2], COLOR_GRASS_B[2], t))
                pygame.draw.line(surf, (r, g, b), (side[0], y), (side[1], y))

        # Grass texture dots
        for side_x, side_w in [(0, road_x - ROAD_BORDER), (road_x + ROAD_WIDTH + ROAD_BORDER, SCREEN_WIDTH)]:
            for _ in range(2000):
                x = random.randint(side_x, side_w)
                y = random.randint(0, SCREEN_HEIGHT)
                c = random.choice([(25, 90, 40), (18, 60, 28), (40, 110, 55), (12, 45, 20)])
                pygame.draw.circle(surf, c, (x, y), random.randint(1, 3))

        # Road surface
        pygame.draw.rect(surf, COLOR_ROAD, (road_x - ROAD_BORDER, 0, ROAD_WIDTH + ROAD_BORDER * 2, SCREEN_HEIGHT))
        # Road subtle gradient overlay
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            alpha = int(20 * (1 - t))
            pygame.draw.line(surf, (255, 255, 255), (road_x - ROAD_BORDER, y), (road_x + ROAD_WIDTH + ROAD_BORDER, y))

        # Road noise
        for _ in range(3000):
            x = random.randint(road_x - ROAD_BORDER, road_x + ROAD_WIDTH + ROAD_BORDER)
            y = random.randint(0, SCREEN_HEIGHT)
            shade = random.randint(22, 40)
            surf.set_at((x, y), (shade, shade, shade + 4))

        # Edge shadows on road
        for i in range(30):
            alpha = int(80 * (1 - i / 30))
            pygame.draw.line(surf, (0, 0, 0), (road_x - ROAD_BORDER + i, 0), (road_x - ROAD_BORDER + i, SCREEN_HEIGHT))
            pygame.draw.line(surf, (0, 0, 0), (road_x + ROAD_WIDTH + ROAD_BORDER - i, 0), (road_x + ROAD_WIDTH + ROAD_BORDER - i, SCREEN_HEIGHT))

        return surf

    def update(self, speed):
        self.offset = (self.offset + speed * 0.7) % (LINE_HEIGHT * 2)
        self.curb_offset = (self.curb_offset + speed * 0.7) % 32

    def draw(self):
        self.screen.blit(self._bg, (0, 0))
        road_x = (SCREEN_WIDTH - ROAD_WIDTH) // 2

        # Animated curb stripes
        stripe_h = 16
        for side_x in [road_x - ROAD_BORDER, road_x + ROAD_WIDTH]:
            y = -stripe_h + self.curb_offset
            toggle = 0
            while y < SCREEN_HEIGHT + stripe_h:
                color = COLOR_CURB_A if toggle % 2 == 0 else COLOR_CURB_B
                pygame.draw.rect(self.screen, color, (side_x, int(y), ROAD_BORDER, stripe_h))
                y += stripe_h
                toggle += 1

        # Center road line (faint)
        cx = road_x + ROAD_WIDTH // 2
        for y in range(-LINE_HEIGHT * 2, SCREEN_HEIGHT, LINE_HEIGHT * 2):
            ry = y + self.offset
            pygame.draw.rect(self.screen, COLOR_ROAD_LINE, (cx - 3, ry, 6, LINE_HEIGHT))

        # Lane dashes — animated
        for lane in range(1, LANE_COUNT):
            x = road_x + lane * LANE_WIDTH
            for y in range(-LINE_HEIGHT * 2, SCREEN_HEIGHT, LINE_HEIGHT * 2):
                ry = y + self.offset
                # Glow lane marker
                s = pygame.Surface((14, LINE_HEIGHT), pygame.SRCALPHA)
                s.fill((200, 200, 210, 30))
                self.screen.blit(s, (x - 7, ry))
                pygame.draw.rect(self.screen, COLOR_LANE, (x - 4, ry, 8, LINE_HEIGHT), border_radius=3)

        # Road edge lines
        pygame.draw.line(self.screen, (90, 90, 100), (road_x, 0), (road_x, SCREEN_HEIGHT), 2)
        pygame.draw.line(self.screen, (90, 90, 100), (road_x + ROAD_WIDTH, 0), (road_x + ROAD_WIDTH, SCREEN_HEIGHT), 2)

    @staticmethod
    def lane_center(lane_index):
        road_x = (SCREEN_WIDTH - ROAD_WIDTH) // 2
        return road_x + lane_index * LANE_WIDTH + LANE_WIDTH // 2


# -----------------------------
# Car Drawing
# -----------------------------
def draw_car(surface, cx, cy, w, h, body_color, roof_color, glass_color, glass_sheen,
             wheel_color, rim_color, headlight_color, taillight_color,
             tilt=0, is_player=False, wheel_spin=0):
    """
    Draw a top-down stylized car with detailed shading, wheels, lights, glass.
    cx, cy = center. w, h = half-width, half-height.
    """

    # ---- Shadow ----
    shadow_pts = [
        (cx - w * 0.85 + tilt * 0.5, cy + h * 0.95),
        (cx + w * 0.85 + tilt * 0.5, cy + h * 0.95),
        (cx + w * 0.70 + tilt * 0.5, cy + h + 10),
        (cx - w * 0.70 + tilt * 0.5, cy + h + 10),
    ]
    sh_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(sh_surf, (0, 0, 0, 60), shadow_pts)
    surface.blit(sh_surf, (0, 0))

    # ---- Body ----
    body_pts = [
        (cx - w * 0.70, cy - h * 0.92),   # front-left
        (cx + w * 0.70, cy - h * 0.92),   # front-right
        (cx + w * 0.85, cy - h * 0.35),   # shoulder-right
        (cx + w * 0.92, cy + h * 0.20),   # mid-right
        (cx + w * 0.78, cy + h * 0.80),   # rear-right
        (cx - w * 0.78, cy + h * 0.80),   # rear-left
        (cx - w * 0.92, cy + h * 0.20),   # mid-left
        (cx - w * 0.85, cy - h * 0.35),   # shoulder-left
    ]
    pygame.draw.polygon(surface, body_color, body_pts)
    # Body sheen highlight
    highlight_pts = [
        (cx - w * 0.42, cy - h * 0.88),
        (cx + w * 0.18, cy - h * 0.88),
        (cx + w * 0.08, cy + h * 0.18),
        (cx - w * 0.38, cy + h * 0.18),
    ]
    sh2 = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(sh2, (255, 255, 255, 40), highlight_pts)
    surface.blit(sh2, (0, 0))
    pygame.draw.polygon(surface, (0, 0, 0), body_pts, 2)

    # ---- Hood vents ----
    for i in range(3):
        vent_x = cx - w * 0.32 + i * w * 0.30
        vent_pts = [
            (vent_x - w * 0.08, cy - h * 0.70),
            (vent_x + w * 0.08, cy - h * 0.70),
            (vent_x + w * 0.06, cy - h * 0.50),
            (vent_x - w * 0.06, cy - h * 0.50),
        ]
        pygame.draw.polygon(surface, (20, 20, 20), vent_pts)
        pygame.draw.polygon(surface, (120, 120, 150), vent_pts, 1)

    # ---- Roof / cabin ----
    roof_pts = [
        (cx - w * 0.50, cy - h * 0.55),
        (cx + w * 0.50, cy - h * 0.55),
        (cx + w * 0.62, cy + h * 0.10),
        (cx - w * 0.62, cy + h * 0.10),
    ]
    pygame.draw.polygon(surface, roof_color, roof_pts)
    pygame.draw.polygon(surface, (0, 0, 0), roof_pts, 1)

    # ---- Windshield (front) ----
    ws_pts = [
        (cx - w * 0.46, cy - h * 0.56),
        (cx + w * 0.46, cy - h * 0.56),
        (cx + w * 0.40, cy - h * 0.20),
        (cx - w * 0.40, cy - h * 0.20),
    ]
    pygame.draw.polygon(surface, glass_color, ws_pts)
    sheen_pts = [
        (cx - w * 0.44, cy - h * 0.54),
        (cx + w * 0.08, cy - h * 0.54),
        (cx + w * 0.06, cy - h * 0.24),
        (cx - w * 0.40, cy - h * 0.24),
    ]
    sh3 = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(sh3, (255, 255, 255, 70), sheen_pts)
    surface.blit(sh3, (0, 0))
    pygame.draw.polygon(surface, (0, 0, 0), ws_pts, 1)

    # ---- Rear window ----
    rw_pts = [
        (cx - w * 0.42, cy + h * 0.05),
        (cx + w * 0.42, cy + h * 0.05),
        (cx + w * 0.48, cy + h * 0.32),
        (cx - w * 0.48, cy + h * 0.32),
    ]
    pygame.draw.polygon(surface, glass_color, rw_pts)
    pygame.draw.polygon(surface, (0, 0, 0), rw_pts, 1)

    # ---- Side intakes ----
    intake_colors = [(20, 20, 30), (80, 80, 100)]
    intake_pts = [
        (cx - w * 0.84, cy - h * 0.15),
        (cx - w * 0.94, cy - h * 0.05),
        (cx - w * 0.94, cy + h * 0.15),
        (cx - w * 0.84, cy + h * 0.25),
    ]
    pygame.draw.polygon(surface, intake_colors[0], intake_pts)
    pygame.draw.polygon(surface, intake_colors[1], intake_pts, 1)
    intake_pts = [
        (cx + w * 0.84, cy - h * 0.15),
        (cx + w * 0.94, cy - h * 0.05),
        (cx + w * 0.94, cy + h * 0.15),
        (cx + w * 0.84, cy + h * 0.25),
    ]
    pygame.draw.polygon(surface, intake_colors[0], intake_pts)
    pygame.draw.polygon(surface, intake_colors[1], intake_pts, 1)

    # ---- Headlights ----
    for sign in [-1, 1]:
        hx = int(cx + sign * w * 0.55)
        hy = int(cy - h * 0.84)
        pygame.draw.ellipse(surface, headlight_color, (hx - 9, hy - 5, 18, 10))
        pygame.draw.ellipse(surface, (255, 255, 255), (hx - 9, hy - 5, 18, 10), 1)
        # Glow
        glow_circle(surface, headlight_color, (hx, hy), 10, layers=4)

    # ---- Taillights ----
    for sign in [-1, 1]:
        tx = int(cx + sign * w * 0.62)
        ty = int(cy + h * 0.72)
        pygame.draw.ellipse(surface, taillight_color, (tx - 10, ty - 5, 20, 10))
        pygame.draw.ellipse(surface, (0, 0, 0), (tx - 10, ty - 5, 20, 10), 1)
        if is_player:
            glow_circle(surface, taillight_color, (tx, ty), 11, layers=5)

    # ---- Wheels ----
    wheel_positions = [
        (cx - w * 0.76, cy - h * 0.62),  # front-left
        (cx + w * 0.76, cy - h * 0.62),  # front-right
        (cx - w * 0.76, cy + h * 0.62),  # rear-left
        (cx + w * 0.76, cy + h * 0.62),  # rear-right
    ]
    for wx, wy in wheel_positions:
        wix, wiy = int(wx + tilt * 0.25), int(wy)
        wr = int(w * 0.28)
        pygame.draw.circle(surface, wheel_color, (wix, wiy), wr)
        pygame.draw.circle(surface, (20, 20, 24), (wix, wiy), wr, 3)
        pygame.draw.circle(surface, rim_color, (wix, wiy), int(wr * 0.55))
        for i in range(5):
            angle = wheel_spin + i * (2 * math.pi / 5)
            sx = wix + int(math.cos(angle) * wr * 0.42)
            sy = wiy + int(math.sin(angle) * wr * 0.42)
            pygame.draw.line(surface, (70, 70, 90), (wix, wiy), (sx, sy), 2)
        pygame.draw.circle(surface, (220, 220, 230), (wix, wiy), int(wr * 0.20))


# -----------------------------
# Player
# -----------------------------
class Player:
    def __init__(self):
        start_x = Road.lane_center(LANE_COUNT // 2)
        start_y = SCREEN_HEIGHT - PLAYER_HEIGHT - 40
        self.x = float(start_x)
        self.y = float(start_y)
        self.w = PLAYER_WIDTH // 2
        self.h = PLAYER_HEIGHT // 2
        self.speed = 0.0
        self.max_speed = 14.0
        self.acceleration = 0.38
        self.deceleration = 0.30
        self.friction = 0.16
        self.turn_speed = 5.2
        self.tilt = 0.0
        self.wheel_spin = 0.0
        self.exhaust_timer = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w), int(self.y - self.h), self.w * 2, self.h * 2)

    def update(self, keys, particles):
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed += self.acceleration
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed -= self.deceleration
        else:
            if self.speed > 0:
                self.speed -= self.friction
            elif self.speed < 0:
                self.speed += self.friction
            if abs(self.speed) < 0.05:
                self.speed = 0

        self.speed = clamp(self.speed, -3, self.max_speed)

        turn = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -(self.turn_speed + self.speed * 0.16)
            self.x += dx
            turn = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = (self.turn_speed + self.speed * 0.16)
            self.x += dx
            turn = 1

        self.tilt = lerp(self.tilt, turn * (self.speed * 2), 0.18)

        left_limit = (SCREEN_WIDTH - ROAD_WIDTH) // 2 + self.w + 8
        right_limit = (SCREEN_WIDTH + ROAD_WIDTH) // 2 - self.w - 8
        self.x = clamp(self.x, left_limit, right_limit)

        self.wheel_spin += self.speed * 0.06

        # Exhaust particles
        self.exhaust_timer += 1
        if self.speed > 1 and self.exhaust_timer % 2 == 0:
            ex = self.x
            ey = self.y + self.h
            particles.emit_exhaust(ex - 14, ey, self.speed)
            particles.emit_exhaust(ex + 14, ey, self.speed)

    def draw(self, surface):
        draw_car(surface, self.x, self.y, self.w, self.h,
                 PLAYER_BODY, PLAYER_ROOF, PLAYER_GLASS, PLAYER_GLASS_SHEEN,
                 PLAYER_WHEEL, PLAYER_RIM, PLAYER_HEADLIGHT, PLAYER_TAILLIGHT,
                 tilt=self.tilt, is_player=True, wheel_spin=self.wheel_spin)


# -----------------------------
# Enemy
# -----------------------------
class Enemy:
    def __init__(self, lane, speed):
        self.x = float(Road.lane_center(lane))
        self.y = float(-ENEMY_HEIGHT)
        self.w = ENEMY_WIDTH // 2
        self.h = ENEMY_HEIGHT // 2
        self.speed = speed
        self.palette = random.choice(ENEMY_PALETTES)
        self.wheel_spin = 0.0
        self.tilt = random.uniform(-3, 3)

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w), int(self.y - self.h), self.w * 2, self.h * 2)

    def update(self, game_speed):
        self.y += self.speed + game_speed
        self.wheel_spin -= (self.speed + game_speed) * 0.06

    def off_screen(self):
        return self.y - self.h > SCREEN_HEIGHT + 60

    def draw(self, surface):
        body, roof, glass = self.palette
        draw_car(surface, self.x, self.y, self.w, self.h,
                 body, roof, glass, (200, 230, 255),
                 PLAYER_WHEEL, PLAYER_RIM,
                 (255, 255, 200), (255, 80, 80),
                 tilt=self.tilt, is_player=False, wheel_spin=self.wheel_spin)


# -----------------------------
# HUD
# -----------------------------
class HUD:
    def __init__(self, screen):
        self.screen = screen
        self.speedometer_angle = -150.0
        self._panel = self._make_panel()

    def _make_panel(self):
        s = pygame.Surface((210, 80), pygame.SRCALPHA)
        pygame.draw.rect(s, (10, 14, 30, 180), (0, 0, 210, 80), border_radius=14)
        pygame.draw.rect(s, (80, 120, 200, 60), (0, 0, 210, 80), 2, border_radius=14)
        return s

    def draw(self, score, high_score, speed, level, active):
        if not active:
            return

        # Top-left score panel
        self.screen.blit(self._panel, (14, 14))
        draw_text(self.screen, f"SCORE", 13, 24, 20, COLOR_ACCENT2, shadow=False)
        draw_text(self.screen, f"{int(score):06d}", 26, 24, 34, COLOR_TEXT)
        draw_text(self.screen, f"BEST  {int(high_score):06d}", 14, 24, 64, (160, 180, 220))

        # Top-right level badge
        level_x = SCREEN_WIDTH - 100
        lv_surf = pygame.Surface((86, 44), pygame.SRCALPHA)
        pygame.draw.rect(lv_surf, (10, 14, 30, 180), (0, 0, 86, 44), border_radius=10)
        pygame.draw.rect(lv_surf, (COLOR_ACCENT[0], COLOR_ACCENT[1], COLOR_ACCENT[2], 80), (0, 0, 86, 44), 2, border_radius=10)
        self.screen.blit(lv_surf, (level_x, 14))
        draw_text(self.screen, "LEVEL", 12, level_x + 8, 18, COLOR_ACCENT2, shadow=False)
        draw_text(self.screen, f"{level:02d}", 24, level_x + 30, 28, COLOR_ACCENT)

        # Speedometer (bottom-right)
        self._draw_speedometer(speed)

    def _draw_speedometer(self, speed):
        cx, cy = SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80
        radius = 54

        # Background
        pygame.draw.circle(self.screen, (10, 14, 30), (cx, cy), radius)
        pygame.draw.circle(self.screen, (50, 80, 140), (cx, cy), radius, 2)

        # Tick marks
        for i in range(11):
            angle = math.radians(-210 + i * 24)
            inner = radius - 10
            outer = radius - 4
            x1 = cx + int(math.cos(angle) * inner)
            y1 = cy + int(math.sin(angle) * inner)
            x2 = cx + int(math.cos(angle) * outer)
            y2 = cy + int(math.sin(angle) * outer)
            col = COLOR_ACCENT if i >= 8 else (120, 140, 180)
            pygame.draw.line(self.screen, col, (x1, y1), (x2, y2), 2 if i % 5 == 0 else 1)

        # Needle
        target = -210 + (speed / 14) * 240
        self.speedometer_angle = lerp(self.speedometer_angle, target, 0.12)
        angle = math.radians(self.speedometer_angle)
        nx = cx + int(math.cos(angle) * (radius - 14))
        ny = cy + int(math.sin(angle) * (radius - 14))
        pygame.draw.line(self.screen, COLOR_ACCENT, (cx, cy), (nx, ny), 3)
        pygame.draw.circle(self.screen, (200, 200, 220), (cx, cy), 6)

        # Speed label
        draw_text(self.screen, f"{int(speed * 10)}", 16, cx, cy + 18, COLOR_TEXT, center=True, shadow=False)
        draw_text(self.screen, "km/h", 10, cx, cy + 32, (140, 160, 200), center=True, shadow=False)


# -----------------------------
# Overlay (Menu / Game Over)
# -----------------------------
class Overlay:
    def __init__(self, screen):
        self.screen = screen
        self._stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT // 2),
                        random.uniform(0.5, 2.5)) for _ in range(120)]

    def _draw_stars(self):
        for sx, sy, size in self._stars:
            alpha = random.randint(120, 255)
            pygame.draw.circle(self.screen, (200, 220, 255), (sx, sy), int(size))

    def draw_start(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 8, 20, 210))
        self.screen.blit(overlay, (0, 0))
        self._draw_stars()

        # Title glow
        glow_rect(self.screen, COLOR_ACCENT,
                  pygame.Rect(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 3 - 38, 440, 76),
                  radius=18, layers=7)

        draw_text(self.screen, "NITRO RACER", 58, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, COLOR_ACCENT, center=True)
        draw_text(self.screen, "P  R  O", 22, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 44, (180, 200, 240), center=True)

        # Instruction cards
        for i, (key, desc) in enumerate([("↑ W", "Accelerate"), ("↓ S", "Brake"), ("← A  → D", "Steer")]):
            bx = SCREEN_WIDTH // 2 - 180 + i * 120
            by = SCREEN_HEIGHT // 2 + 20
            card = pygame.Surface((110, 52), pygame.SRCALPHA)
            pygame.draw.rect(card, (20, 30, 60, 180), (0, 0, 110, 52), border_radius=10)
            pygame.draw.rect(card, (80, 120, 200, 80), (0, 0, 110, 52), 1, border_radius=10)
            self.screen.blit(card, (bx - 55, by))
            draw_text(self.screen, key, 18, bx, by + 10, COLOR_ACCENT, center=True, shadow=False)
            draw_text(self.screen, desc, 12, bx, by + 32, (160, 180, 220), center=True, shadow=False)

        # Press SPACE button
        t = pygame.time.get_ticks() / 1000
        pulse = 0.5 + 0.5 * math.sin(t * 3)
        col = (int(lerp(COLOR_ACCENT[0], 255, pulse * 0.4)),
               int(lerp(COLOR_ACCENT[1], 255, pulse * 0.3)),
               int(lerp(COLOR_ACCENT[2], 80, pulse * 0.2)))
        draw_text(self.screen, "[ PRESS SPACE TO START ]", 28, SCREEN_WIDTH // 2,
                  SCREEN_HEIGHT // 2 + 110, col, center=True)

    def draw_gameover(self, score, high_score):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 8, 20, 220))
        self.screen.blit(overlay, (0, 0))

        # Big crash text
        glow_rect(self.screen, (220, 40, 40),
                  pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 3 - 46, 400, 88),
                  radius=18, layers=8)
        draw_text(self.screen, "CRASHED!", 62, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, (255, 80, 80), center=True)

        # Score display
        sc_surf = pygame.Surface((340, 110), pygame.SRCALPHA)
        pygame.draw.rect(sc_surf, (10, 14, 30, 200), (0, 0, 340, 110), border_radius=16)
        pygame.draw.rect(sc_surf, (80, 120, 200, 80), (0, 0, 340, 110), 2, border_radius=16)
        self.screen.blit(sc_surf, (SCREEN_WIDTH // 2 - 170, SCREEN_HEIGHT // 2 - 10))
        draw_text(self.screen, "SCORE", 15, SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2, COLOR_ACCENT2, shadow=False)
        draw_text(self.screen, f"{int(score):06d}", 34, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 8, COLOR_TEXT, center=True)
        is_new = int(score) >= int(high_score)
        draw_text(self.screen, ("★ NEW BEST! ★" if is_new else f"BEST  {int(high_score):06d}"),
                  17, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 48,
                  COLOR_ACCENT if is_new else (140, 160, 200), center=True)

        t = pygame.time.get_ticks() / 1000
        pulse = 0.5 + 0.5 * math.sin(t * 3)
        col = (int(lerp(COLOR_ACCENT[0], 255, pulse * 0.4)),
               int(lerp(COLOR_ACCENT[1], 255, pulse * 0.3)),
               int(lerp(COLOR_ACCENT[2], 80, pulse * 0.2)))
        draw_text(self.screen, "[ PRESS SPACE TO RESTART ]", 26, SCREEN_WIDTH // 2,
                  SCREEN_HEIGHT // 2 + 108, col, center=True)


# -----------------------------
# Game
# -----------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Nitro Racer PRO")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.road = Road(self.screen)
        self.particles = ParticleSystem()
        self.player = Player()
        self.enemies = []
        self.score = 0.0
        self.high_score = 0.0
        self.spawn_timer = 0
        self.running = True
        self.active = False
        self.game_speed = 0.0
        self.level = 1
        self.spawn_delay = SPAWN_INTERVAL
        self.last_level_increase = 0
        self.hud = HUD(self.screen)
        self.overlay = Overlay(self.screen)
        self.crash_flash = 0
        self.screen_shake = 0

    def reset(self):
        self.player = Player()
        self.enemies = []
        self.particles = ParticleSystem()
        self.score = 0.0
        self.game_speed = 0.0
        self.level = 1
        self.spawn_delay = SPAWN_INTERVAL
        self.active = True
        self.spawn_timer = 0
        self.last_level_increase = pygame.time.get_ticks()
        self.crash_flash = 0
        self.screen_shake = 0

    def spawn_enemy(self):
        lane = random.randrange(LANE_COUNT)
        speed = random.uniform(3.5, 6.0 + self.level * 0.25)
        e = Enemy(lane, speed)
        self.enemies.append(e)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if self.active:
            self.player.update(keys, self.particles)
            self.game_speed = clamp(self.player.speed * 0.65, 2.5, 10)
            self.road.update(self.game_speed)
            self.score += self.game_speed * dt * 0.022
            self.particles.update()

            now = pygame.time.get_ticks()
            if now - self.spawn_timer > self.spawn_delay:
                self.spawn_timer = now
                self.spawn_enemy()

            if now - self.last_level_increase > 10000:
                self.last_level_increase = now
                self.level += 1
                self.spawn_delay = max(500, self.spawn_delay - 90)

            for enemy in self.enemies:
                enemy.update(self.game_speed)
            self.enemies = [e for e in self.enemies if not e.off_screen()]

            if self.check_collision():
                self.active = False
                self.high_score = max(self.high_score, self.score)
                self.crash_flash = 18
                self.screen_shake = 22
                # Big crash particles
                px, py = self.player.x, self.player.y
                self.particles.emit_sparks(px, py, 40)
                self.particles.emit_debris(px, py)

            if self.screen_shake > 0:
                self.screen_shake -= 1
            if self.crash_flash > 0:
                self.crash_flash -= 1
        else:
            self.road.update(0)
            self.particles.update()

    def check_collision(self):
        pr = self.player.rect
        # Shrink collision box slightly for fairness
        pr = pr.inflate(-14, -14)
        for enemy in self.enemies:
            er = enemy.rect.inflate(-10, -10)
            if pr.colliderect(er):
                return True
        return False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.active:
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

            self.update(dt)

            # Offset for screen shake
            ox, oy = 0, 0
            if self.screen_shake > 0:
                ox = random.randint(-int(self.screen_shake * 0.5), int(self.screen_shake * 0.5))
                oy = random.randint(-int(self.screen_shake * 0.4), int(self.screen_shake * 0.4))

            draw_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.road.draw()
            self.particles.draw(self.screen)

            # Draw enemies
            for enemy in self.enemies:
                enemy.draw(self.screen)

            # Draw player
            if self.active or self.crash_flash > 0:
                self.player.draw(self.screen)

            # Crash flash
            if self.crash_flash > 0:
                alpha = int(180 * (self.crash_flash / 18))
                fl = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                fl.fill((255, 80, 30, alpha))
                self.screen.blit(fl, (0, 0))

            self.hud.draw(self.score, self.high_score, self.player.speed, self.level, self.active)

            if not self.active:
                if self.score == 0:
                    self.overlay.draw_start()
                else:
                    self.overlay.draw_gameover(self.score, self.high_score)

            # Screen shake: shift everything
            if ox != 0 or oy != 0:
                shifted = self.screen.copy()
                self.screen.fill((0, 0, 0))
                self.screen.blit(shifted, (ox, oy))

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()