# %%

from os.path import join
import numpy as np
import xarray as xr
from scipy.interpolate import interpn

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

#interpolation/regridding sizes
nlon = 700
nlat = 350

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

#interpolation/regridding coordinates
lonc_interp = np.linspace(lonc.min(), lonc.max(), nlon)
latc_interp = np.linspace(latc.min(), latc.max(), nlat)
Lonc_interp, Latc_interp = np.meshgrid(lonc_interp, latc_interp)
xi = np.stack([Lonc_interp.flatten(), Latc_interp.flatten()]).T

#read all of the climate normals into arrays
prism = dict()
for v in ['ppt', 'tmin', 'tmean', 'tmax']:
    #read the slice
    d = join(DATADIR, v)
    grids = []
    for month in range(1,13):
        fn = f'PRISM_{v}_30yr_normal_4kmM3_{month:02}_bil.bil'
        Y = readbil(join(d, fn))
        #interpolate/regrid
        Y = interpn(
            (lonc, latc),
            Y.T,
            xi
        ).reshape(nlat, nlon)
        print(f'{v} {month} regridded')
        grids.append(Y)
    #stack
    prism[v] = np.stack(grids)
    print(f'{v} final shape: {prism[v].shape}')

# %%
    
#convert to fahrenheit
for v in ['tmin', 'tmean', 'tmax']:
    prism[v] *= 1.8
    prism[v] += 32
#convert to inches
prism['ppt'] *= 0.0393701
prism['ppt'][prism['ppt'] > 16] = 16

#cast as DataArrays
for k in prism:
    prism[k] = xr.DataArray(
        prism[k],
        coords=dict(
            month=range(1,13),
            lat=latc_interp,
            lon=lonc_interp)
        )

#also read elevation, which is stored in integer format, into a DataArray
prism['dem'] = readbil(join(DATADIR, 'dem', 'PRISM_us_dem_4km_bil.bil'), dtype=np.int32)
prism['dem'] = interpn(
    (lonc, latc),
    prism['dem'].T,
    xi
).reshape(nlat, nlon)
prism['dem'] = xr.DataArray(
    prism['dem'],
    coords=dict(
        lat=latc_interp,
        lon=lonc_interp
    )
)
prism['dem'] *= 3.28084
print(f"dem shape: {prism['dem'].shape}")

#convert to xarray format
prism = xr.Dataset(prism)

#save to netcdf
prism.to_netcdf(join(OUTDIR, 'prism.nc'))

# %%
