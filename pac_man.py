import pygame
import math
import random

# --------------------
# Initialize pygame
# --------------------
pygame.init()

# Screen
WIDTH = 1000
HEIGHT = 1000

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Pac-Man")

clock = pygame.time.Clock()

# --------------------
# Colors
# --------------------
BLACK = (0, 0, 0)
YELLOW = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
RED = (250, 218, 221)

# --------------------
# Pac-Man variables
# --------------------
pac_x = 300
pac_y = 300

pac_radius = 25
speed = 5

mouth_angle =0
mouth_opening = True

# Food
food_x = 100
food_y = 100
food_radius = 6

score = 0

font = pygame.font.SysFont(None, 40)

# Direction
direction = "RIGHT"

# --------------------
# Game loop
# --------------------
running = True

while running:

    clock.tick(60)

    # --------------------
    # Events
    # --------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --------------------
    # Key controls
    # --------------------
    keys = pygame.key.get_pressed()

    if keys[pygame.K_RIGHT]:
        pac_x += speed
        direction = "RIGHT"

    if keys[pygame.K_LEFT]:
        pac_x -= speed
        direction = "LEFT"

    if keys[pygame.K_UP]:
        pac_y -= speed
        direction = "UP"

    if keys[pygame.K_DOWN]:
        pac_y += speed
        direction = "DOWN"

    # --------------------
    # Boundary collision
    # --------------------
    if pac_x - pac_radius < 0:
        pac_x = pac_radius
    if pac_x + pac_radius > WIDTH:
        pac_x = WIDTH - pac_radius
    if pac_y - pac_radius < 0:
        pac_y = pac_radius
    if pac_y + pac_radius > HEIGHT:
        pac_y = HEIGHT - pac_radius

    # --------------------
    # Mouth animation
    # --------------------
    if mouth_opening:
        mouth_angle += 2
        if mouth_angle >= 40:
            mouth_opening = False
    else:
        mouth_angle -= 2
        if mouth_angle <= 5:
            mouth_opening = True

    # --------------------
    # Food collision
    # --------------------
    distance = math.sqrt((pac_x - food_x)**2 + (pac_y - food_y)**2)

    if distance < pac_radius:
        food_x = random.randint(50, 550)
        food_y = random.randint(50, 550)
        score += 1

    # --------------------
    # Background
    # --------------------
    screen.fill(RED)

    # --------------------
    # Draw food
    # --------------------
    pygame.draw.circle(screen, WHITE, (food_x, food_y), food_radius)

    # --------------------
    # Draw Pac-Man
    # --------------------

    start_angle = 0
    end_angle = 0

    if direction == "RIGHT":
        start_angle = math.radians(mouth_angle)
        end_angle = math.radians(360 - mouth_angle)

    elif direction == "LEFT":
        start_angle = math.radians(180 + mouth_angle)
        end_angle = math.radians(180 - mouth_angle)

    elif direction == "UP":
        start_angle = math.radians(270 + mouth_angle)
        end_angle = math.radians(270 - mouth_angle)

    elif direction == "DOWN":
        start_angle = math.radians(90 + mouth_angle)
        end_angle = math.radians(90 - mouth_angle)

    pygame.draw.circle(screen, YELLOW, (pac_x, pac_y), pac_radius)

    pygame.draw.polygon(
        screen,
        BLACK,
        [
            (pac_x, pac_y),

            (
                pac_x + pac_radius * math.cos(start_angle),
                pac_y - pac_radius * math.sin(start_angle)
            ),

            (
                pac_x + pac_radius * math.cos(end_angle),
                pac_y - pac_radius * math.sin(end_angle)
            )
        ]
    )

    # --------------------
    # Score
    # --------------------
    score_text = font.render(f"Score: {score}", True, BLUE)

    screen.blit(score_text, (20, 20))

    # --------------------
    # Update display
    # --------------------
    pygame.display.update()

pygame.quit()