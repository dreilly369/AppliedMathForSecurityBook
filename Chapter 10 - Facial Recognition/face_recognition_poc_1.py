# -*- coding: utf-8 -*-
from imutils import face_utils
import numpy as np
import pandas as pd
import imutils
import dlib
import cv2
from scipy.spatial import ConvexHull
from shapely.geometry.polygon import Polygon, LineString
import os
from faker import Faker
import imageio


image_paths = []
fake = Faker()
IMG_W = 300
shape_predictor = "facial_model/shape_predictor_68_face_landmarks.dat"
# initialize dlib's face detector (HOG-based) and then create
# the facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(shape_predictor)
# load the input image, resize it, and create a grayscale working copy
face_collection = []
fake_names = {}

def line_length(point_a, point_b):
    line = LineString((point_a, point_b))
    return line.length
    
def get_image_files(start_at, located=[]):
    # recurse from root directory, grab filepaths
    for root, dirs, files in os.walk(start_at):
        for fname in files:
            if ".txt" in fname:
                continue
            located.append(os.path.join(root, fname))
        for next_root in dirs:
            get_image_files(next_root, located)
    return located

def shape_to_np(shape, dtype="int"):
    # initialize the list of (x, y)-coordinates
    coords = np.zeros((68, 2), dtype=dtype)
 
    # loop over the 68 facial landmarks and convert them
    # to a tuple of (x, y) coordinates
    for i in range(0, 68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
 
    # return the list of (x, y) coordinates
    return coords

def process_gif(file_path):
    gif = imageio.mimread(file_path)
    img = cv2.cvtColor(gif[0], cv2.COLOR_RGB2BGR)
    image = imutils.resize(img, width=IMG_W)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
def process_jpg(file_path):
    img = cv2.imread(file_path)
    if img is None:
        print("None from process_jpg")
        return
    image = imutils.resize(img, width=IMG_W)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def locate_landmarks(image_file):
    gray = process_jpg(image_file)
    if gray is None:
        return {}
    # clone the resized image to display markers
    clone = gray.copy()
    # detect faces in the grayscale image
    rects = detector(clone, 1)
    feature_coordinates = {}
    # loop over the facial area rectangles
    for (i, rect) in enumerate(rects):
        # determine the facial landmarks for the face region, then
        # convert the landmark (x, y)-coordinates to a NumPy array
        shape = predictor(clone, rect)
        shape = shape_to_np(shape)
        # loop over the face parts individually
        for (part_name, (i, j)) in face_utils.FACIAL_LANDMARKS_IDXS.items():
            feature_coordinates[part_name] = []
            # loop over the subset of facial landmarks, saving each X,Y tuple
            for x, y in shape[i:j]:
                feature_coordinates[part_name].append((x, y))
        face_points = []
        for n in feature_coordinates.keys():
            face_points += feature_coordinates[n]
        feature_coordinates["hull"] = face_points
    return feature_coordinates


image_paths = get_image_files("facial_model/faces94", image_paths)
image_paths = get_image_files("facial_model/faces95", image_paths)

for image_file in image_paths:
    print("on", image_file)
    if "male" in image_file:
        user_id = os.path.basename(image_file).split(".")[0]
        name = fake.name_male()
    elif "female" in image_file:
        user_id = os.path.basename(image_file).split(".")[0]
        name = fake.name_female()
    elif "lfw_funneled" in image_file:
        parts = image_file.split("/")
        user_id = parts[-2]
        name = user_id
        print("LFW: %s" % name)
    else:
        name = fake.name()
        user_id = os.path.basename(image_file).split(".")[0]
    name = name.replace(" ", "_")
    if user_id not in fake_names.keys():
        fake_names[user_id] = name
        
    feature_coordinates = locate_landmarks(image_file)
    if len(feature_coordinates.keys()) < 8:
        continue
    face_points = feature_coordinates["hull"]
    nose_points = feature_coordinates["nose"]
    leye_points = feature_coordinates["left_eye"]
    reye_points = feature_coordinates["right_eye"]
    lbrow_points = feature_coordinates["left_eyebrow"]
    rbrow_points = feature_coordinates["right_eyebrow"]
    mouth_points = feature_coordinates["mouth"]
    jaw_points = feature_coordinates["jaw"]
    if any([
        len(jaw_points) < 1,
        len(mouth_points) < 1,
        len(nose_points) < 1,
        len(leye_points) < 1,
        len(reye_points) < 1,
        len(lbrow_points) < 1,
        len(rbrow_points) < 1
    ]):
        print("not including %s" % image_file)
        continue

    # Eye Features
    left_so_node = feature_coordinates["left_eyebrow"][2]
    right_so_node = feature_coordinates["right_eyebrow"][3]
    left_ue_node = feature_coordinates["left_eye"][1]
    right_ue_node = feature_coordinates["right_eye"][2]
    left_io_node = feature_coordinates["left_eye"][5]
    right_io_node = feature_coordinates["right_eye"][4]
    left_oc_node = feature_coordinates["left_eye"][3]
    right_oc_node = feature_coordinates["right_eye"][0]
    left_ic_node = feature_coordinates["left_eye"][0]
    right_ic_node = feature_coordinates["right_eye"][3]
    
    # Nose Features
    bridge_top = feature_coordinates["nose"][0]
    bridge_btm = feature_coordinates["nose"][3]
    nose_ledge = feature_coordinates["nose"][8]
    nose_btm = feature_coordinates["nose"][6]
    nose_redge = feature_coordinates["nose"][4]
    
    # Mouth Features
    lmouth = feature_coordinates["mouth"][6]
    rmouth = feature_coordinates["mouth"][0]
    upper_lip_ctr = feature_coordinates["mouth"][3]
    lower_lip_ctr = feature_coordinates["mouth"][9]
    
    # Jaw Features
    right_temple = feature_coordinates["jaw"][0]
    chin_center = feature_coordinates["jaw"][8]
    left_temple = feature_coordinates["jaw"][16]
    
    face_hull = ConvexHull(face_points)
    nose_hull = [nose_points[0]]
    for p in nose_points[4:]:
        nose_hull.append(p)
    nose_hull.append(nose_points[0])
    nose_poly = Polygon(nose_hull)
    
    mouth_hull = mouth_points[:12]
    mouth_hull.append(mouth_points[0])
    mouth_poly = Polygon(mouth_hull)
    leye_poly = Polygon(leye_points)
    reye_poly = Polygon(reye_points)
    chin_tri = Polygon([lmouth, chin_center, rmouth,lmouth])
    center_tri = Polygon([left_oc_node, nose_btm, right_oc_node, left_oc_node])
    eyebrow_tri = Polygon([lbrow_points[-1], bridge_top, rbrow_points[0], lbrow_points[-1]])
    left_tri = Polygon([lbrow_points[-1], left_temple, chin_center, lbrow_points[-1]])
    right_tri = Polygon([rbrow_points[0], right_temple, chin_center, rbrow_points[0]])
    face_dict = {}
    face_dict["name"] = fake_names[user_id]
    face_hull_edges = [list(simplex) for simplex in face_hull.simplices]
    face_hull_points = []
    for n1_i, n2_i in face_hull_edges:
        loc_1 = face_points[n1_i]
        face_hull_points.append(loc_1)
        loc_2 = face_points[n2_i]
        face_hull_points.append(loc_2)
    face_poly = Polygon(face_hull_points, [
        nose_poly.exterior.coords,
        leye_poly.exterior.coords,
        reye_poly.exterior.coords,
        mouth_poly.exterior.coords
    ])

    face_dict["outter_eyes"] = line_length(left_oc_node, right_oc_node)  # This line angle sets base head angle
    face_dict["inner_eyes"] = line_length(left_ic_node, right_ic_node)  # measure between Inner Canthuses
    face_dict["right_eye_horz"] = line_length(right_ic_node, right_oc_node)  # measure between UE and IO right eye 
    face_dict["right_eye_vert"] = line_length(right_ue_node, right_io_node)  # measure between IC and OC right eye 
    face_dict["right_ic_nose_top"] = line_length(right_ic_node, bridge_top)
    face_dict["right_ic_nose_btm"] = line_length(right_ic_node, bridge_btm)
    face_dict["right_oc_nose_btm"] = line_length(right_oc_node, bridge_btm)
    face_dict["left_eye_horz"] = line_length(left_oc_node, left_ic_node)
    face_dict["left_eye_vert"] = line_length(left_ue_node, left_io_node)
    face_dict["left_ic_nose_top"] = line_length(left_ic_node, bridge_top)
    face_dict["left_ic_nose_btm"] = line_length(left_ic_node, bridge_btm) 
    face_dict["left_oc_nose_btm"] = line_length(left_oc_node, bridge_btm)
    face_dict["mouth_horz"] = line_length(lmouth, rmouth) 
    face_dict["mouth_vert"] = line_length(upper_lip_ctr, lower_lip_ctr)
    face_dict["nose_horz"] = line_length(nose_ledge, nose_redge)
    face_dict["nose_vert"] = line_length(bridge_top, nose_btm)
    face_dict["lmouth_nose_ledge"] = line_length(lmouth, nose_ledge)
    face_dict["rmouth_nose_redge"] = line_length(rmouth, nose_redge)
    face_dict["chin_lower_lip"] = line_length(chin_center, lower_lip_ctr)
    face_dict["chin_lmouth"] = line_length(chin_center, lmouth)
    face_dict["chin_rmouth"] = line_length(chin_center, rmouth)
    face_dict["face_horz"] = line_length(left_temple, right_temple)
    face_dict["face_vert"] = line_length(chin_center, bridge_top)
    face_dict["rmouth_right_temple"] = line_length(rmouth, right_temple)
    face_dict["lmouth_left_temple"] = line_length(lmouth, left_temple)
    face_dict["rmouth_right_oc_node"] = line_length(rmouth, right_oc_node)
    face_dict["lmouth_left_oc_node"] = line_length(lmouth, left_oc_node)
    face_dict["nose_ledge_left_oc_node"] = line_length(nose_ledge, left_oc_node)
    face_dict["nose_redge_right_oc_node"] = line_length(nose_redge, right_oc_node)
    face_dict["nose_ledge_upper_lip_ctr"] = line_length(nose_ledge, upper_lip_ctr)
    face_dict["nose_redge_upper_lip_ctr"] = line_length(nose_redge, upper_lip_ctr)
    face_dict["rbrow_right_temple"] = line_length(rbrow_points[0], right_temple)
    face_dict["rbrow_right_oc_node"] = line_length(rbrow_points[0], right_oc_node)
    face_dict["lbrow_left_temple"] = line_length(lbrow_points[0], rbrow_points[-1])
    face_dict["right_ic_node_rbrow"] = line_length(right_ic_node, rbrow_points[-1])
    face_dict["left_ic_node_lbrow"] = line_length(left_ic_node, lbrow_points[0])
    face_dict["right_ue_node_rbrow"] = line_length(right_ue_node, rbrow_points[-1])
    face_dict["left_ue_node_lbrow"] = line_length(left_ue_node, lbrow_points[0])
    face_dict["lbrow_left_temple"] = line_length(lbrow_points[-1], left_temple)
    face_dict["lbrow_left_oc_node"] = line_length(lbrow_points[-1], left_oc_node)
    face_dict["right_ic_node_bridge_btm"] = line_length(bridge_btm, rbrow_points[-1])
    face_dict["left_ic_node_bridge_btm"] = line_length(bridge_btm, lbrow_points[0])
    face_dict["right_ic_node_bridge_top"] = line_length(bridge_top, rbrow_points[-1])
    face_dict["left_ic_node_bridge_top"] = line_length(bridge_top, lbrow_points[0])
    face_dict["nose_ledge_bridge_btm"] = line_length(nose_ledge, bridge_btm)
    face_dict["nose_redge_bridge_btm"] = line_length(nose_redge, bridge_btm)
    face_dict["right_oc_node_right_temple"] = line_length(right_oc_node, right_temple)
    face_dict["left_oc_node_left_temple"] = line_length(left_oc_node, left_temple)
    face_dict["face_area"] = face_poly.area
    face_dict["mouth_area"] = mouth_poly.area
    face_dict["nose_area"] = nose_poly.area
    face_dict["left_eye_area"] = leye_poly.area
    face_dict["right_eye_area"] = reye_poly.area
    face_dict["chin_tri_area"] = chin_tri.area
    face_dict["center_tri_area"] = center_tri.area
    face_dict["eyebrow_tri_area"] = eyebrow_tri.area
    face_dict["left_tri_area"] = left_tri.area
    face_dict["right_tri_area"] = right_tri.area
    face_dict["eye_symmetry"] = leye_poly.area / reye_poly.area
    face_dict["leye_ratio"] = face_poly.area / leye_poly.area
    face_dict["reye_ratio"] = face_poly.area / reye_poly.area
    face_dict["nose_ratio"] = face_poly.area / nose_poly.area
    face_dict["mouth_ratio"] = face_poly.area / mouth_poly.area
    
    face_dict["file"] = image_file

    for k in feature_coordinates.keys():
        i = 0
        if k == "hull":
            continue
        points = feature_coordinates[k]
        for p in points:
            i += 1
            n = "%s_%d" % (k, i)
            face_dict[n + "_x"] = p[0]
            face_dict[n + "_y"] = p[1]
    face_series = pd.Series(face_dict)
    face_collection.append(face_series)
faces_df = pd.DataFrame(face_collection)
faces_df.to_csv("facial_geometry.csv")
