import math
import random
import sys
import pygame

# -----------------------------
# Constants
# -----------------------------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 900
FPS = 60
ROAD_WIDTH = 420
ROAD_BORDER = 80
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT
LINE_HEIGHT = 40
PLAYER_WIDTH = 80
PLAYER_HEIGHT = 200
ENEMY_WIDTH = 80
ENEMY_HEIGHT = 200
SPAWN_INTERVAL = 1100  # milliseconds

# Colors
COLOR_SKY = (43, 89, 144)
COLOR_GRASS = (36, 110, 67)
COLOR_GRASS_LIGHT = (95, 175, 80)
COLOR_GRASS_DARK = (22, 75, 35)
COLOR_ROAD = (56, 56, 56)
COLOR_ROAD_BORDER = (194, 194, 194)
COLOR_SIDEWALK_YELLOW = (255, 204, 0)
COLOR_SIDEWALK_BLACK = (20, 20, 20)
COLOR_LANE = (235, 235, 235)
COLOR_PLAYER = (255, 44, 70)
COLOR_ENEMY = (14, 170, 219)
COLOR_TEXT = (246, 246, 246)
COLOR_ACCENT = (255, 215, 64)
COLOR_SHADOW = (20, 20, 20, 140)

# -----------------------------
# Utility functions
# -----------------------------
def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def draw_text(surface, text, size, x, y, color=COLOR_TEXT, center=False):
    font = pygame.font.SysFont("Arial", size, bold=True)
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)


class Road:
    def __init__(self, screen):
        self.screen = screen
        self.offset = 0
        # Pre-cache grass texture
        self.grass_surface = self._create_grass_texture()

    def _create_grass_texture(self):
        """Create a grass texture pattern once and reuse it"""
        grass_surface = pygame.Surface((ROAD_BORDER, SCREEN_HEIGHT))

        # Base gradient for depth
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(COLOR_GRASS[0] * (1 - t) + COLOR_GRASS_LIGHT[0] * t)
            g = int(COLOR_GRASS[1] * (1 - t) + COLOR_GRASS_LIGHT[1] * t)
            b = int(COLOR_GRASS[2] * (1 - t) + COLOR_GRASS_LIGHT[2] * t)
            pygame.draw.line(grass_surface, (r, g, b), (0, y), (ROAD_BORDER, y))

        # Draw grass blades and tufts
        for _ in range(2800):
            x = random.randint(0, ROAD_BORDER - 1)
            y = random.randint(0, SCREEN_HEIGHT - 1)
            length = random.randint(6, 14)
            angle = random.uniform(-0.5, 0.5)
            blade_color = (
                max(0, min(255, COLOR_GRASS[0] + random.randint(-18, 18))),
                max(0, min(255, COLOR_GRASS[1] + random.randint(-40, 40))),
                max(0, min(255, COLOR_GRASS[2] + random.randint(-18, 18)))
            )
            end_x = int(x + length * math.cos(angle))
            end_y = int(y + length * math.sin(angle))
            pygame.draw.line(grass_surface, blade_color, (x, y), (end_x, end_y), 1)

        for _ in range(1400):
            x = random.randint(0, ROAD_BORDER - 1)
            y = random.randint(0, SCREEN_HEIGHT - 1)
            dot_color = (
                max(0, min(255, COLOR_GRASS_LIGHT[0] + random.randint(-10, 10))),
                max(0, min(255, COLOR_GRASS_LIGHT[1] + random.randint(-10, 10))),
                max(0, min(255, COLOR_GRASS_LIGHT[2] + random.randint(-10, 10)))
            )
            grass_surface.set_at((x, y), dot_color)

        return grass_surface

    def update(self, speed):
        self.offset = (self.offset + speed * 0.6) % (LINE_HEIGHT * 2)

    def draw_sidewalk(self, x, width):
        tile_size = 24
        rows = SCREEN_HEIGHT // tile_size + 1
        cols = width // tile_size + 1
        for row in range(rows):
            for col in range(cols):
                color = COLOR_SIDEWALK_YELLOW if (row + col) % 2 == 0 else COLOR_SIDEWALK_BLACK
                tile_x = x + col * tile_size
                tile_y = row * tile_size
                pygame.draw.rect(self.screen, color, (tile_x, tile_y, tile_size, tile_size))

    def draw(self):
        self.screen.fill(COLOR_SKY)
        road_x = (SCREEN_WIDTH - ROAD_WIDTH) // 2
        self.screen.blit(self.grass_surface, (0, 0))
        self.screen.blit(self.grass_surface, (SCREEN_WIDTH - ROAD_BORDER, 0))

        pygame.draw.rect(self.screen, COLOR_ROAD, (road_x, 0, ROAD_WIDTH, SCREEN_HEIGHT))
        self.draw_sidewalk(road_x - ROAD_BORDER, ROAD_BORDER)
        self.draw_sidewalk(road_x + ROAD_WIDTH, ROAD_BORDER)
        pygame.draw.rect(self.screen, COLOR_ROAD_BORDER, (road_x - ROAD_BORDER, 0, ROAD_BORDER, SCREEN_HEIGHT), 2)
        pygame.draw.rect(self.screen, COLOR_ROAD_BORDER, (road_x + ROAD_WIDTH, 0, ROAD_BORDER, SCREEN_HEIGHT), 2)

        # Lane markers
        for lane in range(1, LANE_COUNT):
            x = road_x + lane * LANE_WIDTH
            for y in range(-LINE_HEIGHT * 2, SCREEN_HEIGHT, LINE_HEIGHT * 2):
                rect_y = y + self.offset
                pygame.draw.rect(self.screen, COLOR_LANE, (x - 5, rect_y, 10, LINE_HEIGHT))

    @staticmethod
    def lane_center(lane_index):
        road_x = (SCREEN_WIDTH - ROAD_WIDTH) // 2
        return road_x + lane_index * LANE_WIDTH + LANE_WIDTH // 2


