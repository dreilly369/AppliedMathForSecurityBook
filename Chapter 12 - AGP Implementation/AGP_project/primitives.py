# -*- coding: utf-8 -*-
"""Base classes for modeling floorplans, rooms, guards, and sensor devices in
a physical space.
@author Daniel Reilly
"""
from shapely.geometry import Point, LineString
from shapely.geometry.polygon import Polygon
import pygame
import png
import math

WHITE = (255, 255, 255) # RGB tuple for Black
BLACK = (0, 0, 0)  # RGB tuple for Black
BLUE = (0, 0, 255)  # RGB tuple for Black
GREEN = (0, 255, 0)  # RGB tuple for Black
RED = (255, 0, 0)

SCREEN_SIZE = [640, 480]
ROOM_LAYER = 1
OBSTACLE_LAYER = 2
GUARD_LAYER = 3
DEVICE_LAYER = 4
WALL_LAYER = 5
MARKER_LAYER = 6
FOC_LAYER = 7

        
class Marker(pygame.sprite.Sprite):
    """Sprite subclass representing a single vertex. Drawn as a filled circle.
    
        Attributes
        ----------
        center_pos : Tuple
            The (x,y) location for the center of the vertex graphic
        color : Tuple
            The (r,g,b) value for displaying the vertex
        width : Integer
            The number of pixels wide to display the point
        layer : Integer
            The layer number the vertex belongs to. Default MARKER_LAYER (6)
        rect : Tuple
            The rectangle object representing the display surface area
        image : Surface
            The PyGame display Surface
            
        Methods
        -------
        init_surface()
            Create PyGame surface to display the vertex.
        to_geometry()
            Returns the Marker object represented as a shapely Point
        clear_surface()
            Remove the graphic from the disaply object.
    """
    center_pos = None
    color = None
    width = 3
    layer = MARKER_LAYER
    
    def __init__(self, center_pos, width=3, color=(0, 0, 255)):
        """
        Parameters
        ----------
        center_pos : Tuple
            The (x,y) location for the center of the vertex graphic
        color : Tuple
            The (r,g,b) value for displaying the vertex. Default (0, 0, 255)
        width : Integer
            The number of pixels wide to display the point. Default 3
        """
        super().__init__()
        self.center_pos = center_pos
        self.color = color
        self.width = width
        
    def init_surface(self):
        """ Create pygame Surface to hold the Marker graphic. Needs to be called
        before displaying the marker in the application.
        
        Parameters
        ----------
        None
        """
        # Set the background color and set it to be transparent
        self.image = pygame.Surface([self.width * 2, self.width * 2])
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        pygame.draw.circle(
                self.image,
                self.color,
                (self.width, self.width),
                self.width,
                1
            )
        self.rect = self.image.get_rect()
        self.rect.x = self.center_pos[0] - self.width
        self.rect.y = self.center_pos[1] - self.width
        
    def to_geometry(self):
        """Return a shapely Point object representing this marker in 2D space.
        
        Parameters
        ----------
        None
        """
        return(Point(self.center_pos))
        
    def clear_surface(self):
        """Clear the Marker graphic by painting the surface object white
        
        Parameters
        ----------
        None
        """
        self.image.fill(WHITE)
        
        
