""" Configuration for Dash app.

Exposes app and cache to enable other files (namely callbacks) to register callbacks and update cache.
App is actually started by ujt.py
"""

import grpc
import server_pb2_grpc

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
# To persist virtual nodes across server sessions,
# we need to save virtual nodes as protos to disk and read them here.
# this is a temporary solution.
cache.set("virtual_node_map", {})
cache.set("parent_virtual_node_map", {})

# Although the RPC server setup isn't part of the Dash app setup,
# it feels right to place it in this file. We should rename this
# file to something more appropriate. 
# This file feels likt it should hold "global"ish instance variables.
# (should we use singleton pattern here? or unnecessary)
channel = grpc.insecure_channel("localhost:50051")  # hardcode this for now...
reporting_server_stub = server_pb2_grpc.ReportingServiceStub(channel)
