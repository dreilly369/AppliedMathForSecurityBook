# -*- coding: utf-8 -*-
"""
Manage the Application State for the Physical Security Planner. Maintains the
list of Objects being used in the application. Processes Keyboard and mouse
commands. Saves and Reloads Work files.

@author Daniel Reilly
"""
import pygame
import primitives
from primitives import Room, Guard, Device, Obstacle
from primitives import Wall, Marker, Floor, Background
from shapely.geometry.polygon import Polygon
from zipfile import ZipFile
from tempfile import TemporaryDirectory
import graph_shapes
import os, json, shutil, random
import threading
from PIL import Image

class DisplayAGP(threading.Thread):
    """Thread class to handle opening solution graphs in independent (Daemon)
    threads. The thread opens a previously saved image
    """
    open_image = None
    def set_file(self, bgd_file):
        self.open_image = bgd_file
        
    def run(self):
        '''Start your thread here'''
        file, ext = os.path.splitext(self.open_image)
        im = Image.open(self.open_image)
        im.show()
        return

EPSILON = 3  # Default adjustment for near-miss clicks

room_opened = False  # Determine if Room shape has been started
hole_opened = False  # Determine if Obstacle shape has been started
room_id = None  # Holds the room of the opened hole
walls = []  # Holds lines connecting open points for Rooms or Obstacles
markers = []  # Holds center points for polygon shapes
use_feet = False  # determines interpretation of distance as meters or feet
shifted = False  # Holds if the Shift key was detected (pressed)
controlled = False  # Holds if the Control key was detected (pressed)
out_file = None  # Holds the output zip name
temp_dir = None  # Holds the temporary directory name while working
scale_mode = False
current_floor = None
all_floors = []


def _generate_colors(number_colors, as_int=True, r_max=255, g_max=255, b_max=255):
    """Generate a set of random RGB color tuples as integers or floats.
    Parameters:
        number_colors: The number of RGB tuples to generate
        as_int: Return tuples as Integer values (default) or Floats 0.0-1.0
        r_max: Max Integer value for Red color value (default 255)
        g_max: Max Integer value for Green color value (default 255)
        b_max: Max Integer value for Blue color value (default 255)
    """
    colors = []
    for i in range(number_colors):
        if as_int:
            r = float("{:.2f}".format(random.random() * r_max)) 
            g = float("{:.2f}".format(random.random() * g_max))
            b = float("{:.2f}".format(random.random() * b_max))
        else:
            r = float("{:.2f}".format(random.random())) 
            g = float("{:.2f}".format(random.random()))
            b = float("{:.2f}".format(random.random()))
        colors.append((r, g, b))
    return colors
    
    
def ccw(A, B, C):
    """Tests whether the turn formed by points A, B, and C is ccw"""
    return (B[0] - A[0]) * (C[1] - A[1]) > (B[1] - A[1]) * (C[0] - A[0])
    
    
def get_all_file_paths(directory):
    """Returns a list of all file paths given a containing directory. 
    Parameters:
        directory: The root directory to search in
    """
    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    # returning all file paths
    return file_paths
    

def set_scale():    
    obj_length = float(input("input length: "))
    all_floors[current_floor].set_scale(
        obj_length
    )
    print("Pixels per Unit: %.2f" % all_floors[current_floor].ppu_scale)
    print("Unit per Pixel: %.2f" % all_floors[current_floor].upp_scale)
    
    
