# -*- coding: utf-8 -*-
import networkx as nx
import pickle
from matplotlib import pyplot as plt
import matplotlib.patches as patches
from networkx.algorithms.coloring import greedy_color
from networkx.algorithms import approximation
from networkx.algorithms.covering import min_edge_cover
import imageio
from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial import ConvexHull, convex_hull_plot_2d
from shapely.geometry import Point, LineString, MultiLineString, Polygon, LinearRing
import triangle as tr
from math import cos, sin
import multiprocessing as mp

def polygons_to_graph(shape_list):
    G = nx.Graph()
    pos_list = []
    for room in shape_list:
        obstacles = [list(o.coords) for o in list(room.interiors)]
        print(obstacles)
        room_coords = room.exterior.coords[0:-1]
        G.add_node(0, coords=room_coords[0], node_type="room vertex")
        pos_list.append(room_coords[0])
        for i in range(1,len(room_coords)):
            p = room_coords[i]
            pos_list.append(p)
            G.add_edge(i-1, i, segment=True, hole=False, tess=False)
            G.nodes[i]["coords"] = p
            G.nodes[i]["node_type"] = "room vertex"
            # close the shape edges
            if i == len(room_coords)-1:
                G.add_edge(i, 0, segment=True, hole=False, tess=False)
        for h in obstacles:
            print("hole", h)
            start = len(G.nodes())
            #print("hole started at node %d" % start)
            hvp = tuple([float(f) for f in h[0]])
            G.add_node(start, coords=hvp, room=room.name, node_type="hole vertex")
            pos_list.append(hvp)
            for j in range(1,len(h)):
                hvp = tuple([float(f) for f in h[j]])
                pos_list.append(hvp)
    return (G, pos_list)

def mp_agp_floorplan(p, q):
    work = None
    done = False
    while not done:
        while work == None:
            work = p.get()
            print("got work")
            print(work)
        floor = work["shapes"]
        if "max_area" in work.keys():
            max_area = work["max_area"]
        else:
            max_area = None
        gallery_name = work["name"]
        shape_list = work["shapes"]
        G, pos = polygons_to_graph(shape_list)
        print("got graph, triangulating")
        G_tri, tri_res = triangulate_floor(shape_list, max_area)
        gallery_colored = greedy_color(G_tri)
        
        for k in gallery_colored.keys():
            v = gallery_colored[k]
            G_tri.nodes[k]["group"] = v
        solution=({
            "graph": G_tri, 
            "coloring": gallery_colored,
            "triangle": tri_res
        })
        q.put(solution)
        print("put solution")
        done = True

def mp_solve_floors(floors):
    ctx = mp.get_context('fork')
    q = ctx.Queue()
    p = ctx.Queue()
    procs = []
    for i in range(0,len(floors)):
        proc = ctx.Process(target=mp_agp_floorplan, args=(p,q))
        proc.start()
        procs.append(proc)
    results = []
    
    for f in floors:
        shapes = []
        for room in f.rooms:
            obstacles = [o.hull_points for o in room.obstacles]
            room_poly = Polygon(room.vertex_list, obstacles)
            shapes.append(room_poly)
        w = {
            "name": f.floor_name,
            "shapes": shapes,
        }
        p.put(w)
    while True:
        r = q.get()
        print(r)
        results.append(r)
    for proc in procs:
        proc.join()
    return results

def get_endpoint(p, angle, length):
    """Convert angle and magnitude to end point"""
    x1, y1 = p
    return ((x1 + length*cos(angle), y1 + length*sin(angle)))

def assign_triangles(graph, triangulated, group_id):
    """Assign a triangle segment to the closest guard from the given group"""
    guard_nodes = [n for n in graph.nodes() if graph.nodes[n]["group"] == group_id]
    triangles = {k:[] for k in guard_nodes}

    for i in range(len(triangulated["triangles"])):
        t = triangulated["triangles"][i]
        t_poly = Polygon([graph.nodes[p]["coords"] for p in t])

        # if triangle touches a guard directly at any point
        if t[0] in guard_nodes:
            triangles[t[0]].append(t_poly)
        elif t[1] in guard_nodes:
            triangles[t[1]].append(t_poly)
        elif t[2] in guard_nodes:
            triangles[t[2]].append(t_poly)
        else:
            dists = {
                k: t_poly.distance(Point(graph.nodes[k]["coords"])) for k in guard_nodes
            }
            close = min(dists, key=dists.get)
            #print("closest: %d" % close)
            triangles[close].append(t_poly)
    return triangles