class View(pygame.sprite.Sprite):
    """Sprite subclass representing a Field of View. Drawn as a filled polygon.
    
    Attributes
    ----------
    origin_pos : Tuple
        The (x,y) location for the vertex generating the FoV
    color : Tuple
        The (r,g,b) value for displaying the FoV polygon
    rot : Float
        The rotation in degrees for the centerline of the FoV
    effective_range : Float
        The effective range for the FoV in scale units
    fov : Float
        The range in degrees for the FoV
    image : Surface
        The PyGame display Surface
    surface_size : Tuple
        The (width, height) tuple for the screen
    vertex_list : Float
        The list of vertices which make up the FoV polygon
    rect : Tuple
        The rectangle object representing the display surface area
    image : Surface
        The PyGame display Surface
        
    Methods
    -------
    init_surface()
        Create PyGame surface to display the vertex.
    to_geometry()
        Returns the Marker object represented as a shapely Point
    clear_surface()
        Remove the graphic from the disaply object.
    """
    origin_pos = None
    rot = None
    effective_range = None
    fov = None
    color = None
    image = None
    surface_size = (10, 10)
    vertex_list = None
    
    def __init__(
            self, origin_pos, vertex_list,
            rotation, eff_range=10.0, fov_deg=60.0,
            screen_size=(10,10), color=(0, 0, 255)
        ):
        """
        Parameters
        ----------
        origin_pos : Tuple
            The (x,y) location for the vertex generating the FoV
        vertex_list : Float
            The range in degrees for the FoV  
        rot : Float
            The rotation in degrees for the centerline of the FoV
        eff_range : Float
            The effective range for the FoV in scale units. Default 10.0
        fov_deg : Float
            The range in degrees for the FoV. Default 60.0
        screen_size : Tuple
            The range in degrees for the FoV
        color : Tuple
            The (r,g,b) tuple to use when displaying the Fov
        """
        super().__init__()
        self.origin_pos = origin_pos
        self.rot = rotation
        self.effective_range = eff_range
        self.fov = fov_deg
        self.color = color
        self.surface_size = screen_size
        self.vertex_list = vertex_list
        
    def init_surface(self):
        """ Create pygame Surface to hold the Marker graphic. Needs to be called
        before displaying the marker in the application.
        
        Parameters
        ----------
        None
        """
        # Set the background color and set it to be transparent
        self.image = pygame.Surface(self.surface_size)
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        self.image.set_alpha(80)  # set the FoV alpha level
        pygame.draw.polygon(
            self.image,
            self.color,
            self.vertex_list
        )
        self.rect = self.image.get_rect()
    
    def to_geometry(self):
        """Return a shapely Polygon object representing this FoV in 2D space.
        
        Parameters
        ----------
        None
        """
        return(Polygon(self.vertex_list))
        
    def clear_surface(self):
        """Clear the view graphic by painting the surface object white
        
        Parameters
        ----------
        None
        """
        self.image.fill(WHITE)
        
class Wall(pygame.sprite.Sprite):
    """Sprite subclass representing a connection between two points in an open 
    polygon.

    Attributes
    ----------
    start_pos : Tuple
        The (x,y) location for the wall's start
    end_pos : Tuple
        The (x,y) location for wall's end
    width : Integer
        Pixel thickness to draw the line on-screen
    color : Tuple
        An (r,g,b) tuple of the color to use when displaying the wall
    surface_size : Tuple
        A (width, height) tuple to size the display Suface object
    rect : Tuple
        The rectangle object representing the display surface area
    image : Surface
        The PyGame display Surface
        
    Methods
    -------
    init_surface()
        Create PyGame surface to display the wall.
    to_geometry()
        Returns the wall object represented as a shapely LineString
    intersects(thing)
        Checks if the wall object intersects with the thing passed in.
        See the function notes for valid types for thing
    clear_surface()
        Remove the graphic from the disaply object.
    """
    start_pos = None
    end_pos = None
    color = None
    width = 0
    surface_size = None
    
    def __init__(self, start_pos, end_pos, width=2, color=(255, 0, 0), screen_size=(10,10)):
        """
        Parameters
        ----------
        start_pos : Tuple
            The (x,y) location for the wall's start
        end_pos: Tuple
            The (x,y) location for wall's end
        width: Integer
            Pixel thickness to draw the line on-screen
        color: Tuple
            An (r,g,b) tuple (default (255,0,0))
        surface_size: Tuple
            A (width, height) tuple (default (10,10))
        """
        super().__init__()
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.width = width
        self.surface_size = screen_size
        
    def init_surface(self):
        """ Create pygame Surface to hold the wall graphic. Needs to be called
        before displaying the wall in the application.
        
        Parameters
        ----------
        None
        """
        # Set the background color and set it to be transparent
        self.image = pygame.Surface(self.surface_size)
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        # Draw the wall graphic on the display Surface
        pygame.draw.line(
            self.image,
            self.color,
            self.start_pos,
            self.end_pos,
            self.width
        )
        # Set the rect attribue based on the 
        self.rect = self.image.get_rect()
        
    def to_geometry(self):
        """ Returns a shapely LineString object representing the wall.
        
        Parameters
        ----------
        None
        """
        return(LineString([self.start_pos, self.end_pos]))
        
    def intersects(self, thing):
        """ Checks if Wall intersects with the object passed in. Valid types for
        thing are another primitive which has the to_geometry attribute, 
        an (x,y) Tuple representing a point, or a list of (x,y) tuples. If
        the list starts and ends with the same point thing is treated as a Polygon,
        otherwise it is treated as a LineString.
        
        Parameters
        ----------
        None
        
        Raises
        ------
        NotImplementedError
            If type of thing cannot be determined raises exception with the
            type of the thing passed in for reference
        """
        thing_1 = self.to_geometry()
        if hasattr(thing, "to_geometry"):
            # Thing is another primitive
            thing_2 = thing.to_geometry()
        elif isinstance(thing, tuple):
            # Thing is a point
            thing_2 = Point(thing)
        elif isinstance(thing, list):
            if len(thing) >= 2:
                if thing[0] != thing[-1]:
                    # Start and end don't match, Thing is a line string
                    thing_2 = LineString(thing)
                else:
                    # Start and end mantch, Thing is a Polygon
                    thing_2 = Polygon(thing)
        else:
            msg = "Unsupported type for Wall.Intersects %s" % type(thing)
            raise NotImplementedError(msg)
        # uses shapely's intersects function
        return thing_1.intersects(thing_2)
        
    def clear_surface(self):
        """ Clears the wall graphic by painting the display Surface white.
        
        Parameters
        ----------
        None
        """
        self.image.fill(WHITE)
        
        