def reload_work(save_file):
    """ Load a previously created save zip archive
    Parameters:
        save_file: The name of the Zip archive to load from
    """
    global current_floor
    global all_floors
    
    working = os.path.dirname(__file__) + "/working/"
    with ZipFile(save_file, "r") as saved_zip: 
        os.chdir(working)
        with saved_zip.open("floors.json", "r") as layer0:
            floors = json.loads(layer0.read().decode())
        for k in list(floors.keys()):
            bg = os.path.basename(floors[k]["background"]["bg_image"])
            saved_zip.extract(bg)
            data = floors[k]
            bg = Background(data["background"]["bg_image"])
            bg.init_surface()
            fl_obj = Floor(bg, k, data["scale_points"], data["floor_name"])
            fl_obj.ppu_scale = data["ppu_scale"]
            fl_obj.upp_scale = data["upp_scale"]
            #print(fl_obj.ppu_scale)
            #print(fl_obj.upp_scale)
            print("Loading %d rooms for floor %s" % (len(floors[k]["rooms"]), k))
            if "rooms" not in data.keys():
                continue
            for room_name in list(data["rooms"].keys()):
                r_data = data["rooms"][room_name]
                r = Room(room_name, [])
                r.from_dict(r_data)
                r.init_surface()
                fl_obj.rooms.append(r)
                fl_obj.all_sprites.add(r, layer=primitives.ROOM_LAYER)
                for obs in r.obstacles:
                    fl_obj.all_sprites.add(obs, layer=primitives.OBSTACLE_LAYER)
            if "guards" in data.keys():
                for guard_name in list(data["guards"].keys()):
                    g_data = data["guards"][guard_name]
                    g = Guard(g_data["center_pos"])
                    g.from_dict(g_data)
                    g.init_surface()
                    fl_obj.all_sprites.add(g, layer=primitives.GUARD_LAYER)
                    fl_obj.guard_points.append(g)
            if "devices" in data.keys():
                for device_name in list(data["devices"].keys()):
                    d_data = data["devices"][device_name]
                    d = Device(bg.surface_size, d_data["center_pos"])
                    d.from_dict(d_data)
                    d.init_surface()
                    #print("Device FOV cone:")
                    #print(d.fov_sprite.vertex_list)
                    fl_obj.all_sprites.add(d, layer=primitives.DEVICE_LAYER)
                    fl_obj.all_sprites.add(d.fov_sprite, layer=primitives.FOC_LAYER)
                    fl_obj.device_points.append(d)
            all_floors.append(fl_obj)
            current_floor = 0
    os.chdir(os.path.dirname(__file__))
    
    
def save_work(save_file):
    """ Create a save Zip archive with all the required resources. 
    There are 3 shape files + 1 background PNG per floor. Plus 1 config JSON
    Parameters:
        save_file: The name of the Zip archive to create
    """
    global temp_dir
    global all_floors
    
    all_data = {}
    print("Saving %d floors." % len(all_floors))
    temp_dir = TemporaryDirectory()
    with temp_dir as tmp_name:
        #print("creating temporary files in %s" % tmp_name)
        script = os.path.abspath(__file__)
        l0_file = "%s/floors.json" % (tmp_name)
        working_dir = os.path.dirname(script)
    
        for i in range(len(all_floors)):
            floor = all_floors[i]
            data = floor.to_dict()
            image_name = os.path.basename(data["background"]["bg_image"])
            bgd_stored = "%s/%s" % (tmp_name, image_name)
            shutil.copy(floor.background.bg_image, bgd_stored)
            data["rooms"] = {}
            
            if len(all_floors[i].rooms) < 1:
                print("No rooms created on floor %d yet" % i)
                all_data[i] = data
                continue
            print("Saving %d rooms." % len(all_floors[i].rooms))
            for room in all_floors[i].rooms:
                data["rooms"][room.name] = room.to_dict()
            data["guards"] = {}
            count = 0
            for gp in all_floors[i].guard_points:
                data["guards"][count] = gp.to_dict()
                count += 1
            data["devices"] = {}
            count = 0
            for dev in all_floors[i].device_points:
                data["devices"][count] = dev.to_dict()
                count += 1
            all_data[i] = data
        with open(l0_file, "w") as layer0:
            json.dump(all_data, layer0)
        # call function to get all file paths in the directory
        file_paths = get_all_file_paths(tmp_name)
        # write files to a zipfile
        #print(save_file)
        with ZipFile(save_file, 'w') as save_zip:
            # writing each file one by one
            #print(save_zip)
            os.chdir(tmp_name)
            for fl in file_paths:
                save_zip.write(os.path.basename(fl))
    os.chdir(working_dir)
    print('Successfully Saved: %s' % save_file)


def add_floor(bgd_image, switch_to=False):
    """A Floor is a collection of objects and the background to display. 
    """
    global all_floors
    global current_floor
    global scale_mode
    
    working = os.path.dirname(__file__) + "/working"
    if working not in bgd_image:
        name = os.path.basename(bgd_image)
        to = "%s/%s" % (working, name)
        shutil.copy(bgd_image, to)  # Copy into working dir
        print("Created Background image copy in working directory")
        bgd_image = to # update path to working dir path
    background_sprite = Background(bgd_image)
    background_sprite.init_surface()
    r_name = input("Enter floor name: ")
    floor = Floor(background_sprite, len(all_floors), floor_name=r_name)
    all_floors.append(floor)
    if switch_to:
        current_floor = len(all_floors) - 1
        scale_mode = True

