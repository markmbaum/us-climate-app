# %%

from os.path import join
import numpy as np
import xarray as xr

# %%----------------------------------------------------------------------------
# INPUT

#path to PRISM data
DATADIR = join('..', 'data', 'prism')

#output directory
OUTDIR = join('..', 'assets')

#grid definition (from hdr files)
NROW = 621
NCOL = 1405
STEP = 0.04166666666667
XMIN = -125.016666666667
YMAX = 49.9333333333323

# %%----------------------------------------------------------------------------
#FUNCTIONS

def readbil(path, dtype=np.float32):
    X = np.fromfile(path, dtype=dtype).reshape(NROW,NCOL)
    X = X.astype(np.float32)
    X[np.isclose(X, -9999.0)] = np.nan
    return X

# %%----------------------------------------------------------------------------
#MAIN

#grid edge coordinates
lon = np.linspace(XMIN, XMIN + STEP*NCOL, NCOL+1)
lat = np.linspace(YMAX, YMAX - STEP*NROW, NROW+1)
#grid center coordinates
latc = (lat[:-1] + lat[1:])/2
lonc = (lon[:-1] + lon[1:])/2

#read all of the climate normals into xarray datasets
prism = dict()
for v in ['ppt', 'tmin', 'tmean', 'tmax']:
    d = join(DATADIR, v)
    X = []
    for month in range(1,13):
        fn = f'PRISM_{v}_30yr_normal_4kmM3_{month:02}_bil.bil'
        X.append( readbil(join(d, fn)) )
    prism[v] = np.stack(X)
    
#convert to fahrenheit
for v in ['tmin', 'tmean', 'tmax']:
    prism[v] *= 1.8
    prism[v] += 32
#convert to inches
prism['ppt'] *= 0.0393701
prism['ppt'][prism['ppt'] > 16] = 16

#cast as DataArrays
for k in prism:
    prism[k] = xr.DataArray(prism[k], coords=dict(month=range(1,13), lat=latc, lon=lonc))

#also read elevation into a DataArray
prism['dem'] = xr.DataArray(
    readbil(join(DATADIR, 'dem', 'PRISM_us_dem_4km_bil.bil'), dtype=np.int32),
    coords=dict(
        lat=latc,
        lon=lonc
    )
)
prism['dem'] *= 3.28084

#convert to xarray format
prism = xr.Dataset(prism)

#save to netcdf
prism.to_netcdf(join(OUTDIR, 'prism.nc'))

# %%