def count_groups(colored_dict):
    """Count the number of groups present in the solution"""
    seen = []
    for k in list(colored_dict.keys()):
        if colored_dict[k] not in seen:
            seen.append(colored_dict[k])
    return(len(seen))

def group_symbol(group_i):
    """Return a symbol for plotting given a group ID
    currently 7 groups can be represented
    """
    sym_table = ['o','d','s','*',"P","X","D"]
    return sym_table[group_i]

def group_color(group_i):
    """Return a color for plotting given a group ID
    currently 7 groups can be represented
    """
    color_table = ['red','blue','green','orange','gray','purple', 'teal']
    return color_table[group_i]
    
def nodes_by_fields(G, features, values, with_data=True):
    """Match all nodes in a given graph based on a set of features and values 
    to select on"""
    if len(features) != len(values):
        raise Exception("Feature and Value vector lengths dont match")
    return [G.node[i] for i in range(len(G.nodes)) if all(
                [G.node[i][features[j]] == values[j] for j in range(len(features))]
            )
    ]

def create_cell_graph(points):
    """Create constrained Voronoi graph"""

def display_cell_graph(vor, bgd_file, shape_list):
    """Display the constrained Voronoi diagram"""
    img = imageio.imread(bgd_file)
    imw,imh,z = img.shape
    
    shade = [[o.hull_points for o in r.obstacles] for r in shape_list]
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(12,12))

def is_within(poly1, poly2):
    """Determine if the poly1 is entirely inside poly2"""
    shape_1 = Polygon(poly1)
    shape_2 = Polygon(poly2)
    return shape_1.within(shape_2)
    
    
def contains(poly1, poly2):
    """Determine if the poly1 completely surrounds poly2"""
    shape_1 = Polygon(poly1)
    shape_2 = Polygon(poly2)
    return shape_1.contains(shape_2)


def any_contains(container_set, obj):
    if isinstance(obj, tuple):
        p = Point(obj)
    elif isinstance(obj, list):
        if len(obj) > 2 and obj[0] == obj[-1]:
            p = Polygon(obj)
        else:
            p = LineString(obj)
    elif any([
        isinstance(obj, Polygon),
        isinstance(obj, Point),
        isinstance(obj, LineString)
        ]):
        p = obj
    else:
        raise Exception("Unknown object type %s" % type(obj))
    for i in range(len(container_set)):
        cont = container_set[i]
        if isinstance(cont, list):
            poly = Polygon(cont)
        elif isinstance(cont, Polygon):
            poly = cont
        else:
            raise Exception("Unknown container type %s" % type(cont))
        if poly.contains(p):
            return i
    return None
     
     
def calculate_coverage_areas(G, room=None):
    """Calculate coverage area for a deployment"""
    
def calculate_coverage_polygon(G, room=None):
    """Turn the AoR into a polygon"""
    
    
def build_graph(shape_list):
    """Create a graph representation containing each room in a list of rooms
    Designate the room edges as segments and the obstacle vert    
    """
    G = nx.Graph()
    pos_list = []
    for room in shape_list:
        #print("Converting %s to Graph" % room.name)
        obstacles = [o.hull_points for o in room.obstacles]
        room_poly = Polygon(room.vertex_list, obstacles)
        room_coords = room_poly.exterior.coords[0:-1]
        G.add_node(0, coords=room_coords[0], room=room.name, node_type="room vertex")
        pos_list.append(room_coords[0])
        for i in range(1,len(room_coords)):
            p = room_coords[i]
            pos_list.append(p)
            G.add_edge(i-1, i, segment=True, hole=False, tess=False, room=room.name)
            G.nodes[i]["coords"] = p
            G.nodes[i]["room"] = room.name
            G.nodes[i]["node_type"] = "room vertex"
            # close the shape edges
            if i == len(room_coords)-1:
                G.add_edge(i, 0, segment=True, hole=False, tess=False, room=room.name)
        for h in obstacles:
            start = len(G.nodes())
            #print("hole started at node %d" % start)
            hvp = tuple([float(f) for f in h[0]])
            G.add_node(start, coords=hvp, room=room.name, node_type="hole vertex")
            pos_list.append(hvp)
            for j in range(1,len(h)):
                hvp = tuple([float(f) for f in h[j]])
                pos_list.append(hvp)
                on = start + j
                G.add_edge(on-1, on, segment=True, hole=True, tess=False, room=room.name)
                G.nodes[on]["coords"] = hvp
                G.nodes[on]["room"] = room.name
                G.nodes[on]["node_type"] = "hole vertex"
                # close the shape edges
                if j == len(h)-1:
                    G.add_edge(on, start, segment=True, hole=True, tess=False, room=room.name)
                    #print("Hole closed at node %d" % on)
    return G, pos_list
        