def add_device(pos, to_room):
    """Add a new Device object to the list of Device Points.
    Parameters:
        pos: The (X, Y) tuple representing the mouse location
    """
    global random_color
    global current_floor
    global all_floors
    
    fov = float(input("FoV in Degrees: "))
    er = float(input("Effective Range: "))
    rot = float(input("Rotation in Degrees: "))
    nm = input("Device name: ")
    #print(all_floors[current_floor].ppu_scale)
    r_name = all_floors[current_floor].rooms[to_room].name
    dev = Device(
            all_floors[current_floor].background.surface_size, pos,
            room_name=r_name, name=nm, rotation=rot, effective_range=er, 
            fov_deg=fov, ppu_scale=all_floors[current_floor].ppu_scale
        )
    #print("add device")
    #print(dev.fov_points())
    dev.init_surface()    
    all_floors[current_floor].device_points.append(dev)
    all_floors[current_floor].all_sprites.add(dev,layer=primitives.DEVICE_LAYER)
    all_floors[current_floor].all_sprites.add(dev.fov_sprite,layer=primitives.FOC_LAYER)
    all_floors[current_floor].created_stack.append("d")


def add_guard(pos, to_room, color=(0, 0, 0)):
    """Add a new Guard object to the list of Guard Points.
    Parameters:
        pos: The (X, Y) tuple representing the mouse location
        to_room: Index of the room to add the Guard Object to
        color: RGB String for Guard
    """
    global guard_points
    global random_color
    global current_floor
    
    olist = [c for c in all_floors[current_floor].rooms[to_room].obstacles]
    for obs in olist:
        if obs.contains(pos):
            print("Cannot place guard in obstruction.")
            return
    g_name = input("Guard Name: ")
    r_name = all_floors[current_floor].rooms[to_room].name
    guard = Guard(pos, name=g_name, color=color, room_name=r_name)
    guard.init_surface()
    all_floors[current_floor].guard_points.append(guard)
    all_floors[current_floor].all_sprites.add(guard, layer=primitives.GUARD_LAYER)
    all_floors[current_floor].created_stack.append("g")


def add_room():
    """Create a new Room object by closing the last opened marker set"""
    global room_opened
    global markers
    global walls
    global current_floor
    
    last_mark = Marker(markers[-1][0].center_pos)
    last_mark.init_surface()
    markers[-1].append(last_mark)
    
    new_shape = Polygon([m.center_pos for m in markers[-1]])
    for existing_area in all_floors[current_floor].rooms:
        other_room = existing_area.to_geometry()
        if new_shape.contains(other_room):
            print("Cannot enclose existing room")
            del markers[-1][-1]
            return
    
    all_floors[current_floor].all_sprites.remove(walls)
    all_floors[current_floor].all_sprites.remove(markers[-1])
    walls = []

    r_name = input("Name this Room: ")
    screen_size = all_floors[current_floor].surface_size
    r = Room(r_name, markers[-1], (0, 255, 0), screen_size)
    r.init_surface()
    all_floors[current_floor].rooms.append(r)
    room_opened = False
    all_floors[current_floor].all_sprites.add(r, layer=primitives.ROOM_LAYER)
    all_floors[current_floor].created_stack.append("r")
   
   
def add_obstacle_to_room():
    """Create a new Obstacle object by closing the last opened marker set"""
    global room_opened
    global markers
    global hole_opened
    global walls
    global room_id
    global current_floor
    
    m_end = Marker(markers[-1][0].center_pos)
    m_end.init_surface()
    markers[-1].append(m_end)
    olist = [c for c in all_floors[current_floor].rooms[room_id].obstacles]
    new_ob = Polygon([c.center_pos for c in markers[-1]])
    for obs in olist:
        if new_ob.contains(obs.to_geometry()):
            print("Cannot enclose other obstructions.")
            del markers[-1][-1]
            return
    print("Closing obstruction in room: %s" % all_floors[current_floor].rooms[room_id].name)
    obstacle = Obstacle(
        markers[-1],
        color=(0, 0, 0),  # RGB tuple for Black
        in_room=all_floors[current_floor].rooms[room_id].name,
        screen_sz=all_floors[current_floor].surface_size
    )
    obstacle.init_surface()
    all_floors[current_floor].rooms[room_id].add_obstacle(obstacle)
    hole_opened = False
    room_id = None
    all_floors[current_floor].all_sprites.remove(walls)
    all_floors[current_floor].all_sprites.remove(markers[-1])
    all_floors[current_floor].all_sprites.add(obstacle, layer=primitives.OBSTACLE_LAYER)
    all_floors[current_floor].created_stack.append("o")


