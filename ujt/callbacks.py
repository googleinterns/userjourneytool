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
    transformers,
    utils)
from .dash_app import app


@app.callback(
    Output("cytoscape-graph",
           "elements"),
    [
        Input("refresh-button",
              "n_clicks_timestamp"),
        Input({"datatable-id": ALL},
              "selected_row_ids"),
        Input("collapse-validation-signal", "children"),
    ],
    [State("cytoscape-graph",
           "elements"),
    State("cytoscape-graph", "selectedNodeData"),
    State("virtual-node-input", "value"),
    ],
)
def update_graph_elements(
    n_clicks_timestamp, 
    selected_row_ids, 
    collapse_validation_signal,
    elements, 
    selected_node_data,
    virtual_node_input_value,
):
    """ Update the elements of the cytoscape graph.

    This function is called on startup, when the refresh button is clicked, and when a row is selected in the User Journey Datatable.
    We need this callback to handle these (generally unrelated) situations because Dash only supports assigning
    a single callback to a given output element.

    Returns:
        A dictionary of cytoscape elements describing the nodes and edges of the graph.
    """
    ctx = dash.callback_context

    if ctx.triggered:
        # ctx.triggered[0] is either "cytoscape-graph.tapNode" or "client-dropdown.value"
        triggered_id, triggered_prop = ctx.triggered[0]["prop_id"].split(".")
        triggered_value = ctx.triggered[0]["value"]
    else:
        triggered_id, triggered_prop, triggered_value = None, None, None

    if triggered_id is None or triggered_id == "refresh-button":
        # in future versions, the refresh button / other triggers to this callback
        if triggered_id == "refresh-button":
            state.clear_cache()

        node_name_message_map, client_name_message_map = state.get_message_maps()

        return converters.cytoscape_elements_from_maps(
            node_name_message_map,
            client_name_message_map,
        )

    # checking triggered_prop is easier than triggered_ids, since the triggered_id
    # is a stringified dictionary when used with a pattern matching callback
    if triggered_prop == "selected_row_ids":
        if selected_row_ids == [None]:
            user_journey_name = None
        else:
            user_journey_name = selected_row_ids[0][0]

        return transformers.apply_highlighted_edge_class_to_elements(
            elements,
            user_journey_name)

    if triggered_id == "collapse-validation-signal" and triggered_value == constants.OK_SIGNAL:
        return transformers.collapse_nodes(virtual_node_input_value, selected_node_data, elements)

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


@app.callback(
    Output("collapse-validation-signal", "children"),
    Input("collapse-button", "n_clicks_timestamp"),
    State("cytoscape-graph", "selectedNodeData"),
    prevent_initial_call=True,
)
def validate_selected_nodes(n_clicks_timestamp, selected_node_data):
    """ Validate the selected nodes before collapsing them.

    Nodes with parents cannot be collapsed. 
    Client nodes cannot be collapsed.
    At least two nodes must be selected to be collapsed at once.

    Returns:
        A string to be placed in the children property of the collapse-validation-signal hidden div. 
        This hidden div is used to ensure the callbacks to update the error modal visibility and cytoscape graph
        are called in the correct order. 
    """
    if selected_node_data is None or len(selected_node_data) < 2:
        return "Error: Must select at least two nodes to collapse."
    node_name_message_map, client_name_message_map = state.get_message_maps()
    for node_data in selected_node_data:
        if node_data["id"] in client_name_message_map:
            return "Error: Cannot collapse clients."
        node = node_name_message_map[node_data["id"]]
        if node.parent_name != "":
            return "Error: Cannot collapse node with parent."
    return constants.OK_SIGNAL


@app.callback(
    [
        Output("collapse-error-modal", "is_open"),
        Output("collapse-error-modal-body", "children"),
    ],
    [
        Input("collapse-error-modal-close", "n_clicks_timestamp"),
        Input("collapse-validation-signal", "children"),
    ],
    prevent_initial_call=True,
)
def toggle_collapse_error_modal(n_clicks_timestamp, signal_message):
    ctx = dash.callback_context

    triggered_id, triggered_prop = ctx.triggered[0]["prop_id"].split(".")
    triggered_value = ctx.triggered[0]["value"]

    if triggered_id == "collapse-error-modal-close":
        print("trying to close")
        return False, ""
    
    if triggered_value != "OK":
        return True, triggered_value

    return False, ""
