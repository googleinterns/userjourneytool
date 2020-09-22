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
""" Callbacks for Dash app. """

from collections import deque
from typing import Dict, Tuple, cast

import dash
import dash_html_components as html
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate
from graph_structures_pb2 import Client, Node, NodeType

from . import (
    compute_status,
    constants,
    converters,
    generate_data,
    state,
    utils)
from .dash_app import app


@app.callback(
    Output("cytoscape-graph",
           "elements"),
    [
        Input("refresh-button",
              "n_clicks_timestamp"),
        Input({"datatable-id": ALL},
              "selected_row_ids")
    ],
    [State("cytoscape-graph",
           "elements")],
)
def update_graph_elements(n_clicks_timestamp, selected_row_ids, elements):
    """ Update the elements of the cytoscape graph.

    This function is called on startup, when the refresh button is clicked, and when a row is selected in the User Journey Datatable.
    We need this callback to handle these (generally unrelated) situations because Dash only supports assigning
    a single callback to a given output element.

    Returns:
        A dictionary of cytoscape elements describing the nodes and edges of the graph.
    """

    # regenerate elements on initial call and callbacks invoked by refresh button
    regenerate_elements = True

    ctx = dash.callback_context

    if ctx.triggered:
        # ctx.triggered[0] is either "cytoscape-graph.tapNode" or "client-dropdown.value"
        triggered_id, triggered_prop = ctx.triggered[0]["prop_id"].split(".")
        if triggered_id == "refresh-button":
            state.clear_cache()
        else:
            # don't regenerate elements when triggered by a client datatable row selection
            regenerate_elements = False

    if regenerate_elements:
        node_name_message_map, client_name_message_map = state.get_message_maps()

        cytoscape_graph_elements = converters.cytoscape_elements_from_maps(
            node_name_message_map,
            client_name_message_map,
        )
    else:
        edges_map = {}
        nodes_list = []
        for element in elements:
            element_data = element["data"]
            if "source" in element_data.keys():
                edges_map[(element_data["source"],
                           element_data["target"])] = element
            else:
                nodes_list.append(element)

        updated_edges_map = remove_highlighted_class_from_edges(edges_map)
        if selected_row_ids != [None]:
            updated_edges_map = apply_highlighted_class_to_edges(
                updated_edges_map,
                selected_row_ids[0][0])

        cytoscape_graph_elements = list(updated_edges_map.values()) + nodes_list

    return cytoscape_graph_elements


# refactor the following two methods, but where to put them?
def remove_highlighted_class_from_edges(edges_map):
    for edge in edges_map.values():
        edge["classes"] = ""
    return edges_map


def apply_highlighted_class_to_edges(edges_map, user_journey_name):
    node_name_message_map, client_name_message_map = state.get_message_maps()
    client_name = user_journey_name.split(".")[0]
    client = client_name_message_map[client_name]
    user_journey = next(
        user_journey for user_journey in client.user_journeys
        if user_journey.name == user_journey_name)

    node_frontier = deque()

    # add the initial set of nodes to the frontier
    for dependency in user_journey.dependencies:
        node_frontier.append(node_name_message_map[dependency.target_name])
        edges_map[(client_name,
                   dependency.target_name
                  )]["classes"] = constants.HIGHLIGHTED_UJ_EDGE_CLASS

    while node_frontier:
        node = node_frontier.pop()
        for dependency in node.dependencies:
            node_frontier.append(node_name_message_map[dependency.target_name])
            edges_map[(node.name,
                       dependency.target_name
                      )]["classes"] = constants.HIGHLIGHTED_UJ_EDGE_CLASS

    return edges_map


@app.callback(
    Output("node-info-panel",
           "children"),
    [Input("cytoscape-graph",
           "tapNode")],
)
def generate_node_info_panel(tap_node):
    if tap_node is None or utils.is_client_cytoscape_node(tap_node):
        raise PreventUpdate

    node_name = tap_node["data"]["id"]
    node_name_message_map = state.get_node_name_message_map()
    node = node_name_message_map[node_name]

    out = [
        html.H2(
            f"{utils.relative_name(node_name)} ({utils.human_readable_enum_name(node.node_type, NodeType)})"
        ),
    ]

    if node.slis:
        out += [
            html.H3("SLI Info"),
            converters.datatable_from_slis(
                node.slis,
                table_id=constants.SLI_DATATABLE_ID)
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
                table_id=constants.CHILD_DATATABLE_ID)
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
                table_id=constants.DEPENDENCY_DATATABLE_ID)
        ]

    return out


@app.callback(
    Output("client-info-panel",
           "children"),
    [Input("cytoscape-graph",
           "tapNode"),
     Input("client-dropdown",
           "value")],
)
def generate_client_info_panel(tap_node, dropdown_value):
    ctx = dash.callback_context

    if not ctx.triggered:  # initial callback - no graph clicks or dropdown selection yet
        raise PreventUpdate

    # ctx.triggered[0] is either "cytoscape-graph.tapNode" or "client-dropdown.value"
    triggered_id, triggered_prop = ctx.triggered[0]["prop_id"].split(".")
    if triggered_id == "cytoscape-graph":
        tap_node = ctx.triggered[0]["value"]
        if not utils.is_client_cytoscape_node(tap_node):
            raise PreventUpdate

        client_name = tap_node["data"]["id"]
    else:
        client_name = ctx.triggered[0]["value"]

    client_name_message_map = state.get_client_name_message_map()
    client = client_name_message_map[client_name]
    return converters.datatable_from_client(client, "datatable-client")


@app.callback(
    Output("client-dropdown",
           "value"),
    [Input("cytoscape-graph",
           "tapNode")],
)
def update_client_dropdown_value(tap_node):
    if tap_node is None or not utils.is_client_cytoscape_node(tap_node):
        raise PreventUpdate
    return tap_node["data"]["id"]


'''
@app.callback(
    Output("cytoscape-graph", "elements"),
    [Input("client_dropdown", "value")],
    [State("cytoscape_graph", "elements")],
)
def highlight_user_joruney_path(value, elements):
    return elements
'''
