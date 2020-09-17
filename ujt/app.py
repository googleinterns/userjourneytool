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

from typing import Dict, List, Set, Tuple, Union, cast
from collections import defaultdict

import dash
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output
from flask_caching import Cache
from google.protobuf.message import Message

from generated.graph_structures_pb2 import (SLI, Client, Node, SLIType, Status,
                                            UserJourney)

from . import converters, generate_data, utils, logic


def read_local_data() -> Tuple[Dict[str, Node], Dict[str, Client]]:
    """ Reads protobufs in text format from ../data directory into protobuf objects.

    This is simply used as a proof-of-concept/test implementation. 
    In actual usage, this method should not be used. Instead, protobufs should be read from a reporting server.
    THis is highly coupled with implementation of mock data storage conventions.

    Returns:
        A tuple of two dictionaries.
        The first dictionary contains a mapping from Node name to the actual Node protobuf message.
        The first dictionary contains a mapping from Client name to the actual Client protobuf message.
    """

    service_names = generate_data.SERVICE_ENDPOINT_NAME_MAP.keys()
    client_names = generate_data.CLIENT_USER_JOURNEY_NAME_MAP.keys()

    flattened_endpoint_names = []
    for service_name, endpoint_names in generate_data.SERVICE_ENDPOINT_NAME_MAP.items(
    ):
        flattened_endpoint_names += [
            f"{service_name}.{endpoint_name}"
            for endpoint_name in endpoint_names
        ]

    node_names = list(service_names) + flattened_endpoint_names

    node_name_message_map: Dict[str, Node] = {
        name: cast(
            Node,
            utils.read_proto_from_file(
                utils.named_proto_file_name(name, Node),
                Node,
            )) for name in node_names
    }

    client_name_message_map: Dict[str, Client] = {
        name: cast(
            Client,
            utils.read_proto_from_file(
                utils.named_proto_file_name(name, Client), Client))
        for name in client_names
    }

    return node_name_message_map, client_name_message_map


def generate_graph_elements_from_local_data():
    """ Generates a cytoscape elements dictionary from mock protobufs saved in the ../data directory.

    In actual usage, this method should not be used. Instead, protobufs should be read from a reporting server.
    In subsequent versions, this method should be replaced with generate_graph_elements_from_remote_data to
    use a RPC to fetch protobuf data from a reporting server instead of reading local data.

    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service or Client) or edge (Dependency).
    """

    node_name_message_map, client_name_message_map = read_local_data()

    return generate_graph_elements(node_name_message_map,
                                   client_name_message_map)

def generate_graph_elements_from_remote_data():
    """ Generates a cytoscape elements dictionary from mock protobufs saved in the ../data directory.

    In actual usage, this method should be used to read protobufs from a reporting server.
    This mthod should replace generate_graph_elements_from_local_data

    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service or Client) or edge (Dependency).
    """
    raise NotImplementedError

def generate_graph_elements(node_name_message_map: Dict[str, Node],
                            client_name_message_map: Dict[str, Client]):
    """ Generates a cytoscape elements dictionary from Service, SLI, and Client protobufs.

    Args:
        node_name_message_map: A dictionary mapping Node names to their corresponding Node protobuf message.
        client_name_message_map: A dictionary mapping Client names to the corresponding Client protobuf message.

    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service or Client) or edge (Dependency).
    """

    logic.compute_node_statuses(node_name_message_map, client_name_message_map)

    return (converters.cytoscape_elements_from_nodes(node_name_message_map) +
            converters.cytoscape_elements_from_clients(client_name_message_map))


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
        "selector": ".NODETYPE_SERVICE",
        "style": {
            "shape": "rectangle",
            # set non-compound nodes (services with no endpoints) to match same color as compound nodes
            "background-color": "lightgrey",
        }
    },
    {
        "selector": ".STATUS_HEALTHY",
        "style": {
            "background-color": "green"
        }
    },
    {
        "selector": ".STATUS_WARN",
        "style": {
            "background-color": "orange"
        }
    },
    {
        "selector": ".STATUS_ERROR",
        "style": {
            "background-color": "red"
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
"""
@app.callback()
def refresh_slis():
    pass
"""

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
