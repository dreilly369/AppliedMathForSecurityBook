# -*- coding: utf-8 -*-
"""
This program allows users to mathematically analyze different types of security
for 2 dimensional spaces. Currently the two types of analysis are internal and
perimeter. The general workflow is:
    1. Load a Floorplan as a background PNG (-b)
    2. Draw one or more closed polygons. Add the vertices in CCW order.
    3. Save the shape file (Keyboard S) to the output file (-o)
    4. To add internal guards (Keyboard Shift + Left Click)
@author Daniel Reilly
"""

import os, time
import pygame
import sys
import state_manager as state
import triangle as tr
from pgu import gui
from pygame.locals import *
from optparse import OptionParser

poly_color = (100, 255, 0)  # Default Room color
hole_color = (0, 0, 0)  # Default Obstacle color
guard_color = (255, 0, 0)  # Default Guard color
device_color = (120, 0, 120)  # Default Guard color
white = (255, 255, 255)  # White for background
random_color = False  # Randomly select color for new Guards and Devices
bgd_image = None  # Holds the path string
loaded = None  # Holds the background image data

clock = pygame.time.Clock()  # Used to manage how fast the screen updates
def open_file_browser(arg):
    d = gui.FileDialog()
    d.connect(gui.CHANGE, handle_file_browser_closed, d)
    d.open()
    

def handle_file_browser_closed(dlg):
    if dlg.value:
        if ".png" in dlg.value:
            return dlg.value
        else:
            print("Nota valid PNG file")
            
class SimpleDialog(gui.Dialog):
    def __init__(self):
        title = gui.Label("")
        main = gui.Container(width=640, height=480)
        # passing the 'height' parameter resulting in a typerror when paint was called
        super(SimpleDialog, self).__init__(title, main, width=640)  # , height=40)

    def close(self, *args, **kwargs):
        return super(SimpleDialog, self).close(*args, **kwargs)
    
if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-r", "--resume", dest="resume_file", default=None,
        help="Load Room shapes from a previously saved file")
    parser.add_option("-b", "--background", dest="bgd_file", default=None,
        help="Background PNG to load (if not resuming)")
    parser.add_option("-o", "--out-file", dest="out_file", default=None,
        help="File to save shapes to")
    #parser.add_option("-c", "--randomize-color", dest="rand_color", default=None,
    #    help="Randomly assign colors to guards")
    parser.add_option("-e", "--epsilon", dest="epsilon", default=3,
        help="Sets near-miss distance")
    parser.add_option("-f", "--use-feet", dest="change_measure", default=False,
        help="Convert distances from meters to feet", action="store_true")
    (opts, args) = parser.parse_args()
    app = gui.App()

    dialog = SimpleDialog()
    app.init(dialog)
    if not opts.out_file:
        print("Need output file to save work to")
        exit()
    state.out_file = opts.out_file
    if opts.resume_file:
        state.reload_work(opts.resume_file)
    elif opts.bgd_file is None:
        print("Need Background PNG file (-b)")
        exit()
    else:
        bgd_image = opts.bgd_file
        state.add_floor(bgd_image, True)
    print("initializing display")
    pygame.display.init()
    

    # set the pygame window name
    f_name = state.all_floors[state.current_floor].floor_name
    pygame.display.set_caption('Floor %s to Polygon' % f_name)
    screen_size = state.all_floors[state.current_floor].surface_size
    display_surface = pygame.display.set_mode(screen_size) 
    display_surface.fill(white) 
    app.paint(display_surface)
    if len(state.all_floors[state.current_floor].scale_points) == 0:
        print("Entering Scale Mode")
        state.scale_mode = True
    # Create the room polygon layer
    layer_1 = pygame.Surface(screen_size) 
    layer_1.set_alpha(70)  # alpha level
    layer_1.set_colorkey(white)
    layer_1.fill(white)
    # Limit to 60 frames per second
    clock.tick(60)
    # infinite loop
    running = True
    disp = True
    last_floor = 0
    
    while running:
        display_surface.fill(white) 
        if state.scale_mode:
            #print("Entering Scale Mode")
            f_name = state.all_floors[state.current_floor].floor_name
            pygame.display.set_caption('%s Scale Entry Mode' % f_name)
            disp = True
        else:
            if disp:
                print(state.all_floors[state.current_floor].scale_points)
                disp = False
            if state.current_floor != last_floor:
                
                print("changed to floor %d" % state.current_floor)
                last_floor = state.current_floor
                f_name = state.all_floors[state.current_floor].floor_name
                pygame.display.set_caption('Floor %s to Polygon' % f_name)

        display_surface.blit(state.all_floors[state.current_floor].background.image, (0, 0))
        # Draws the surface objects to the screen.
        layer_1.fill(white) # clear screen
        state.all_floors[state.current_floor].all_sprites.draw(layer_1)
        display_surface.blit(layer_1, (0, 0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                working_files = state.get_all_file_paths(os.path.dirname(__file__))
                for file_path in working_files:
                    os.remove(file_path)
                pygame.display.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                state.handle_click(event)
            elif event.type == pygame.KEYDOWN:
                pygame.event.clear(None)
                state.handle_keydown(event)
            elif event.type == pygame.KEYUP:
                state.handle_keyup(event)
            elif event.type != pygame.MOUSEMOTION:
                pass
                #print(event)
        pygame.event.clear() # Clear events that may have requeued during the previous loop
        pygame.display.flip()
        
        time.sleep(0.05)
    exit()
