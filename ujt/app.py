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

from generated import graph_structures_pb2

from . import generate_data, utils

def generate_service_elements_from_local_data():
    """ Converts the Service protobufs from the ../data directory to a cytoscape graph format.

    In subsequent versions, this should be handled by the reporting server, and protobufs should be returned to the tool.
    
    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service) or edge (Dependency).
    """
    service_names = generate_data.SERVICE_NAMES
    services = [
        utils.read_proto_from_file(name, graph_structures_pb2.Service)
        for name in service_names
    ]

    parent_nodes, child_nodes, edges = [], [], []

    for service in services:
        parent_nodes.append({
            "data": {
                "id": service.name,
                "label": service.name,
            },
            "classes": "service",
        })
        for endpoint in service.endpoints:
            child_nodes.append({
                "data": {
                    "id": endpoint.name,
                    "label": endpoint.name,
                    "parent": service.name,
                }
            })
            for dependency in endpoint.dependencies:
                edges.append({
                    "data": {
                        "source":
                            endpoint.name,
                        "target": (dependency.target_endpoint_name
                                   if dependency.target_endpoint_name else
                                   dependency.target_service_name)
                    }
                })

    return parent_nodes + child_nodes + edges

def generate_client_elements_from_local_data():
    """ Converts the Client protobufs from the ../data directory to a cytoscape graph format.

    In subsequent versions, this should be handled by the reporting server, and protobufs should be returned to the tool.
    
    Returns:
        A list of dictionary objects, each containing information regarding a single node (Client) or edge (Dependency).
    """
    client_names = generate_data.CLIENT_NAMES
    clients = [
        utils.read_proto_from_file(name, graph_structures_pb2.Client)
        for name in client_names
    ]

    nodes, edges = [], []

    for client in clients:
        nodes.append({
            "data": {
                "id": client.name,
                "label": client.name,
            },
            "classes": "client",
        })
        for user_journey in client.user_journeys:
            for dependency in user_journey.dependencies:
                edges.append({
                    "data": {
                        "source":
                            client.name,
                        "target": (dependency.target_endpoint_name
                                   if dependency.target_endpoint_name else
                                   dependency.target_service_name)
                    }
                })

    return nodes + edges

def generate_graph_elements_from_local_data():
    """ Converts the protobufs from the ../data directory to a cytoscape graph format.

    In subsequent versions, this method should use a RPC to fetch protobuf data from a reporting Server.

    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service or Client) or edge (Dependency).
    """
    return generate_service_elements_from_local_data() + generate_client_elements_from_local_data()

cyto.load_extra_layouts()
app = dash.Dash(__name__)

STYLESHEET = [
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

app.layout = html.Div(
    children=[
        html.H1(children="User Journey Tool",
                style={
                    "textAlign": "center",
                    "color": "black",
                }),
        cyto.Cytoscape(
            id="cytoscape-two-nodes",
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
            stylesheet=STYLESHEET,
        )
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
