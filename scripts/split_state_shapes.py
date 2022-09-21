# %%

from os.path import join
import numpy as np
import geopandas as gpd
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

# %%

fnin = join('..', 'data', 'states', 'cb_2016_us_state_500k.shp')

fnout = join('..', 'assets', 'states.npy')

# %%

states = gpd.read_file(fnin)

shapes = []
for idx in states.index:
    s = states.at[idx,'geometry']
    if type(s) is Polygon:
        coords = [s.exterior.coords]
    elif type(s) is MultiPolygon:
        coords = [geom.exterior.coords for geom in s.geoms]
    for coord in coords:
        x = [i[0] for i in coord]
        y = [i[1] for i in coord]
        shape = np.vstack([x, y])
        shape = np.hstack([shape, np.full((2,1), np.nan)])
        shapes.append(shape)

shapes = np.hstack(shapes).astype(np.float32)[:,:-1]
np.save(fnout, shapes)
# %%

