# %%

from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go

from os.path import join
import numpy as np
import xarray as xr
import calendar

# %% config

fnstates = join('assets', 'states.npy')

fnprism = join('assets', 'prism.nc')

# %% aux functions

floor = lambda X: 10*np.floor(X.min().values/10)

ceil = lambda X: 10*np.ceil(X.max().values/10)

mask = lambda X, a, b: (X.min(axis=0) < a) | (X.max(axis=0) > b)

# %% load and set data

states = np.load(fnstates)

prism = xr.load_dataset(fnprism)
lat = prism.lat.values
lon = prism.lon.values

ranges = {v: (floor(prism[v]), ceil(prism[v])) for v in prism.data_vars}

colorscales = {
    'tmin': 'turbo',
    'tmean': 'turbo',
    'tmax': 'turbo',
    'ppt': 'YlGnBu',
    'dem': 'Electric_r'
}

dvars = [
    'Low Temperature (°F)',
    'Mean Temperature (°F)',
    'High Temperature (°F)',
    'Precipitation (inches)',
    'Elevation (ft)'
]

dvar2var = dict(zip(dvars, ['tmin', 'tmean', 'tmax', 'ppt', 'dem']))

dpers = ['Annual Mean'] + list(calendar.month_name)[1:]

dper2num = dict(zip(dpers, range(-1,13)))

# %% main

def plot_states(fig, states):
    fig.add_trace(
        go.Scatter(
            x=states[0,:],
            y=states[1,:],
            mode='lines',
            opacity=0.5,
            line=dict(
                color='black',
                width=0.5
            )
        )
    )
    return None

def plot_prism(fig, data, colorscale, label):
    fig.add_trace(
        go.Heatmap(
            x=lon,
            y=lat,
            z=data,
            opacity=0.9,
            colorscale=colorscale,
            colorbar=dict(
                title=dict(
                    text=label,
                    side='top',
                    font=dict(size=14)
                ),
                orientation='h',
                thickness=15,
                xpad=250
            ),
            name='',
            hoverongaps=False
        )
    )
    return None

def update_layout(fig):
    fig.update_layout(
        showlegend=False,
        xaxis_title='Longitude (°)',
        yaxis_title='Latitude (°)',
        plot_bgcolor='white',
        width=1250,
        height=1250/1.8
    )
    fig.update_xaxes(
        range=[lon.min(), lon.max()],
        constrain='domain'
    )
    fig.update_yaxes(
        range=[lat.min(), lat.max()],
        scaleratio=1,
        constrain='domain'
    )
    return None

def generate_data(var, per, rtmin, rtmax, rppt):
    #display data
    X = prism[var]
    #annual mean or specific month
    if var != 'dem':
        if per == -1:
            X = X.mean(axis=0)
        else:
            X = X[per,...]
    #create the mask from temp and ppt ranges
    M = mask(prism.tmin, *rtmin) | mask(prism.tmax, *rtmax) | mask(prism.ppt, *rppt)
    #copy display array and set masked values to nan
    X = X.values.copy()
    X[M] = np.nan
    #cap precipitation if needed, which is often skewed by western mountain areas
    if var == 'ppt':
        X[X > 10] = 10
    
    return X

def generate_figure(data, colorscale, label):
    fig = go.Figure()
    plot_states(fig, states)
    plot_prism(fig, data, colorscale, label)
    update_layout(fig)
    return fig

fig = generate_figure(
    generate_data(
        'tmean',
        -1,
        ranges['tmin'],
        ranges['tmax'],
        ranges['ppt']),
    colorscales['tmean'],
    'Annual Mean Temperature (°F)'
)

# %%

app = Dash(__name__)
application = app.server
app.title = "US Climate"

app.layout = html.Div(
    style=dict(
        textAlign='center',
        fontFamily='Open Sans, sans-serif',
        margin='auto',
        width=1250
    ),
    children=[
        html.H1(
            children="Where is the weather...?"
        ),
        html.H3(
            children="An interactive map parsing weather data throughout the continental US"
        ),
        dcc.Graph(
            figure=fig,            
            id='figure'
        ),
        html.H4(
            children="Low Temperature (°F)"
        ),
        html.P(
            children="restricts display to areas where monthly average low temperature is never outside this range",
            style=dict(fontSize=13)
        ),
        dcc.RangeSlider(
            ranges['tmin'][0],
            ranges['tmin'][1],
            value=ranges['tmin'],
            step=5,
            id='tmin-slider'
        ),
        html.H4(
            children="High Temperature (°F)"
        ),
        html.P(
            children="restricts display to areas where monthly average high temperature is never outside this range",
            style=dict(fontSize=13)
        ),
        dcc.RangeSlider(
            ranges['tmax'][0],
            ranges['tmax'][1],
            value=ranges['tmax'],
            step=5,
            id='tmax-slider'
        ),
        html.H4(
            children="Monthly Precipitation (inches)"
        ),
        html.P(
            children="restricts display to areas where monthly precipitation is never outside this range",
            style=dict(fontSize=13)
        ),
        dcc.RangeSlider(
            ranges['ppt'][0],
            ranges['ppt'][1],
            value=ranges['ppt'],
            step=1,
            id='ppt-slider'
        ),
        html.H4(
            children="Display Data"
        ),
        dcc.RadioItems(
            dvars,
            dvars[1],
            labelStyle=dict(
                padding='5px'
            ),
            id='var-buttons'
        ),
        html.H4(
            children="Display Period"
        ),
        dcc.RadioItems(
            dpers,
            dpers[0],
            labelStyle=dict(
                padding='6px'
            ),
            id='per-buttons'
        ),
        html.Div(
            style=dict(
                color='gray',
                width=700,
                margin='0.9cm auto 0 auto',
                borderTop='1px solid black'
            ),
            children=[
                html.H5(
                    "Notes",
                    style=dict(
                        fontSize=14,
                        marginBottom=0
                    )
                ),
                dcc.Markdown(
                    """
                        * Climate data represent estimates of spatially continuous 30 year averages from the [PRISM Climate Group](https://prism.oregonstate.edu/normals/).

                        * State boundaries are drawn using [shapefiles](https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html) from the US Census Bureau.

                        * Monthly precipitation values are truncated at 16 inches. Values up to about 40 inches occur over some of the western mountains, but are rare and badly skew the colorscale for areas in a more normal range.

                        * This little app was created using [Plotly/Dash](https://dash.plotly.com/) and code is available [on GitHub](https://github.com/markmbaum/us-climate-app).
                    """,
                    style=dict(
                        fontSize=12,
                        textAlign='left'
                    )
                )
            ]
        )
    ]
)

@app.callback(
    Output(component_id='figure', component_property='figure'),
    Input(component_id='tmin-slider', component_property='value'),
    Input(component_id='tmax-slider', component_property='value'),
    Input(component_id='ppt-slider', component_property='value'),
    Input(component_id='var-buttons', component_property='value'),
    Input(component_id='per-buttons', component_property='value')
)
def update_figure(rtmin, rtmax, rppt, dvar, dper):
    var = dvar2var[dvar]
    per = dper2num[dper]
    if var == 'dem':
        label = dvar
    else:
        label = (dper + ' ' + dvar).replace('Mean Mean', 'Mean')
    fig = generate_figure(
        generate_data(var, per, rtmin, rtmax, rppt),
        colorscales[var],
        label
    )
    return fig

# %%

if __name__ == '__main__':
    app.run(port=8080)

# %%
