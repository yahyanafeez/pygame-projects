import pygame

pygame.init()

# size and position
screen_height = 600
screen_width = 900

rectangle_height = 100
rectangle_width = 100

rectangle_x = 200
rectangle_y = 200

# colors
green_colore = (0, 255, 0)

# create screen
main_screen = pygame.display.set_mode((screen_width, screen_height))

running = True

while running:

    # events
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    # fill background
    main_screen.fill((0, 0, 0))

    # draw rectangle
    pygame.draw.rect(
        main_screen,
        green_colore,
        (rectangle_x, rectangle_y, rectangle_width, rectangle_height)
    )

    # update screen
    pygame.display.update()

pygame.quit()