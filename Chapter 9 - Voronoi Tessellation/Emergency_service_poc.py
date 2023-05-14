# coding: utf-8

import json, os, urllib, requests
import pandas as pd
import geopandas as gpd
import geocoder
import plotly.graph_objects as go
from shapely.geometry import GeometryCollection, shape
import numpy as np
from geovoronoi import voronoi_regions_from_coords

def locate(addr):
    """
    Geolocation for string address
        parameters:
            addr: string address to geolocate
    """
    g = geocoder.osm(addr)
    data = g.json
    if data is None:
        return None
    return {
        "address": data["address"],
        "lat": data["lat"],
        "lon": data["lng"],
        "osm_id": data["osm_id"]
    }
def row_to_str(x):
    """
    Convert data frame row to string address
        parameters:
            x: row with address columns
    """
    addr = "%s %s %s %s" % (
        x["street"],
        x["city"],
        x["state"],
        x["zip"],
    )
    return addr

if not os.path.exists("portland_geodata.json"):
    print("Looking up GeoData")
    base = "https://nominatim.openstreetmap.org/search.php"
    f = {"q": "Portland OR", "polygon_geojson":1, "format":"json"}
    q = urllib.parse.urlencode(f)
    resp = requests.get("%s?%s" % (base, q))
    resp_data = json.loads(resp.text)[0]
    with open("portland_geodata.json", "w") as f:
        f.write(json.dumps(resp_data))

else:
    with open("portland_geodata.json") as f:
        resp_data = json.loads(f.read())

city_gj = {
  "type": "FeatureCollection",
  "features": [
      {
          "type": "Feature",
          "geometry": resp_data["geojson"],
          "properties": {
            "name": "City Boundary"
          }
      }
  ]
}

stations_df = pd.read_csv("station_addresses_portland.csv", names=[
    "name", "street", "city", "state", "zip"
])
stations_df["addr"] = stations_df.apply(row_to_str, axis=1)

with open("station_addresses_portland.csv") as f:
    raw = f.read().strip()
rows = raw.split("\n")
stations = []
for r in rows:
    dat = r.split(",")
    stations.append({
        "id":dat[0],
        "street":dat[1],
        "city":dat[2],
        "state":dat[3],
        "zip":dat[4],
        "addr": "%s %s %s %s" % (dat[1],dat[2],dat[3],dat[4])
    })
stations_df = pd.DataFrame(stations)
print("Stations loaded")
locations = stations_df["addr"].apply(locate)
locations = [a for a in list(locations) if a is not None]
loc_df = pd.DataFrame(locations)
loc_df.to_csv("portland_station_geodata.csv")

geo_df = gpd.GeoDataFrame(
    loc_df,
    geometry=gpd.points_from_xy(loc_df.lat, loc_df.lon)
)
print("GeoDataFrame created")
with open("portland_fire_stations.geojson") as f:
    points_gj = json.loads(f.read())

city_shape = GeometryCollection(
    [shape(feature["geometry"]).buffer(0) for feature in city_gj["features"]]
)
#Accesses the single Multipolygon internal element
city_shape = [geom for geom in city_shape][0]
print("City Shape Data loaded")
points = np.array([[p.y, p.x] for p in list(geo_df["geometry"])])

poly_shapes, poly_to_pt_assignments = voronoi_regions_from_coords(points, city_shape)

vor_gdf = gpd.GeoDataFrame(poly_shapes)
vor_gdf.rename(columns={0:"geometry"}, inplace=True)
vor_gdf.set_geometry(col='geometry', inplace=True)
vor_gj = vor_gdf.__geo_interface__
print("Voronoi GDF created")
# Handle ties by collecting a list and displaying all the winners
winning = 0
winner = -1
winner_shape = []
for i in range(len(poly_shapes)):
    ps = poly_shapes[i]
    if ps.area == winning:
        print("Region %d tied for first currently" % i)
        if isinstance(winning, int):
            winner = [winner, i]
        elif isinstance(winning, list):
            winner.append(i)
        winner_shape.apend(ps)
    elif ps.area > winning:
        winner = i
        winning = ps.area
        winner_shape = [ps]
print(winner_shape)
# From here on no longer handles multiple winners
# you would need to extend this to display each polygon
station_i = poly_to_pt_assignments[winner]
station_pt = geo_df.iloc[station_i]
winner_gj = gpd.GeoSeries(winner_shape).__geo_interface__

fig = go.Figure(go.Scattermapbox(
    mode = "markers",
    lon = station_pt["lon"], lat = station_pt["lat"],
    marker = {'size': 10, 'color': "red"}))

fig.update_layout(
    mapbox = {
        "style": "open-street-map",
        "center": { 'lon': list(geo_df["lon"])[0], 'lat': list(geo_df["lat"])[0]},
        "zoom":10,
        "layers": [
            {
            "source": winner_gj,
            "type": "fill",
            "below": "",
            "color": "royalblue", "opacity": 0.3
            }
        ]
    },
    margin = {'l':0, 'r':0, 'b':0, 't':0})
fig.show()