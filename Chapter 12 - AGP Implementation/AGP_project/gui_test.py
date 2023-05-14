import pygame
from colour import Color

pygame.init()
GREEN = (0,255,0)
WHITE = (255,255,255)
BLUE = (0,0,255)

class Room(pygame.sprite.Sprite):
    vertex_list = []
    color = BLUE
    obstacles = []
    surface_size = None
    
    def __init__(self, vertex_list, screen_sz):
        super().__init__()
        self.vertex_list = [(p[0],p[1]) for p in vertex_list]
        self.obstacles = []
        self.surface_size = screen_sz
        
    def init_surface(self):
        # Set the background color and set it to be transparent
        self.screen = pygame.Surface(self.surface_size)
        self.screen.fill(WHITE)
        self.screen.set_colorkey(WHITE)
        pygame.draw.polygon(
            self.screen,
            self.color,
            self.vertex_list,
            0  # Filled polygon
        )
    def clear_surface(self):
        self.screen.fill(WHITE)
        self.screen.set_colorkey(WHITE)
        
def test_1():

    background = pygame.image.load("working/guggenheim.png")
    screen = pygame.display.set_mode(background.get_rect().size, 0, 32)
    background = background.convert()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.blit(background, (0, 0))
        
        mid_x = screen.get_width() / 2
        mid_y = screen.get_height() / 2
        pygame.draw.circle(screen, GREEN, (mid_x, mid_y), 50)
        
        pygame.display.flip()
        pygame.image.save(screen, "screenshot.png")
    pygame.quit()

def test_2():
    gallery_poly = [(20, 10), (20, 20), (55, 148), (145, 145)]
    background = pygame.image.load("working/guggenheim.png")
    screen = pygame.display.set_mode(background.get_rect().size, 0, 32)
    background = background.convert()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.blit(background, (0, 0))
        poly_sprite = Room(gallery_poly, background.get_rect().size)
        poly_sprite.init_surface()
        screen.blit(poly_sprite.screen, (5,5))
        pygame.display.flip()
        pygame.image.save(screen, "screenshot2.png")
    pygame.quit()
    
test_2()