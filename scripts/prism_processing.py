# %%

from os.path import join, isfile
import numpy as np
import zarr

# %%----------------------------------------------------------------------------
# INPUT

# path to PRISM data
datadir = join("..", "data", "raw", "prism")

# output directory
outdir = join("..", "data", "pro", "prism")

# grid definition (from hdr files)
NROW = 621
NCOL = 1405
STEP = 0.04166666666667
XMIN = -125.016666666667
YMAX = 49.9333333333323

# %%----------------------------------------------------------------------------
# FUNCTIONS


def readbil(path, dtype=np.float32):
    X = np.fromfile(path, dtype=dtype).reshape(NROW, NCOL)
    X = X.astype(np.float32)
    X[np.isclose(X, -9999.0)] = np.nan
    return X


# %%----------------------------------------------------------------------------
# MAIN

# grid edge coordinates
lon = np.linspace(XMIN, XMIN + STEP * NCOL, NCOL + 1)
lat = np.linspace(YMAX, YMAX - STEP * NROW, NROW + 1)
# grid center coordinates
latc = (lat[:-1] + lat[1:]) / 2
lonc = (lon[:-1] + lon[1:]) / 2

# %%

# read all of the climate normals into arrays
prism = []
for v in ["ppt", "tmin", "tmean", "tmax", "soltrans"]:
    # read the slice
    d = join(datadir, v)
    grids = []
    for month in range(1, 13):
        path = join(d, f"PRISM_{v}_30yr_normal_4kmM4_{month:02}_bil.bil")
        if not isfile(path):
            path = path.replace("M4", "M3")
        Y = readbil(path)
        grids.append(Y)
    # stack
    prism.append(np.stack(grids))
    print(f"{v} final shape: {prism[-1].shape}")

dem = readbil(join(datadir, "dem", "PRISM_us_dem_4km_bil.bil"), dtype=np.int32)

# %%

# convert precip to inches
prism[0] *= 0.0393701
prism[0][prism[0] > 18] = 18
# convert temperature to fahrenheit
for i in range(1, 4):
    prism[i] *= 1.8
    prism[i] += 32
# convert elevation to feet
dem *= 3.28
# convert cloudiness to %
prism[-1] *= 100

# %% shifted, rounded numbers for smaller storage type

normals = np.stack(prism) * 100
normals[np.isnan(normals)] = -9999
normals = normals.round().astype(np.int16)

# %%

zarr.save(join(outdir, "normals.zarr"), normals)

zarr.save(join(outdir, "dem.zarr"), dem)

zarr.save(join(outdir, "lonc.zarr"), lonc.astype(np.float32))

zarr.save(join(outdir, "latc.zarr"), latc.astype(np.float32))

# %%
