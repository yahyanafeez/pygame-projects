import math
import random
import sys
import pygame

# -----------------------------
# Constants
# -----------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
ROAD_WIDTH = 420
ROAD_BORDER = 80
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT
LINE_HEIGHT = 40
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 100
ENEMY_WIDTH = 50
ENEMY_HEIGHT = 100
SPAWN_INTERVAL = 1100  # milliseconds

# Colors
COLOR_SKY = (43, 89, 144)
COLOR_GRASS = (36, 110, 67)
COLOR_ROAD = (56, 56, 56)
COLOR_ROAD_BORDER = (194, 194, 194)
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

    def update(self, speed):
        self.offset = (self.offset + speed * 0.6) % (LINE_HEIGHT * 2)

    def draw(self):
        self.screen.fill(COLOR_SKY)
        pygame.draw.rect(self.screen, COLOR_GRASS, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        road_x = (SCREEN_WIDTH - ROAD_WIDTH) // 2
        pygame.draw.rect(self.screen, COLOR_ROAD, (road_x, 0, ROAD_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, COLOR_ROAD_BORDER, (road_x - ROAD_BORDER, 0, ROAD_BORDER, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, COLOR_ROAD_BORDER, (road_x + ROAD_WIDTH, 0, ROAD_BORDER, SCREEN_HEIGHT))

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

    def draw(self, surface):
        points = self._get_car_shape()
        pygame.draw.polygon(surface, COLOR_SHADOW, [(p[0] + 4, p[1] + 8) for p in points])
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, COLOR_TEXT, [points[0], points[1], points[1], points[2]], 2)

    def _get_car_shape(self):
        x, y = self.rect.center
        w = self.rect.width // 2
        h = self.rect.height // 2
        return [
            (x - w * 0.8, y - h),  # top-left
            (x + w * 0.8, y - h),  # top-right
            (x + w, y + h),        # bottom-right
            (x - w, y + h),        # bottom-left
        ]


class Player(Car):
    def __init__(self):
        start_x = Road.lane_center(LANE_COUNT // 2)
        start_y = SCREEN_HEIGHT - PLAYER_HEIGHT - 40
        super().__init__(start_x, start_y, PLAYER_WIDTH, PLAYER_HEIGHT, COLOR_PLAYER)
        self.speed = 0
        self.max_speed = 14
        self.acceleration = 0.4
        self.deceleration = 0.3
        self.turn_speed = 5
        self.friction = 0.18
        self.lane = LANE_COUNT // 2

    def update(self, keys):
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed += self.acceleration
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed -= self.deceleration
        else:
            if self.speed > 0:
                self.speed -= self.friction
            elif self.speed < 0:
                self.speed += self.friction

        self.speed = clamp(self.speed, -3, self.max_speed)

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.turn_speed + self.speed * 0.15
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.turn_speed + self.speed * 0.15

        left_limit = (SCREEN_WIDTH - ROAD_WIDTH) // 2 + 10
        right_limit = (SCREEN_WIDTH + ROAD_WIDTH) // 2 - self.rect.width - 10
        self.rect.x = clamp(self.rect.x, left_limit, right_limit)

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
        if self.active:
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
            if self.player.rect.colliderect(enemy.rect):
                return True
        return False

    def draw_overlay(self):
        if not self.active:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 10, 180))
            self.screen.blit(overlay, (0, 0))
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

    def draw_ui(self):
        draw_text(self.screen, f"Score: {int(self.score)}", 24, 20, 20)
        draw_text(self.screen, f"High Score: {int(self.high_score)}", 24, 20, 50)
        draw_text(self.screen, f"Speed: {int(self.player.speed * 10)} km/h", 24, 20, 80)
        draw_text(self.screen, f"Level: {self.level}", 24, SCREEN_WIDTH - 150, 20)

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

            self.update(dt)
            self.road.draw()
            self.player.draw(self.screen)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            self.draw_ui()
            if not self.active:
                self.draw_overlay()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