class Guard(Marker):
    """Marker subclass representing a human guard position in the gallery.
    Inherits the to_geometry and clear_surface() functions.
    
    Attributes
    ----------
    name : String
        The name to idenify the guard by
    room_name : String
        The id of the room polygon the guard node is located in
    layer : String
        The display layer for the guard node. Default GUARD_LAYER (3)
    effective_range : Float
        The distance in scale units the guard can cover. Default 15.0
    surface_size: Tuple
        A (width, height) tuple set to twice the width value for display
    rect : Tuple
        The rectangle object representing the display surface area
    image : Surface
        The PyGame display Surface
        
    Methods
    -------
    init_surface()
        Create PyGame surface to display the guard.
    to_dict()
        Returns a dictionary representation of the guard object's data
    from_dict()
        Configures a guard object from a dictionary
    """
    
    name = ""
    room_name = ""
    layer = GUARD_LAYER
    effective_range = 15 
    
    def __init__(
            self, center_pos, name="", room_name="", effective_range=15,
            width=8, color=(128, 0, 128)
        ):
        """
        Parameters
        ----------
        center_pos : Tuple
            The (x,y) location for the guard position
        name : String
            The string identifier for the guard. Default empty
        room_name : String
            The string identifier for room the guard is located in. Default empty
        width: Integer
            Pixel thickness to draw the line Marker on-screen
        color: Tuple
            An (r,g,b) tuple (default (128, 0, 128))
        """
        super().__init__(center_pos, width, color)
        self.center_pos = center_pos
        self.color = color
        self.width = width
        self.effective_range = effective_range
        self.name = name
        self.room_name = room_name
        
    def init_surface(self):
        """ Create pygame Surface to hold the guard graphic. Needs to be called
        before displaying the guard in the application.
        
        Parameters
        ----------
        None
        """
        # Set the background color and set it to be transparent
        self.image = pygame.Surface([self.width * 2, self.width * 2])
        #self.image.set_alpha(80)  # alpha level
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        pygame.draw.circle(
                self.image,
                self.color,
                (self.width, self.width),
                self.width,
                1
            )
        self.rect = self.image.get_rect()
        self.rect.x = self.center_pos[0] - self.width
        self.rect.y = self.center_pos[1] - self.width
        
    def to_dict(self):
        """Create a dictionary object containing the guard object's attributes.
        
        Parameters
        ----------
        None
        """
        return {
            "name": self.name,
            "center_pos": self.center_pos,
            "room": self.room_name,
            "width": self.width,
            "color": self.color,
            "effective_range": self.effective_range
        }

    def from_dict(self, p_dict):
        """Create a guard from object from a dictionary. The only required keys
        are name center_pos, room, width, color, and effective_range. No other 
        guarantees of formatting are made, so it is possible to extend guard objects
        with additional data on load. This could also be dangerous if loading
        dicts from untrusted sources (over the network for example).

        Parameters
        ----------
        p_dict : Dictionary
            required keys are name center_pos, room, width, color, and 
            effective_range. Other keys are added as attributes to the object
        
        Raises
        ------
        KeyError
            If one of the required keys is missing
        """
        # Ensure minimum data is present to construct a guard
        if any([
            "name" not in p_dict.keys(),
            "center_pos" not in p_dict.keys(),
            "room" not in p_dict.keys(),
            "width" not in p_dict.keys(),
            "color" not in p_dict.keys(),
            "effective_range" not in p_dict.keys(),
        ]):
            keys = ", ".join(list(p_dict.keys()))
            raise KeyError("guard dictionary missing required key. Found: %s" % keys)
        # Add all found key value pairs as attributes
        for k in list(p_dict.keys()):
            setattr(self, k, p_dict[k])
        
    
