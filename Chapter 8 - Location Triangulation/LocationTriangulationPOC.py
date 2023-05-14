# -*- coding: utf-8 -*-

"""
Web portal for geolocating Cellphone and IoT devices using OpenCellID
@author: dreilly
"""
import requests
import json
import pyproj
import shapely
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from matplotlib import pyplot as plt
from functools import partial
from shapely.geometry import MultiPolygon, Polygon, Point, GeometryCollection
from shapely.ops import transform
import geojson
import os
from os import environ as env
from shapely.ops import cascaded_union

token = env["OPENCELL_TOKEN"]
UWL_URL = "https://us1.unwiredlabs.com/v2/process.php"
EMPTY = GeometryCollection()

def get_shapely_circle(x):
    lat = x["lat"]
    lon = x["lon"]
    radius = x["accuracy"]
    local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(
        lat, lon
    )
    wgs84_to_aeqd = partial(
        pyproj.transform,
        pyproj.Proj("+proj=longlat +datum=WGS84 +no_defs"),
        pyproj.Proj(local_azimuthal_projection),
    )
    aeqd_to_wgs84 = partial(
        pyproj.transform,
        pyproj.Proj(local_azimuthal_projection),
        pyproj.Proj("+proj=longlat +datum=WGS84 +no_defs"),
    )

    center = Point(float(lon), float(lat))
    point_transformed = transform(wgs84_to_aeqd, center)
    buffer = point_transformed.buffer(radius)
    # Get the polygon with lat lon coordinates
    circle_poly = transform(aeqd_to_wgs84, buffer)
    return circle_poly

def lookup_location(cells, radio = "gsm"):
    """Get location guess from Mapbox API using the passed in cells"""
    payload = {"token": token, "radio": radio, "mcc": 310, "mnc": 410,
                "cells": cells,
               "address": 1
              }
    response = requests.request("POST", UWL_URL, data=json.dumps(payload))
    return json.loads(response.text)

def lookup_towers(cells, radio="gsm"):
    """Lookup the locations for all towers passed in"""
    
    tower_locations = []
    for cell in cells:
        payload = {
            "token": token, "radio": cell["radio"],
            "mcc": 310, "mnc": 410,
            "cells": [cell],       
            "address": 1,
        }
        response = requests.request("POST", UWL_URL, data=json.dumps(payload))
        tower_data = json.loads(response.text)
        tower_locations.append(tower_data)
    return tower_locations

def partition(poly_a, poly_b):
    """
    Splits polygons A and B into their differences and intersection.
    """
    if not poly_a.intersects(poly_b):
        return poly_a, poly_b, EMPTY
    only_a = poly_a.difference(poly_b)
    only_b = poly_b.difference(poly_a)
    inter  = poly_a.intersection(poly_b)
    return only_a, only_b, inter


def eliminate_small_areas(poly, small_area):
    """
    Eliminates tiny parts of a MultiPolygon (or Polygon)
    """
    if isinstance(poly, Polygon):
        if poly.area < small_area:
            return EMPTY
        else:
            return poly
    assert isinstance(poly, MultiPolygon)
    l = [p for p in poly if p.area > small_area]
    if len(l) == 0:
        return EMPTY
    if len(l) == 1:
        return l[0]
    return MultiPolygon(l)


def cascaded_intersections(poly1, lst_poly):
    """
    Splits Polygon poly1 into intersections of/with list of other polygons.
    """

    result = [(lst_poly[0], (0,))]

    for i, poly in enumerate(lst_poly[1:], start=1):

        current = []

        while result:
            r_geo, res_idxs = result.pop(0)
            only_res, only_poly, inter = partition(r_geo, poly)
            for geo, idxs in ((only_res, res_idxs), (inter, res_idxs + (i,))):
                if not geo.is_empty:
                    current.append((geo, idxs))
        curr_union = cascaded_union([elt[0] for elt in current])
        only_poly = poly.difference(curr_union)
        if not only_poly.is_empty:
            current.append((only_poly, (i,)))
        result = current

    for r in range(len(result)-1, -1, -1):
        geo, idxs = result[r]
        if poly1.intersects(geo):
            inter = poly1.intersection(geo)
            result[r] = (inter, idxs)
        else:
            del result[r]

    only_poly1 = poly1.difference(cascaded_union([elt[0] for elt in result]))
    only_poly1 = eliminate_small_areas(only_poly1, 1e-16*poly1.area)
    if not only_poly1.is_empty:
        result.append((only_poly1, None))

    return [r[0] for r in result]
  
with open("cellular_networks.json") as f:
    cells = json.load(f)["cells"]
tower_locs = lookup_towers(cells)
print(tower_locs)
tower_df = pd.DataFrame(tower_locs)
tower_df.drop(["status", "balance"], axis=1, inplace=True)
print(tower_df.columns)
geo_df = gpd.GeoDataFrame(
    tower_df,
    geometry=gpd.points_from_xy(tower_df.lat, tower_df.lon)
)
# Convert the points to polygons representing circles
geo_df["geometry"] = geo_df.apply(get_shapely_circle, axis=1)
#print(geo_df.head())
#style open-street-map
polys = list(geo_df["geometry"])
results = cascaded_intersections(polys[0], polys[1:])
#fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(10,5))
p = results[1]
x,y = p.exterior.xy
print(f"""Search bounded area:
({min(y)}, {min(x)})
to
({max(y)}, {max(x)})"""
)

x_diff = max(x)-min(x)
y_diff = max(y)-min(y)
deg_to_meters = 111139.0 # number of meters in 1 degree
x_meters = round(x_diff * deg_to_meters, 2)
y_meters = round(y_diff * deg_to_meters, 2)
m2 = round(x_meters * y_meters, 2)
print(f"Search bounds size (degrees): {y_diff} degrees latitude by {x_diff} longitude")
print(f"Search bounds size (meters): {x_meters} meters wide by {y_meters} long")
print(f"Search area size (meters): {m2} meters squared")
rep_p = p.representative_point()
c_lon, c_lat = rep_p.xy
fig = go.Figure(go.Scattermapbox(
    fill = "toself",
    lon = list(x), lat = list(y),
    marker = { 'size': 2, 'color': "blue" }))

fig.update_layout(
    mapbox = {
        'style': "open-street-map",
        'center': {'lon': c_lon[0], 'lat': c_lat[0]},
        'zoom': 16},
    showlegend = False)
fig.show()
