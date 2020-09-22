""" Configuration for Dash app.

Exposes app and cache to enable other files (namely callbacks) to register callbacks and update cache.
App is actually started by ujt.py
"""

import dash
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
from flask_caching import Cache

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
# to persist virtual nodes across server sessions, 
# we need to save virtual nodes as protos to disk and read them here.
# this is a temporary solution.
cache.set("virtual_node_map", {})