class Device(Marker):
    """A Device is a subclass of a Marker which denotes a security sensor that
    has a fixed senory cone and effective range. Inherits to_geometry and
    clear_surface functions.
    
    Attributes
    ----------
    surface_size: Tuple
        A (width, height) tuple set to twice the width value for display
    center_pos: Tuple
        An (x, y) tuple representing the location of the device marker
    width : Integer
        The size in pixels to display the device marker
    color : Tuple
        The (r,g,b) tuple to use when displaying the device marker
    room_name : String
        The identifer for the room containing the device location
    name : String
        The identifier for the device. Uniqueness is not enforced
    rotation : Float
        the rotation in degrees for the FoV centerline of the device
    effective_range : Float
        the distance in scale units for the FoV of the device
    fov : Float
        The range in degrees for the FoV spread
    ppu_scale : Float
        The number of pixels per scale unit for drawing the FoV
    rect : Tuple
        The rectangle object representing the display surface area
    image : Surface
        The PyGame display Surface
    fov_vertex_list : List
        The list of vertices which make up the FoV cone for the device
    fov_sprite : View
        Contains the sprite to display the associated FoV graphic.
        
    Methods
    -------
    init_surface()
        Create PyGame surface to display the guard.
    change_rotation(new_rotation : Float)
        Change the centerline rotation of the device and recalculate the FoV
    change_fov(new_fov : Float)
        Change the width of the FoV degrees and recalculate the FoV
    change_effective_range(new_range : Float)
        Change the effective range of the device and recalculate the FoV
    fov_points()
        Calculates the location of each point in the FoV cone using the two 
        edges and the centerline as points. Returns a list of tuples containing
        the (x,y) cooridnates.
    fov_cone()
        Creates the FoV sprite for the device
    to_dict()
        Returns a dictionary representation of the device object's data
    from_dict()
        Configures a device object from a dictionary
    """
    surface_size = (0,0)
    center_pos = (0,0)
    width = 0
    color = (0,0,0)
    room_name = ""
    name = ""
    rotation = 0.0
    effective_range = 0
    fov = 0
    ppu_scale = 0
    
    def __init__(self, screen_size, center_pos, room_name="", name="",
                 rotation=0.0, effective_range=0.0, fov_deg=0.0, ppu_scale=1.0,
                 width=4, color=RED
        ):
        """
        Parameters
        ----------
        screen_size : Tuple
            A (width, height) tuple for the display
        center_pos : Tuple
            An (x, y) tuple marknig the device location
        room_name : String
            The identifer for the room containing the device location
        name : String
            The identifer for the the device
        rotation : Float
            the rotation in degrees for the FoV centerline of the device
        effective_range : Float
            the distance in scale units for the FoV of the device
        fov_deg : Float
            The range in degrees for the FoV spread
        ppu_scale : Float
            The number of pixels per scale unit for drawing the FoV
        width : Integer
            The size in pixels to display the devie marker
        color : Tuple
            An (r,g,b) tuple to use when displaying the device marker
        """
        super().__init__(center_pos, width, color)
        self.center_pos = center_pos
        self.room_name = room_name
        self.name = name
        self.effective_range = effective_range
        self.fov = fov_deg
        self.rotation = rotation
        self.color = color
        self.width = width
        self.surface_size = screen_size
        self.ppu_scale = ppu_scale
        
    def init_surface(self):
        if self.fov == 0:
            return

        # Set the background color and set it to be transparent
        self.image = pygame.Surface(self.surface_size)
        #self.image.set_alpha(80)  # alpha level
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        pygame.draw.circle(
                self.image,
                self.color,
                self.center_pos,
                self.width,
                3
            )
        self.rect = self.image.get_rect()
        self.fov_vertex_list = self.fov_points()
        self.fov_cone()
        
    def change_rotation(self, new_rotation):
        """Change the centerline rotation for the device object
        
        Parameters
        ----------
        new_rotation : Float
            the new centerline rotation angle for the devie
        """
        self.rotation = new_rotation
        self.fov_vertex_list = self.fov_points()
    
    def change_fov(self, new_fov):
        """Change the width of the FoV degrees and recalculate the FoV
        
        Parameters
        ----------
        new_fov : Float
            the new angle for the device's FoV polygon
        """
        self.fov = new_fov
        self.fov_vertex_list = self.fov_points()
        
    def change_effective_range(self, new_range):
        """Change the effective range of the device and recalculate the FoV
        
        Parameters
        ----------
        new_fov : Float
            the new angle for the device's FoV polygon
        """
        self.effective_range = new_range
        self.fov_vertex_list = self.fov_points()
        
    def fov_points(self):
        """Calculate the left, center, and right edge point locationss for the
        device's FoV using the center point, rotation, FoV angle, and effective
        range of the device.
        
        Parameters
        ----------
        None
        """
        # Convert the rotation into min and max angles as radians
        angle_e1 = math.radians(self.rotation + (0.5 * self.fov))
        angle_e2 = math.radians(self.rotation - (0.5 * self.fov))
        angle_c = math.radians(self.rotation) # Centerline
        # Caclulate x,y for the edge e1
        e1_x = (self.ppu_scale * self.effective_range) * math.cos(angle_e1) + self.center_pos[0]
        e1_y = (self.ppu_scale * self.effective_range) * math.sin(angle_e1) + self.center_pos[1]
        # Caclulate x,y for the edge e2
        e2_x = (self.ppu_scale * self.effective_range) * math.cos(angle_e2) + self.center_pos[0]
        e2_y = (self.ppu_scale * self.effective_range) * math.sin(angle_e2) + self.center_pos[1]
        # Caclulate x,y for the centerline
        c_x = (self.ppu_scale * self.effective_range) * math.cos(angle_c) + self.center_pos[0]
        c_y = (self.ppu_scale * self.effective_range) * math.sin(angle_c) + self.center_pos[1]
        # Create the list of vertices and return it
        cone = [
            self.center_pos,
            (e1_x, e1_y),
            (c_x, c_y),
            (e2_x, e2_y),
            self.center_pos
        ]
        return cone
        
    def fov_cone(self):
        """Create the View sprite to contain the FoV for the device object.
        
        Parameters
        ----------
        None
        """
        self.fov_sprite = View(
            self.center_pos, self.fov_vertex_list, self.rotation,
            self.effective_range, self.fov, self.surface_size, self.color
        )
        self.fov_sprite.init_surface()
        
    def to_dict(self):
        """Returns a dictionary representation of the device object's data
        
        Parameters
        ----------
        None
        """
        return {
            "name": self.name,
            "center_pos": self.center_pos,
            "room": self.room_name,
            "width": self.width,
            "color": self.color,
            "fov": self.fov,
            "rotation": self.rotation,
            "ppu_scale": self.ppu_scale,
            "effective_range": self.effective_range,
            "fov_vertex_list": self.fov_vertex_list
        }

    def from_dict(self, p_dict):
        """Create a device from object from a dictionary. See parameters for 
        required keys. No other guarantees of formatting are made, so it is 
        possible to extend guard objects with additional data on load. 
        This could also be dangerous if loading dicts from untrusted sources 
        (over the network for example).

        Parameters
        ----------
        p_dict : Dictionary
            required keys are name, center_pos, room, width, color, fov, rotation
            ppu_scale, and effective_range. Other keys are added as attributes 
            to the object.
        
        Raises
        ------
        KeyError
            If one of the required keys is missing
        """
        # Ensure minimum data is present to construct a device
        if any([
            "name" not in p_dict.keys(),
            "center_pos" not in p_dict.keys(),
            "room" not in p_dict.keys(),
            "width" not in p_dict.keys(),
            "color" not in p_dict.keys(),
            "fov" not in p_dict.keys(),
            "rotation" not in p_dict.keys(),
            "ppu_scale" not in p_dict.keys(),
            "effective_range" not in p_dict.keys(),
        ]):
            keys = ", ".join(list(p_dict.keys()))
            raise KeyError("Device missing required key. Found: %s" % keys)
        for k in list(p_dict.keys()):
            setattr(self, k, p_dict[k])
        if "fov_vertex_list" not in list(p_dict.keys()):
            self.fov_points()
            self.fov_cone()
        
        