def add_marker(at_pos, first=True, color=primitives.RED):
    global markers
    
    new_mark = Marker(at_pos, color=color)
    new_mark.init_surface()
    if first:
        print("Created new marker at %d, %d" % (at_pos[0], at_pos[1]))
        markers.append([new_mark])
    else:
        last_mark = markers[-1][-1]
        if add_wall(last_mark, new_mark, color=color):
            markers[-1].append(new_mark)
        else:
            print("Failed to add wall. Not adding Marker")
            return
    
    all_floors[current_floor].all_sprites.add(new_mark, layer=primitives.MARKER_LAYER)
    all_floors[current_floor].created_stack.append("m")


def add_wall(start_at, end_at, color=primitives.RED):
    """Add a wall sprite to the current floor plan.
    Parameters:
        start_at: Marker object representing the origin of the Wall
        end_at: Marker object representing the termination of the Wall
        color: Marker object representing the origin of the Wall
    """
    global walls
    global current_floor
    global hole_opened
    new_wall = Wall(
        start_at.center_pos,
        end_at.center_pos,
        color=color,
        screen_size = all_floors[current_floor].background.surface_size
    )
    new_wall.init_surface()
    all_floors[current_floor].all_sprites.add(
        new_wall, layer=primitives.WALL_LAYER
    )
    walls.append(new_wall)
    return True
    
def undo():
    global current_floor
    global room_opened
    global hole_opened
    global markers
    global walls
    global room_id
    
    if len(all_floors[current_floor].created_stack) < 1:
        return
    o_type = all_floors[current_floor].created_stack.pop(-1)
    print("last created: %s" % o_type)
    if o_type == "d":
        # Represents a device creation
        if len(all_floors[current_floor].device_points) < 1:
            raise Exception("Encountered missing device in Undo")
        device_layer = all_floors[current_floor].all_sprites.get_sprites_from_layer(
            primitives.DEVICE_LAYER
        )
        del all_floors[current_floor].device_points[-1]
        last = device_layer[-1]
        last.clear_surface()
        all_floors[current_floor].all_sprites.remove(last)
        all_floors[current_floor].all_sprites.remove(last.fov_sprite)
    elif o_type == "g":
        # Represents a guard creation
        if len(guard_points) < 1:
            raise Exception("Encountered missing guard in Undo")
        guard_layer = all_floors[current_floor].all_sprites.get_sprites_from_layer(
            primitives.GUARD_LAYER
        )
        del all_floors[current_floor].guard_points[-1]
        last = guard_layer[-1]
        last.clear_surface()
        all_floors[current_floor].all_sprites.remove(last)
    elif o_type == "m":
        # Represents a Marker creation
        markers[-1].pop()
        marker_layer = all_floors[current_floor].all_sprites.get_sprites_from_layer(
            primitives.MARKER_LAYER
        )
        last = marker_layer[-1]
        last.clear_surface()
        all_floors[current_floor].all_sprites.remove(last)
        if len(markers[-1]) > 0:
            wall_layer = all_floors[current_floor].all_sprites.get_sprites_from_layer(
                primitives.WALL_LAYER
            )
            last = wall_layer[-1]
            last.clear_surface()
            all_floors[current_floor].all_sprites.remove(last)
        else:
            del markers[-1]
            room_opened = False
            hole_opened = False
    elif o_type == "r":
        # Represents a closing of an Room. needs to be reopened
        room = all_floors[current_floor].rooms.pop()
        markers[-1].pop()
        room.clear_surface()
        all_floors[current_floor].all_sprites.add(
            markers[-1][0], layer=primitives.MARKER_LAYER
        )
        for i in range(len(markers[-1]) - 1):
            m1 = markers[-1][i]
            m2 = markers[-1][i + 1]
            all_floors[current_floor].all_sprites.add(m2, layer=primitives.MARKER_LAYER)
            add_wall(m1, m2, primitives.GREEN)
        all_floors[current_floor].all_sprites.remove(room)
        room_opened = True
    elif o_type == "o":
        markers[-1].pop()
        obstacle_sprites = all_floors[current_floor].all_sprites.get_sprites_from_layer(
            primitives.OBSTACLE_LAYER
        )
        all_floors[current_floor].all_sprites.remove(obstacle_sprites[-1])
        all_floors[current_floor].all_sprites.add(
            markers[-1][0], layer=primitives.MARKER_LAYER
        )
        for i in range(len(markers[-1]) - 1):
            m1 = markers[-1][i]
            m2 = markers[-1][i + 1]
            all_floors[current_floor].all_sprites.add(m2, layer=primitives.MARKER_LAYER)
            add_wall(m1, m2, primitives.GREEN)

        hole_opened = True
            
