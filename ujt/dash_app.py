""" Configuration for Dash app.

Exposes app and cache to enable other files (namely callbacks) to register callbacks and update cache
"""

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
from flask_caching import Cache

from . import constants

# Initialize Dash app and Flask-Cache
cyto.load_extra_layouts()
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
cache = Cache()
cache.init_app(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache_dir"
    },
)

app.layout = html.Div(
    children=[
        html.H1(
            children="User Journey Tool",
            style={
                "textAlign": "center",
            }),
        cyto.Cytoscape(
            id="cytoscape-graph",
            layout={
                "name": "dagre",
                "nodeDimensionsIncludeLabels": "true",
            },
            style={
                "width": constants.GRAPH_WIDTH,
                "height": constants.GRAPH_HEIGHT,
                "backgroundColor": constants.GRAPH_BACKGROUND_COLOR,
            },
            stylesheet=constants.CYTO_STYLESHEET,
        ),
        dbc.Button(id="refresh-button",
                   children="Refresh"),
        html.Div(
            children=[
                dbc.Container(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H1("Node Info"),
                                    html.Div(
                                        id="node-info-panel",
                                        className="info-panel"),
                                ]),
                            dbc.Col(
                                [
                                    html.H1("Client Info"),
                                    dcc.Dropdown(
                                        id="client-dropdown",
                                        clearable=False,
                                        searchable=False,
                                    ),
                                    html.Div(
                                        id="client-info-panel",
                                        className="info-panel"),
                                ]),
                        ])),
            ],
            className="mb-5"),
    ],
)