class Obstacle(pygame.sprite.Sprite):
    """ An Obstacle is a closed simple polygone in CCW/CW order entirely 
    contained within a second closed polygon.
    Parameters:
        room_name: A human-readable string identifier of the Room containing this shape
        vertex_list: list of (x,y) tuples defining shape of the obstacle
        color: An (r,g,b) tuple (default (0,0,0))
    """
    hull_points = []
    color = None
    room_name = ""
    surface_size = None
    layer = OBSTACLE_LAYER
    
    def __init__(self, marks, color=(0, 255, 0), in_room="", screen_sz=None):
        super().__init__()
        self.hull_points = [m.center_pos for m in marks]
        self.color = color
        self.surface_size = screen_sz
        self.room_name = in_room

        
    def init_surface(self):
        if self.surface_size is None:
            x_list = [m[0] for m in self.hull_points]
            y_list = [m[1] for m in self.hull_points]
            win_w = abs(max(x_list) - min(x_list))
            win_h = abs(max(y_list) - min(y_list))
            self.surface_size = [win_w, win_h]
        # Set the background color and set it to be transparent
        self.image = pygame.Surface(self.surface_size)
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        #self.image.set_alpha(40)  # alpha level
        pygame.draw.polygon(
            self.image,
            self.color,
            self.hull_points,
            0  # Filled polygon
        )
        self.rect = self.image.get_rect()
        
    def vertices_to_walls(self):
        """Convert the Hull Points to a set of connected Wall objects"""
        walls = []
        for i in range(len(self.vertex_list) - 1):
            st = self.hull_points[i].center_pos
            ed = self.hull_points[i + 1].center_pos
            w = Wall(st, ed)
            walls.append(w)
        return walls
        
    def to_geometry(self):
        """Return a Polygon object representing this shape in 2D space"""
        return(Polygon(self.hull_points))
    
    def contains(self, thing):
        thing_1 = self.to_geometry()
        if hasattr(thing, "to_geometry"):
            thing_2 = thing.to_geometry()
        elif isinstance(thing, tuple):
            thing_2 = Point(thing)
        elif isinstance(thing, list):
            if len(thing) >= 2:
                if thing[0] != thing[-1]:
                    thing_2 = LineString(thing)
                else:
                    thing_2 = Polygon(thing)
        else:
            msg = "Unsupported type for Obstacle.Contains %s" % type(thing)
            raise Exception(msg)
        return thing_1.contains(thing_2)
        
    def clear_surface(self):
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        
    def to_dict(self):
        """Returns a dictionary with data about the marker for storage or
        display"""
        return {
            "hull_points": self.hull_points,
            "room_name": self.room_name,
            "color": self.color,
            "surface_size": self.surface_size,
        }

    def from_dict(self, p_dict):
        """Create a Guard from a dictionary object. no guarantees of
        formatting are made. So it is possible to extend guard objects
        with additional data on load. This could also be dangerous if loading
        dicts from untrusted sources (over the network for example)"""
        for k in list(p_dict.keys()):
            setattr(self, k, p_dict[k])
            