class Car:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (x, y)
        self.color = color
        self.speed = 0
        self.rotation = 0
        self.target_x = x

        # Smaller hitbox to match the visible supercar shape
        hitbox_width = int(width * 0.9)
        hitbox_height = int(height * 0.55)
        self.collision_rect = pygame.Rect(0, 0, hitbox_width, hitbox_height)
        self.collision_rect.center = self.rect.center

    def update_collision_rect(self):
        self.collision_rect.center = self.rect.center

    def draw(self, surface):
        x, y = self.rect.center
        w = self.rect.width // 2
        h = self.rect.height // 2

        # Draw shadow beneath the car
        shadow_rect = pygame.Rect(int(x - w * 0.9), int(y + h * 0.55), int(w * 1.8), int(h * 0.26))
        pygame.draw.ellipse(surface, COLOR_SHADOW, shadow_rect)

        # Main supercar body
        body_points = [
            (x - w * 0.9, y + h * 0.2),
            (x - w * 0.85, y - h * 0.3),
            (x - w * 0.35, y - h * 0.45),
            (x + w * 0.35, y - h * 0.45),
            (x + w * 0.85, y - h * 0.3),
            (x + w * 0.9, y + h * 0.2),
        ]
        pygame.draw.polygon(surface, self.color, body_points)
        pygame.draw.polygon(surface, (10, 10, 10), body_points, 3)

        # Hood and roof
        hood_points = [
            (x - w * 0.75, y + h * 0.1),
            (x - w * 0.25, y - h * 0.35),
            (x + w * 0.25, y - h * 0.35),
            (x + w * 0.75, y + h * 0.1),
        ]
        pygame.draw.polygon(surface, (max(0, self.color[0] - 20), max(0, self.color[1] - 20), max(0, self.color[2] - 20)), hood_points)
        pygame.draw.polygon(surface, (0, 0, 0), hood_points, 2)

        roof_rect = pygame.Rect(int(x - w * 0.35), int(y - h * 0.45), int(w * 0.7), int(h * 0.35))
        pygame.draw.rect(surface, (120, 190, 240), roof_rect, border_radius=8)
        pygame.draw.rect(surface, (0, 0, 0), roof_rect, 2, border_radius=8)

        # Front splitter and headlights
        front_rect = pygame.Rect(int(x - w * 0.9), int(y + h * 0.1), int(w * 1.8), int(h * 0.2))
        pygame.draw.rect(surface, (30, 30, 30), front_rect)
        pygame.draw.line(surface, (255, 255, 255), (x - w * 0.9, y + h * 0.1), (x + w * 0.9, y + h * 0.1), 3)

        headlight_w = int(w * 0.18)
        headlight_h = int(h * 0.12)
        pygame.draw.rect(surface, (230, 230, 120), (x - w * 0.8, y + h * 0.12, headlight_w, headlight_h), border_radius=4)
        pygame.draw.rect(surface, (230, 230, 120), (x + w * 0.62, y + h * 0.12, headlight_w, headlight_h), border_radius=4)

        # Rear spoiler
        spoiler_points = [
            (x - w * 0.65, y + h * 0.15),
            (x - w * 0.55, y + h * 0.35),
            (x + w * 0.55, y + h * 0.35),
            (x + w * 0.65, y + h * 0.15),
        ]
        pygame.draw.polygon(surface, (20, 20, 20), spoiler_points)
        pygame.draw.polygon(surface, (0, 0, 0), spoiler_points, 2)

        # Wheels
        wheel_w = int(w * 0.3)
        wheel_h = int(h * 0.3)
        wheel_positions = [
            (x - w * 0.7, y + h * 0.25),
            (x + w * 0.7 - wheel_w, y + h * 0.25),
            (x - w * 0.7, y - h * 0.05),
            (x + w * 0.7 - wheel_w, y - h * 0.05),
        ]
        for wx, wy in wheel_positions:
            wheel_rect = pygame.Rect(int(wx), int(wy), wheel_w, wheel_h)
            pygame.draw.ellipse(surface, (25, 25, 25), wheel_rect)
            pygame.draw.ellipse(surface, (90, 90, 90), wheel_rect.inflate(-wheel_w * 0.3, -wheel_h * 0.3))
            pygame.draw.ellipse(surface, (0, 0, 0), wheel_rect, 2)

        # Accent lines for a supercar look
        pygame.draw.aaline(surface, (255, 255, 255), (x - w * 0.7, y), (x - w * 0.15, y - h * 0.25))
        pygame.draw.aaline(surface, (255, 255, 255), (x + w * 0.7, y), (x + w * 0.15, y - h * 0.25))

