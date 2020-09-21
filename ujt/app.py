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

from collections import defaultdict
from typing import Dict, List, Set, Tuple, Union, cast

import dash
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from flask_caching import Cache
from google.protobuf.message import Message
from graph_structures_pb2 import (
    SLI,
    Client,
    Node,
    NodeType,
    SLIType,
    Status,
    UserJourney)

from . import compute_status, converters, generate_data, utils

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


@cache.memoize()
def read_local_data() -> Tuple[Dict[str, Node], Dict[str, Client]]:
    """ Reads protobufs in text format from ../data directory into protobuf objects.

    This is simply used as a proof-of-concept/test implementation. 
    In actual usage, this method should not be used. Instead, protobufs should be read from a reporting server.
    This is highly coupled with implementation of mock data storage conventions.

    Returns:
        A tuple of two dictionaries.
        The first dictionary contains a mapping from Node name to the actual Node protobuf message.
        The second dictionary contains a mapping from Client name to the actual Client protobuf message.
    """

    cache.clear()

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

    node_name_message_map: Dict[str,
                                Node] = {
                                    name: cast(
                                        Node,
                                        utils.read_proto_from_file(
                                            utils.named_proto_file_name(
                                                name,
                                                Node),
                                            Node,
                                        ))
                                    for name in node_names
                                }

    client_name_message_map: Dict[str,
                                  Client] = {
                                      name: cast(
                                          Client,
                                          utils.read_proto_from_file(
                                              utils.named_proto_file_name(
                                                  name,
                                                  Client),
                                              Client))
                                      for name in client_names
                                  }

    return node_name_message_map, client_name_message_map


@cache.memoize()
def get_node_name_message_map() -> Dict[str, Node]:
    """ Gets a dictionary mapping Node names to Node messages.

    Currently reads local data, but should be eventually modified to use remote data.
    Computes the status of Nodes and their SLIs before returning dictionary.

    Returns:
        A dictionary mapping Node names to Node messages
    """

    node_name_message_map, client_name_message_map = read_local_data()

    compute_status.compute_statuses(
        node_name_message_map,
        client_name_message_map,
    )

    return node_name_message_map


@cache.memoize()
def get_client_name_message_map() -> Dict[str, Client]:
    """ Gets a dictionary mapping Client names to Client messages.

    Currently reads local data, but should be eventually modified to use remote data.

    Returns:
        A dictionary mapping Client names to Client messages
    """
    return read_local_data()[1]


def generate_graph_elements(
        node_name_message_map: Dict[str,
                                    Node],
        client_name_message_map: Dict[str,
                                      Client]):
    """ Generates a cytoscape elements dictionary from Service, SLI, and Client protobufs.

    Args:
        node_name_message_map: A dictionary mapping Node names to their corresponding Node protobuf message.
        client_name_message_map: A dictionary mapping Client names to the corresponding Client protobuf message.

    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service or Client) or edge (Dependency).
    """

    return (
        converters.cytoscape_elements_from_nodes(node_name_message_map) +
        converters.cytoscape_elements_from_clients(client_name_message_map))


@app.callback(
    Output("cytoscape-graph",
           "elements"),
    [Input("refresh-button",
           "n_clicks_timestamp")],
)
def refresh_graph(n_clicks_timestamp):
    cache.clear()
    return generate_graph_elements(
        get_node_name_message_map(),
        get_client_name_message_map(),
    )


@app.callback(
    Output('node-info-panel',
           'children'),
    [Input('cytoscape-graph',
           'tapNode')],
)
def generate_node_info_panel(tapNode):
    if tapNode is None or utils.is_client_cytoscape_node(tapNode):
        raise PreventUpdate

    node_name = tapNode["data"]["id"]
    node_name_message_map = get_node_name_message_map()
    node = node_name_message_map[node_name]

    out = [
        html.H2(
            f"{utils.relative_name(node_name)} ({utils.human_readable_enum_name(node.node_type, NodeType)})"
        ),
    ]

    if node.slis:
        out += [
            html.H3("SLI Info"),
            converters.datatable_from_slis(node.slis,
                                           id="datatable-slis")
        ]

    if node.child_names:
        child_nodes = [
            node_name_message_map[child_name] for child_name in node.child_names
        ]
        out += [
            html.H3("Child Node Info"),
            converters.datatable_from_nodes(
                child_nodes,
                use_relative_names=True,
                id="datatable-child-node")
        ]

    if node.dependencies:
        dependency_nodes = [
            node_name_message_map[dependency.target_name]
            for dependency in node.dependencies
        ]
        out += [
            html.H3("Dependency Node Info"),
            converters.datatable_from_nodes(
                dependency_nodes,
                use_relative_names=False,
                id="datatable-dependency-nodes")
        ]

    return out


@app.callback(
    Output('client-info-panel',
           'children'),
    [Input('cytoscape-graph',
           'tapNode')],
)
def generate_client_info_panel(tapNode):
    if tapNode is None or not utils.is_client_cytoscape_node(tapNode):
        raise PreventUpdate

    return "client_info"


CYTO_STYLESHEET = [
    {
        "selector": "node",
        "style": {
            "content": "data(label)",
            #"color": "red",
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
        "selector": f".{NodeType.Name(NodeType.NODETYPE_SERVICE)}",
        "style":
            {
                "shape": "rectangle",
                # set non-compound nodes (services with no endpoints) to match same color as compound nodes
                "background-color": "lightgrey",
                "background-blacken": -.5
            }
    },
    {
        "selector": f".{Status.Name(Status.STATUS_HEALTHY)}",
        "style": {
            "background-color": "green"
        }
    },
    {
        "selector": f".{Status.Name(Status.STATUS_WARN)}",
        "style": {
            "background-color": "orange"
        }
    },
    {
        "selector": f".{Status.Name(Status.STATUS_ERROR)}",
        "style": {
            "background-color": "red"
        }
    },
    {
        "selector": ":selected:",
        "style":
            {
                "border-width": 1,
                "border-color": "black",
                #"background-blacken": .5,
            }
    }
]

app.layout = html.Div(
    children=[
        html.H1(
            children="User Journey Tool",
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
            #elements=generate_graph_elements_from_local_data(),
            stylesheet=CYTO_STYLESHEET,
        ),
        dbc.Button(id="refresh-button",
                   children="Refresh"),
        html.Div(id="refresh-signal",
                 style={"display": "none"}),
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
                                    html.Div(
                                        id="client-info-panel",
                                        className="info-panel"),
                                ]),
                        ])),
            ],
            className="mb-5"),
    ])

if __name__ == "__main__":
    app.run_server(debug=True)
