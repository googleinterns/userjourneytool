# Copyright 2020 Chuan Chen

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Main module for Dash app. """

import dash
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output
from flask_caching import Cache

from generated import graph_structures_pb2

from . import converters, generate_data, utils


def generate_graph_elements_from_local_data():
    """ Converts the protobufs from the ../data directory to a cytoscape graph format.

    In subsequent versions, this method should use a RPC to fetch protobuf data from a reporting Server.

    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service or Client) or edge (Dependency).
    """
    service_names = generate_data.SERVICE_ENDPOINT_NAME_MAP.keys()
    client_names = generate_data.CLIENT_USER_JOURNEY_NAME_MAP.keys()
    services = [
        utils.read_proto_from_file(
            utils.named_proto_file_name(name, graph_structures_pb2.Service),
            graph_structures_pb2.Service,
        ) for name in service_names
    ]
    clients = [
        utils.read_proto_from_file(
            utils.named_proto_file_name(name, graph_structures_pb2.Client),
            graph_structures_pb2.Client,
        ) for name in client_names
    ]

    return (converters.cytoscape_elements_from_clients(clients) +
            converters.cytoscape_elements_from_services(services))


cyto.load_extra_layouts()
app = dash.Dash(__name__)
cache = Cache()
cache.init_app(app.server,
               config={
                   "CACHE_TYPE": "filesystem",
                   "CACHE_DIR": "cache_dir"
               })

CYTO_STYLESHEET = [
    {
        "selector": "node",
        "style": {
            "content": "data(label)",
            "color": "red",
        }
    },
    {
        "selector": "edge",
        "style": {
            "curve-style": "straight",
            "target-arrow-shape": "triangle",
        }
    },
    {
        "selector": ".service",
        "style": {
            "shape": "rectangle",
            # set non-compound nodes (services with no endpoints) to match same color as compound nodes
            "background-color": "lightgrey",
        }
    }
]

app.layout = html.Div(children=[
    html.H1(children="User Journey Tool",
            style={
                "textAlign": "center",
                "color": "black",
            }),
    cyto.Cytoscape(
        id="cytoscape-graph",
        #layout={"name": "breadthfirst", "roots": "#MobileClient, #WebBrowser"},
        layout={
            "name": "dagre",
            "nodeDimensionsIncludeLabels": "true",
        },
        style={
            "width": "100%",
            "height": "600px",
            "backgroundColor": "azure"
        },
        elements=generate_graph_elements_from_local_data(),
        stylesheet=CYTO_STYLESHEET,
    ),
    html.Button(id="refresh-button", children="Refresh"),
    html.Div(id="refresh-signal", style={"display": "none"})
])


@app.callback()
def refresh_slis():
    pass


# on interval:
#   update the slis
#   compute status
#   redraw graph
"""
@app.callback(interval)
def updateData():
    slis = get_slis_from_server()
    
    compute the statuses but don't modify 
    
    return generate_elements_from_graph_and_slis(...)

"""
if __name__ == "__main__":
    app.run_server(debug=True)