def handle_keydown(event):
    """Handle PyGame event.KEYDOWN events
    
    """
    global room_opened
    global shifted
    global hole_opened
    global out_file
    global controlled
    global current_floor
    global scale_mode
    
    if event.key in [303, 304]:
        # Shift key depressed
        shifted = True
        return
    if event.key == 306:
        controlled = True
        return
    if event.key == 273:
        # Up arrow cycle up floors
        if room_opened or hole_opened:
            print("Cannot change floor with open shape")
            return
        current_floor = (current_floor + 1) % len(all_floors)
        if len(all_floors[current_floor].scale_points) < 2:
            scale_mode = True
        return
    if event.key == 274:
        # Down arrow cycle down floors
        if room_opened or hole_opened:
            print("Cannot change floor with open shape")
            return
        if current_floor == 0:
            current_floor = len(all_floors) - 1
        else:
            current_floor -= 1
        if len(all_floors[current_floor].scale_points) < 2:
            scale_mode = True
        return
    if event.unicode == "z":
        undo()
    elif event.unicode == "1":
        print("Creating new floor")
        new_bg = input("Enter background PNG path: ")
        add_floor(new_bg, switch_to=True)
    elif event.unicode == "q":
        """ 
        """
        curr_showing = all_floors[current_floor].all_sprites.get_sprites_from_layer(10)
        if len(curr_showing) > 0:
            all_floors[current_floor].all_sprites.remove_sprites_of_layer(10)
        else:
            scale_wall = Wall(
                    all_floors[current_floor].scale_points[0],
                    all_floors[current_floor].scale_points[1],
                    color=primitives.BLUE,
                    screen_size=all_floors[current_floor].surface_size
                )
            scale_wall.init_surface()
            m1 = Marker(all_floors[current_floor].scale_points[0], color=primitives.BLUE)
            m2 = Marker(all_floors[current_floor].scale_points[1], color=primitives.BLUE)
            m1.init_surface()
            m2.init_surface()
            all_floors[current_floor].all_sprites.add([
                    scale_wall,
                    m1,
                    m2
                ], layer=10)
    elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_LCTRL:
        print("Saving...")
        save_work(out_file)
    elif event.unicode == "g":
        """Creates Guard Voronoi Diagram from manually placed guard nodes 
        """
        print("Voronoi Not Implemented, yet. ;)")
        res = graph_shapes.mp_solve_floors(all_floors)
        print(res)
        
    elif event.unicode == "f":
        """ Creates Sensor deployment map 
        """
        print("Voronoi Not Implemented, yet. ;)")
        
    elif event.unicode == "p":
        """ Create deployments with constrained triangle area
        """
        bgd_file = all_floors[current_floor].background.bg_image
        #print(bgd_file)
        shape_list = all_floors[current_floor].rooms
        if len(all_floors[current_floor].rooms) < 1:
            print("No rooms created yet")
            return
        G_tri, deployments, tri_res = graph_shapes.agp_floorplan(
            shape_list, bgd_file
        )
        # Create Guard deployments with constrained triangle area
        thread = DisplayAGP()
        thread.set_file("gugg_solved.png") # Change to whatever the project name should be
        thread.daemon = True
        thread.start()
        return
        
    elif event.unicode == "a":
        print("AoR Not Implemented, yet. ;)")

def handle_keyup(event):
    global shifted
    global controlled
    if event.key in [303, 304]:
        shifted = False
        return
    if event.key == 306:
        controlled = False
        return


def check_clicked_within_room(mouse_pos):
    """Checks if the clicked point is within any closed Room polygon
    Parameters:
        mouse_pos: The (X, Y) tuple representing the mouse location
    """
    
    if len(all_floors[current_floor].rooms) < 1:
        return None
    for i in range(len(all_floors[current_floor].rooms)):
        if all_floors[current_floor].rooms[i].contains(mouse_pos):
            return i
    return None