class Player(Car):
    def __init__(self):
        start_x = Road.lane_center(LANE_COUNT // 2)
        start_y = SCREEN_HEIGHT - PLAYER_HEIGHT - 40
        super().__init__(start_x, start_y, PLAYER_WIDTH, PLAYER_HEIGHT, COLOR_PLAYER)
        self.speed = 0
        self.max_speed = 14
        self.max_reverse_speed = 3
        self.acceleration = 0.4
        self.reverse_acceleration = 0.6
        self.turn_speed = 5
        self.friction = 0.18
        self.lane = LANE_COUNT // 2

    def update(self, keys):
        forward = keys[pygame.K_UP] or keys[pygame.K_w]
        reverse = keys[pygame.K_DOWN] or keys[pygame.K_s]

        if forward and not reverse:
            self.speed += self.acceleration
        elif reverse and not forward:
            self.speed -= self.reverse_acceleration
        else:
            if self.speed > 0:
                self.speed -= self.friction
            elif self.speed < 0:
                self.speed += self.friction

        self.speed = clamp(self.speed, -self.max_reverse_speed, self.max_speed)

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.turn_speed + self.speed * 0.15
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.turn_speed + self.speed * 0.15

        left_limit = (SCREEN_WIDTH - ROAD_WIDTH) // 2 + 10
        right_limit = (SCREEN_WIDTH + ROAD_WIDTH) // 2 - self.rect.width - 10
        self.rect.x = clamp(self.rect.x, left_limit, right_limit)
        self.update_collision_rect()

        self.rotation = -self.speed * 2 if keys[pygame.K_LEFT] else self.speed * 2 if keys[pygame.K_RIGHT] else 0


class Enemy(Car):
    def __init__(self, lane, speed):
        x = Road.lane_center(lane)
        y = -ENEMY_HEIGHT
        super().__init__(x, y, ENEMY_WIDTH, ENEMY_HEIGHT, COLOR_ENEMY)
        self.speed = speed
        self.rect.centerx = x

    def update(self, game_speed):
        self.rect.y += self.speed + game_speed
        self.update_collision_rect()

    def off_screen(self):
        return self.rect.top > SCREEN_HEIGHT + 50


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pygame Racer")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.road = Road(self.screen)
        self.player = Player()
        self.enemies = []
        self.score = 0
        self.high_score = 0
        self.spawn_timer = 0
        self.running = True
        self.active = False
        self.paused = False
        self.game_speed = 0
        self.level = 1
        self.spawn_delay = SPAWN_INTERVAL
        self.last_level_increase = 0

    def reset(self):
        self.player = Player()
        self.enemies = []
        self.score = 0
        self.game_speed = 0
        self.level = 1
        self.spawn_delay = SPAWN_INTERVAL
        self.active = True
        self.paused = False
        self.spawn_timer = 0
        self.last_level_increase = pygame.time.get_ticks()

    def spawn_enemy(self):
        lane = random.randrange(LANE_COUNT)
        speed = random.uniform(3.5, 6.0)
        enemy = Enemy(lane, speed)
        enemy.rect.x = Road.lane_center(lane) - enemy.rect.width // 2
        self.enemies.append(enemy)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if self.active and not self.paused:
            self.player.update(keys)
            self.game_speed = clamp(self.player.speed * 0.65, 3, 10)
            self.road.update(self.game_speed)
            self.score += self.game_speed * dt * 0.02

            now = pygame.time.get_ticks()
            if now - self.spawn_timer > self.spawn_delay:
                self.spawn_timer = now
                self.spawn_enemy()

            if now - self.last_level_increase > 10000:
                self.last_level_increase = now
                self.level += 1
                self.spawn_delay = max(500, self.spawn_delay - 100)

            for enemy in self.enemies:
                enemy.update(self.game_speed)
            self.enemies = [enemy for enemy in self.enemies if not enemy.off_screen()]

            if self.check_collision():
                self.active = False
                self.high_score = max(self.high_score, int(self.score))
        else:
            self.road.update(0)

    def check_collision(self):
        for enemy in self.enemies:
            if self.player.collision_rect.colliderect(enemy.collision_rect):
                return True
        return False

    def draw_overlay(self):
        if not self.active or self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 10, 180))
            self.screen.blit(overlay, (0, 0))
            if not self.active:
                if self.score == 0:
                    draw_text(self.screen, "PYGAME CAR RACER", 48, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, center=True)
                    draw_text(self.screen, "Use arrow keys or WASD to drive", 26, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10, center=True)
                    draw_text(self.screen, "Avoid other cars and survive as long as possible", 22, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30, center=True)
                    draw_text(self.screen, "Press SPACE to start", 28, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90, COLOR_ACCENT, center=True)
                else:
                    draw_text(self.screen, "GAME OVER", 56, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, center=True)
                    draw_text(self.screen, f"Score: {int(self.score)}", 32, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True)
                    draw_text(self.screen, f"High Score: {int(self.high_score)}", 28, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, center=True)
                    draw_text(self.screen, "Press SPACE to restart", 26, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 110, COLOR_ACCENT, center=True)
            else:
                draw_text(self.screen, "GAME PAUSED", 56, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, center=True)
                draw_text(self.screen, "Press P to resume", 28, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, COLOR_ACCENT, center=True)
                draw_text(self.screen, "Press SPACE to restart", 22, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60, center=True)

    def draw_ui(self):
        draw_text(self.screen, f"Score: {int(self.score)}", 24, 20, 20)
        draw_text(self.screen, f"High Score: {int(self.high_score)}", 24, 20, 50)
        draw_text(self.screen, f"Speed: {int(self.player.speed * 10)} km/h", 24, 20, 80)
        draw_text(self.screen, f"Level: {self.level}", 24, SCREEN_WIDTH - 150, 20)
        draw_text(self.screen, "Press P to pause", 18, SCREEN_WIDTH - 190, 50)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if not self.active:
                            self.reset()
                    elif event.key == pygame.K_p and self.active:
                        self.paused = not self.paused

            self.update(dt)
            self.road.draw()
            self.player.draw(self.screen)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            self.draw_ui()
            if not self.active or self.paused:
                self.draw_overlay()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()

