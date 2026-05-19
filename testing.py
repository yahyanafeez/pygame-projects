import pygame
pygame.init()
#size and position
screen_height=600
screen_width=900
rectangle_height=100
rectangle_width=100
rectangle_x=200
rectangle_y=200
#colores
green_colore=(0,255,0)
#functions
main_screen=pygame.display.set_mode((screen_width,screen_height))
while True:
  for event in pygame.event.get():
    if event.type==pygame.QUIT:
        main_screen.fill=(0,0,0)
        pygame.quit()
    pygame.draw.rect(main_screen,green_colore(rectangle_x,rectangle_y,rectangle_height,rectangle_width))
    pygame.display.update()
     
    
