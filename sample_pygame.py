import pygame
import sys

# Initialize pygame
pygame.init()

# Create window
width, height = 600, 400
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pygame Test")

# Colors
white = (255, 255, 255)
blue = (0, 0, 255)

# Game loop
running = True
while running:
    screen.fill(white)

    # Draw a blue rectangle
    pygame.draw.rect(screen, blue, (250, 150, 100, 50))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.update()

# Quit pygame
pygame.quit()
sys.exit()