def triangulate_floor(shape_list, bgd_file, max_area=None):
    """Create a triangulated representation of the graph containing each room 
    and obstacle
    """
    #img = imageio.imread(bgd_file)
    G, pos_list = build_graph(shape_list)
    G2 = G.copy()
    tri_results = {}
    #nx.draw_networkx(G, pos_list)
    #plt.imshow(img, zorder=0)
    #plt.show()
    #return
    for room in shape_list:
        #print("Triangulating %s" % room.name)
        obstacles = [o.hull_points for o in room.obstacles]
        verts = [G.nodes[n]["coords"] for n in G.nodes()]
        #print(verts)
        segs = [tuple(e[0:2]) for e in G.edges(data=True)]# if e[2]["segment"]]
        obst_points = []
        for interior in obstacles:
            hole_rp = Polygon(interior).representative_point()
            hp = [list(v)[0] for v in list(hole_rp.xy)]
            obst_points.append(hp)
        #print("%d obstacles in room" % len(obst_points))
        #print("%d segments gathered" % len(segs))

        if len(obst_points) > 0:
            #print("found obstruction. Calling with holes")
            tri_dict = {
                "vertices": verts,
                "segments": segs,
                "holes": obst_points
            }
        else:
            #print("No obstructions. Calling without holes")
            tri_dict = {
                "vertices": verts,
                "segments": segs
            }
        if max_area is not None:
            opt_string = "pea%.2f" % float(max_area)
        else:
            opt_string = "pe"
        #print(tri_dict)
        triangulated = tr.triangulate(tri_dict, opt_string)
        tri_results[room.name] = triangulated
        #print(triangulated)
        for i in range(len(triangulated["vertices"])):
            if i not in G2.nodes:
                G2.add_node(i, 
                    coords=triangulated["vertices"][i],
                    room=room.name,
                    node_type="steiner"
                )
        for e in triangulated["edges"]:
            if list(e) not in list(G2.edges()):
                G2.add_edge(e[0], e[1], 
                    segment=False, hole=False, tess=True
                )
    return G2, tri_results
    
def agp_floorplan(shape_list, bgd_file, max_area=None):
    """Solve the AGP placement using the different shapes contained in the
    floor. """
    G_tri, tri_res = triangulate_floor(shape_list, bgd_file, max_area)
    nodes = G_tri.nodes(data=True)
    pos_list = [n[1]["coords"] for n in nodes]
    gallery_colored = greedy_color(G_tri)
    
    for k in gallery_colored.keys():
        v = gallery_colored[k]
        G_tri.nodes[k]["group"] = v
    return(G_tri, gallery_colored, tri_res)
    
def missing_node_attr(attr_name, G):
    return all([
        attr_name in G.node[j].keys() for j in range(len(G.nodes))
    ])

def missing_edge_attr(attr_name, G):
    return all([
        attr_name in G.edge[j].keys() for j in range(len(G.edges))
    ])

def unique(list_items):
    out = []
    for i in list_items:
        if i not in out:
            out.append(i)
    return out

def node_index_from_position(pos_list, point_xys):
    return [pos_list.index(p) for p in point_xys]

def aor_coloring(G, pos_list, bgd_file, shape_list, guards):
    img = imageio.imread(bgd_file)
    shade = [[o.hull_points for o in r.obstacles] for r in shape_list]

def display_graph(G, pos_list, color_map, bgd_file, shape_list):
    """Generate a Plot of the graph overlayed on the background image"""
    img = imageio.imread(bgd_file)
    shade = [[o.hull_points for o in r.obstacles] for r in shape_list]
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(12,12))
    for room_blocks in shade:
        for block in room_blocks:
            patch = patches.Polygon(block, color='black', zorder=1, alpha=0.25)
            ax1.add_patch(patch)
    win = plt.gcf()
    win.canvas.set_window_title('Polygon Triangulation Graph')
    nx.draw(G, pos_list, node_color=color_map, node_size=25, ax=ax1)
    plt.imshow(img, zorder=0)
    plt.title("")
    plt.show()    

    
    