def check_clicked_existing_vertex(mouse_pos):
    """Checks if the clicked point is within +/- epsilon of any Marker vertex
    to allow for slight misses with the mouse
    Parameters:
        mouse_pos: The (X, Y) tuple representing the mouse location
    """
    if not markers:
        return None
    clicked = None
    for s in range(len(markers)):
        marker_set = markers[s]
        for i in range(len(marker_set)):
            vertex = marker_set[i].center_pos  # an X, Y tuple
            if within_epsilon(mouse_pos, vertex):
                return (s, i)
    return clicked
    
    
def within_epsilon(mouse_pos, point_pos):
    """Checks if the clicked point is within +/- epsilon of another point
    to allow for slight misses with the mouse
    Parameters:
        mouse_pos: The (X, Y) tuple representing the mouse location
        point_pos: The (X, Y) tuple representing the point to compare against
    """
    return all([
            (abs(mouse_pos[0] - point_pos[0]) < EPSILON),
            (abs(mouse_pos[1] - point_pos[1]) < EPSILON)
        ])
        
        
def left_click(event, clicked=None, in_room=None):
    """Handle Left-Mouse-Button clicks based off current state"""
    global room_opened
    global walls
    global hole_opened
    global room_id
    global obstructions
    global shifted
    global scale_mode
    
    if scale_mode:
        sm = Marker(event.pos, color=primitives.BLUE)
        sm.init_surface()
        all_floors[current_floor].scale_points.append(event.pos)
        all_floors[current_floor].all_sprites.add(sm, layer=10)
        if len(all_floors[current_floor].scale_points) == 2:
            scale_line = Wall(
                all_floors[current_floor].scale_points[0],
                sm.center_pos,
                color=primitives.BLUE,
                screen_size=all_floors[current_floor].surface_size
            )
            scale_line.init_surface()
            all_floors[current_floor].all_sprites.add(scale_line, layer=10)
            set_scale()
            scale_mode = False
        
        return
    if not room_opened:
        # No open polygons
        if in_room is not None and not shifted and not controlled:
            return
        if shifted and in_room is not None:
            add_guard(event.pos, in_room)
        elif controlled and in_room is not None:
            add_device(event.pos, in_room)
        elif clicked is not None:
            print("clicked %d %d" % (clicked[0], clicked[1]))
            return
        elif in_room is None and clicked is None:
            print("opening room")
            add_marker(event.pos, first=True)
            room_opened = True
    else:
        # Open polygon to consider
        if in_room is not None and clicked is None:
            print("Cannot cross Room shapes")
            return
        elif clicked is not None:
            print("clicked %d %d" % (clicked[0], clicked[1]))
            if clicked[1] == 0:
                # Clicked the starting node
                add_room()
                room_opened = False
        elif shifted:
            pass
        elif controlled:
            pass
        else:
            add_marker(event.pos, first=False)

def right_click(event, clicked=None, in_room=None):
    """Handle Right-Mouse-Button clicks based off current state"""
    global walls
    global hole_opened
    global room_id
    global obstructions
    global shifted
    
    if not hole_opened:
        # No open polygons
        if clicked is None and in_room is not None:
            # Add a marker at the exact location
            add_marker(event.pos, first=True, color=primitives.BLACK)
            hole_opened = True
            room_id = in_room
        elif clicked is not None:
            print("clicked node", clicked)
        else:
            # clicked outside all rooms
            print("Right-Clicked outside room %d" % room_id)
    else:
        # Open polygon to consider
        if clicked is None and in_room is None:
            # add point to last opened shape
            print("Cannot extend obstruction past edge of Room")
        elif clicked is not None and clicked[1] == 0:
            if in_room == room_id:
                # Clicked the 0th point in the open Obstacle shape
                add_obstacle_to_room()
        elif in_room != room_id:
            print("Obstacle cannot cross room polygons")
        else:
            add_marker(event.pos, first=False, color=primitives.BLACK)
        
def handle_click(event):
    global room_opened
    global hole_opened
    clicked = check_clicked_existing_vertex(event.pos)
    in_room = check_clicked_within_room(event.pos)
    if event.button == 1:
        if hole_opened:
            print("Complete the opened Obstruction before moving on")
            return
        left_click(event, clicked, in_room)
    elif event.button == 3:
        if room_opened:
            print("Complete the opened Room before moving on")
            return
        right_click(event, clicked, in_room)


def cleanup_state():
    """Cleanup the temp dir and any lingering data"""
    global temp_dir
    if temp_dir is not None:
        temp_dir.cleanup()
        temp_dir = None
