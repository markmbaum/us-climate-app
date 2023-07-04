from os.path import join, dirname
import numpy as np
import zarr
import zipfile
import calendar

from bokeh.plotting import figure, curdoc
from bokeh.layouts import column, row
from bokeh import palettes
from bokeh.models import (
    GeoJSONDataSource,
    ColumnDataSource,
    HoverTool,
    LinearColorMapper,
    Select,
)

DATADIR = join(dirname(__file__), "data")
NROW = 621
NCOL = 1405
STEP = 0.04166666666667
XMIN = -125.016666666667
YMAX = 49.9333333333323
FIELDS = [
    "Precipitation (inches/month)",
    "Low Temperature (°F)",
    "Temperature (°F)",
    "High Temprature (°F)",
    "Sunshine Index",
    "Elevation (m)",
]
MONTHS = ["Annual Average"] + list(calendar.month_name[1:])


def load_prism():
    normals = zarr.open(join(DATADIR, "prism", "normals.zarr"))[:].astype("float32")
    # undo the integer storage
    normals[np.isclose(normals, -9999)] = np.nan
    normals /= 100

    dem = zarr.open(join(DATADIR, "prism", "dem.zarr"))[:]
    latc = zarr.open(join(DATADIR, "prism", "latc.zarr"))[:]
    lonc = zarr.open(join(DATADIR, "prism", "lonc.zarr"))[:]

    return normals, dem, lonc, latc


def load_states():
    archive = zipfile.ZipFile(
        join(DATADIR, "geo", "cb_2018_us_state_500k.geojson.zip"), "r"
    )
    states = archive.read("cb_2018_us_state_500k.geojson").decode("utf-8")
    return states


def load_cities():
    with open(join(DATADIR, "geo", "uscities.geojson"), "r") as ifile:
        cities = ifile.read()
    return cities

def update(field, month):
    fidx = FIELDS.index(field)
    midx = MONTHS.index(month)
    if fidx < 5:
        if midx == 0:
            z = normals[fidx, ...].mean(axis=0)
        else:
            # subtract 1 because first index is annual mean
            z = normals[fidx, midx - 1, ...]
    else:
        z = dem
        cb.color_mapper.low = np.nanmin(dem)
        cb.color_mapper.high = np.nanmax(dem)

    source.data["image"] = [z]

    if fidx == 0:  # precip
        cb.color_mapper.palette = palettes.Blues256[::-1]
        cb.title = f"{month} {field}"
        cb.color_mapper.low = np.nanmin(normals[0, ...])
        cb.color_mapper.high = np.nanmax(normals[0, ...])
    elif fidx == 4:  # sunshine
        cb.color_mapper.palette = palettes.Cividis256
        cb.title = f"{month} {field}"
        cb.color_mapper.low = np.nanmin(normals[4, ...])
        cb.color_mapper.high = np.nanmax(normals[4, ...])
    elif fidx == 5:  # elevation
        cb.color_mapper.palette = palettes.Iridescent23
        cb.title = field
        cb.color_mapper.low = np.nanmin(dem)
        cb.color_mapper.high = np.nanmax(dem)
    else:  # temperature
        cb.color_mapper.palette = palettes.Turbo256
        cb.title = f"{month} {field}"
        cb.color_mapper.low = np.nanmin(normals[1:4, ...])
        cb.color_mapper.high = np.nanmax(normals[1:4, ...])

    return None


def update_field(attr, old, new):
    update(new, month_widget.value)


def update_month(attr, old, new):
    update(field_widget.value, new)


# load data
normals, dem, lonc, latc = load_prism()
states = GeoJSONDataSource(geojson=load_states())
cities = GeoJSONDataSource(geojson=load_cities())

# initalization data
z = normals[2, ...].mean(axis=0)
source = ColumnDataSource({"x": lonc, "y": latc, "image": [z]})

# create figure
p = figure(
    name="map",
    sizing_mode="scale_width",
    aspect_ratio=1.75,
    match_aspect=True,
    tools="pan,wheel_zoom,reset",
    active_drag="pan",
    active_scroll="wheel_zoom",
)
p.xaxis.axis_label = "Longitude (°)"
p.yaxis.axis_label = "Latitude (°)"
p.xgrid.visible = False
p.ygrid.visible = False

# main data
image = p.image(
    image="image",
    x="x",
    y="y",
    dw=NCOL * STEP,
    dh=NROW * STEP,
    anchor="top_left",
    origin="top_left",
    color_mapper=LinearColorMapper(
        palette=palettes.Turbo256,
        low=np.nanmin(normals[1:4, ...]),
        high=np.nanmax(normals[1:4, ...]),
        nan_color="white",
    ),
    source=source,
)
cb = image.construct_color_bar(title=f"{MONTHS[0]} {FIELDS[2]}")
p.add_layout(cb, place="above")

# elevation contours
p.contour(
    x=lonc,
    y=latc,
    z=dem,
    levels=np.linspace(np.nanmin(dem), np.nanmax(dem), 21),
    line_color="black",
    fill_color="none",
    line_alpha=0.25,
)

# state outlines
p.patches(
    "xs",
    "ys",
    source=states,
    fill_color="none",
    line_color="black",
)

# cities
scatter = p.scatter(
    x="x",
    y="y",
    fill_color="gray",
    line_color="black",
    marker="circle",
    size=6,
    source=cities,
)
p.add_tools(
    HoverTool(
        renderers=[scatter],
        tooltips="""
            <div>
                <b>@city</b><br>@state
            </div>
        """,
    )
)

field_widget = Select(title="Field", value=FIELDS[2], options=FIELDS, align="center")
field_widget.on_change("value", update_field)
month_widget = Select(title="Month", value=MONTHS[0], options=MONTHS, align="center")
month_widget.on_change("value", update_month)

layout = column(
    p,
    row(
        field_widget,
        month_widget,
        align="center",
    ),
    sizing_mode="scale_width",
    spacing=30,
)

curdoc().add_root(layout)
curdoc().title = "US Climate"
