# %%

import pandas as pd
import geopandas as gpd
from shapely import Point

# %%

conus = [
    "Alabama",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
]
# %%

df = pd.read_csv("../data/raw/geo/uscities.csv")
df = pd.concat(
    [df.sort_values("population", ascending=False).iloc[:150, :]]
    + [
        df[df.state_name == state]
        .sort_values("population", ascending=False)
        .iloc[:3, :]
        for state in conus
    ]
).drop_duplicates()
df = df[["city", "state_name", "lat", "lng"]]
df.columns = ["city", "state", "lat", "lon"]
df = df[df.state.isin(conus)]

# %%

gpd.GeoDataFrame(
    dict(
        city=df.city,
        state=df.state,
        geometry=[Point(lon,lat) for (lon,lat) in zip(df.lon,df.lat)]
    ),
    crs="EPSG:4269"
).to_file("../data/pro/geo/uscities.geojson", driver='GeoJSON')

# %%