class Room(pygame.sprite.Sprite):
    """A room is a closed polygon (with holes), in CCW/CW order.
    Parameters:
        name: A string identifier for human reference
        vertex_list: list of (x,y) tuples defining shape
        color: An (r,g,b) tuple (default (0,255,0))
    """
    vertex_list = []
    name = None
    color = None
    obstacles = []
    surface_size = None
    layer = ROOM_LAYER
    floor = None
    
    def __init__(self, name, marker_list, color=(0, 255, 0), screen_sz=None, floor=0):
        super().__init__()
        self.vertex_list = [m.center_pos for m in marker_list]
        self.color = color
        self.name = name
        self.obstacles = []
        self.surface_size = screen_sz
        self.floor = floor
        
    def init_surface(self):
        # Set the background color and set it to be transparent
        self.image = pygame.Surface(self.surface_size)
        #self.image.set_alpha(80)  # alpha level
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        #self.image.set_alpha(80)  # alpha level
        pygame.draw.polygon(
            self.image,
            self.color,
            self.vertex_list,
            0  # Filled polygon
        )
        self.rect = self.image.get_rect()
        
    def add_obstacle(self, obs):
        """Add an Obstacle object to the list of contained obstacles"""
        if not isinstance(obs, Obstacle):
            raise Exception("%s is not a Obstacle Object" % str(type(obs)))
        self.obstacles.append(obs)
    
    def vertices_to_walls(self):
        """Convert the vertices to a set of connected Wall objects"""
        walls = []
        for i in range(len(self.vertex_list) - 1):
            st = self.vertex_list[i].center_pos
            ed = self.vertex_list[i + 1].center_pos
            w = Wall(st, ed)
            walls.append(w)
        return walls
        
    def to_geometry(self):
        """Return a Polygon object representing this shape in 2D space.
        Include obstructions as holes in the shape."""
        holes = [[v for v in obs.hull_points] for obs in self.obstacles]
        return(Polygon(self.vertex_list, holes))
    
    def contains(self, thing):
        thing_1 = self.to_geometry()
        if hasattr(thing, "to_geometry"):
            thing_2 = thing.to_geometry()
        elif isinstance(thing, tuple):
            thing_2 = Point(thing)
        elif isinstance(thing, list):
            if len(thing) >= 2:
                if thing[0] != thing[-1]:
                    thing_2 = LineString(thing)
                else:
                    thing_2 = Polygon(thing)
        else:
            msg = "Unsupported type for Room.Contains %s" % type(thing)
            raise Exception(msg)
        #print("Comparing with %s" % type(thing_2))
        return thing_1.contains(thing_2)
        
    def clear_surface(self):
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        
    def to_dict(self):
        """Returns a dictionary with data about the marker for storage or
        display"""
        return {
            "vertex_list": self.vertex_list,
            "name": self.name,
            "color": self.color,
            "floor": self.floor,
            "surface_size": self.surface_size,
            "obstacles": [o.to_dict() for o in self.obstacles]
        }

    def from_dict(self, p_dict):
        """Create a Guard from a dictionary object. no guarantees of
        formatting are made. So it is possible to extend guard objects
        with additional data on load. This could also be dangerous if loading
        dicts from untrusted sources (over the network for example)"""
        for k in list(p_dict.keys()):
            #print(k)
            if k == "obstacles":
                for k2 in p_dict[k]:
                    obs = Obstacle([])
                    obs.from_dict(k2)
                    obs.init_surface()
                    self.obstacles.append(obs)
            else:
                setattr(self, k, p_dict[k])
        #print(self.surface_size)
        
        
