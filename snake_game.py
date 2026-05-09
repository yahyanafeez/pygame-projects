import pygame 
#initislize_program       
pygame.init() 
#main_screen      
screen_width=500        
screen_hight=800        
screen=pygame.display.set_mode((screen_width,screen_hight)) 
#green_ball_variables             
green_color=(0,255,0)                     
x=100                                     
y=110                                    
width_of_rectangle=12                      
hight_of_rectangle=18                                             
speed=1
dir_x=0
dir_y=0
clock = pygame.time.Clock()
#game_loop
while True:                                  
    for event in pygame.event.get():         
     if event.type==pygame.QUIT:            
       pygame.quit()           
       exit()               
    keys=pygame.key.get_pressed()
    if keys[pygame.K_RIGHT] :
     dir_x=speed
     dir_y=0
    elif keys[pygame.K_LEFT]:
      dir_x=-speed
      dir_y=0
    elif keys[pygame.K_UP]:
      dir_y=-speed
      dir_x=0
    elif keys[pygame.K_DOWN]:
      dir_y=speed
      dir_x=0
    x = x + dir_x
    y = y + dir_y

    screen.fill((0,0,0))
    pygame.draw.rect(screen,green_color,(x,y,width_of_rectangle,hight_of_rectangle))                                                                  
    pygame.display.update()                #update_the_modification
    clock.tick(40)