class Background(pygame.sprite.Sprite):
    surface_size = None
    bg_image = None
    bg_color = WHITE
    alpha_color = WHITE
    
    def __init__(self,
                 image_file,
                 bg_color=WHITE,
                 alpha_color=WHITE
        ):
        super().__init__()
        # create a surface object, backgroud image is drawn on it.
        png_obj = png.Reader(image_file)
        png_data = png_obj.read()
        x_pixels = png_data[0]
        y_pixels = png_data[1]
        self.surface_size = [x_pixels, y_pixels]
        self.bg_color = bg_color
        self.alpha_color = alpha_color
        self.bg_image = image_file
    
    def init_surface(self):
        self.image = pygame.Surface(self.surface_size)
        #print(self.bg_image)
        # create the display surfaces object of specific dimension..e(X, Y)
        loaded = pygame.image.load(self.bg_image)
        
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        self.image.blit(loaded, (0, 0))  # (0,0) is top-left
        self.rect = self.image.get_rect()
        
    def to_dict(self):
        """Returns a dictionary with data about the marker for storage or
        display"""
        return {
            "surface_size": self.surface_size,
            "bg_image": self.bg_image,
            "bg_color": self.bg_color,
            "alpha_color": self.alpha_color
        }

    def from_dict(self, p_dict):
        """Create a Guard from a dictionary object. no guarantees of
        formatting are made. So it is possible to extend guard objects
        with additional data on load. This could also be dangerous if loading
        dicts from untrusted sources (over the network for example)"""
        for k in list(p_dict.keys()):
            setattr(self, k, p_dict[k])
        
class Floor():
    """A Floor is a container for the Background PNG and the
    layered Sprite Group representing the other objects on this floor of the
    plan.
    Parameters:
        floor: Int for ordering backgrounds if multiple are used
        image_data: the Image File bytes to create File objects from
        color: An (r, g, b) tuple (default (0,255,0))
    """

    floor_name = None
    surface_size = None
    all_sprites = None
    background = None
    rooms = None
    guard_points = None
    device_points = None
    created_stack = None
    ceiling = 8
    ppu_scale = 0
    upp_scale = 0
    scale_points = []
    floor_number = 0
    
    def __init__(self,
                 background, floor_number=1, scale_points=[], floor_name=""
        ):
        if not isinstance(background, Background):
            raise Exception("Must be background object")
            
        self.rooms = []
        self.guard_points = []
        self.device_points = []
        self.created_stack = []
        self.background = background
        self.surface_size = background.surface_size
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.all_sprites.add(background)
        self.scale_points = scale_points
        self.floor_number = floor_number
        self.floor_name = floor_name
        
            
    def set_scale(self, obj_len):
        pos_1 = self.scale_points[0]
        pos_2 = self.scale_points[1]
        w = Wall(pos_1, pos_2)
        line = w.to_geometry()
        self.ppu_scale = line.length / obj_len
        self.upp_scale = obj_len / line.length
        
    def to_dict(self):
        """Returns a dictionary with data about the marker for storage or
        display"""
        return {
            "floor_name": self.floor_name,
            "floor_number": self.floor_number,
            "ceiling": self.ceiling,
            "scale_points": self.scale_points,
            "ppu_scale": self.ppu_scale,
            "upp_scale": self.upp_scale,
            "background": self.background.to_dict(),
            "surface_size": self.surface_size
        }

    def from_dict(self, p_dict):
        """Create a Guard from a dictionary object. no guarantees of
        formatting are made. So it is possible to extend guard objects
        with additional data on load. This could also be dangerous if loading
        dicts from untrusted sources (over the network for example)"""
        for k in list(p_dict.keys()):
            if k == "background":
                continue # has to be built and passed into the constructor
            setattr(self, k, p_dict[k])