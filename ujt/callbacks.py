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

from typing import Any, Dict, List, Tuple, Union

import dash
import dash_html_components as html
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate
from graph_structures_pb2 import Node, NodeType, VirtualNode

from . import compute_status, constants, converters, state, transformers, utils
from .dash_app import app


@app.callback(
    Output("cytoscape-graph",
           "elements"),
    [
        Input("refresh-sli-button",
              "n_clicks_timestamp"),
        Input({"datatable-id": ALL},
              "selected_row_ids"),
        Input("virtual-node-update-signal",
              "children"),
        Input("collapse-virtual-node-button",
              "n_clicks_timestamp"),
        Input("expand-virtual-node-button",
              "n_clicks_timestamp"),
    ],
    [
        State("cytoscape-graph",
              "elements"),
        State("cytoscape-graph",
              "selectedNodeData"),
        State("virtual-node-input",
              "value"),
    ],
)
def update_graph_elements(
    # Input
    refresh_n_clicks_timestamp: int,
    user_journey_table_selected_row_ids: List[str],
    virtual_node_update_signal: str,
    collapse_n_clicks_timestamp: int,
    expand_n_clicks_timestamp: int,
    # State
    state_elements: List[Dict[str,
                              Any]],
    selected_node_data: List[Dict[str,
                                  Any]],
    virtual_node_input_value: str,
):
    """ Update the elements of the cytoscape graph.

    This function is called:
        on startup to generate the graph
        when the refresh button is clicked to regenerate the graph
        when row is selected in the User Journey Datatable to highlight the User Journey edges through the path
        when a virtual node is added or deleted (via the virtual-node-update-signal)
        when the collapse button is clicked virtual node
        when the expand button is clicked to expand virtual nodes

    We need this callback to handle these (generally unrelated) situations because Dash only supports assigning
    a single callback to a given output element.

    Args:
        refresh_n_clicks_timestamp: Timestamp of when the refresh button was clicked. Value unused, input only provided to register callback.
        user_journey_table_selected_row_ids: List of selected row ids from the user journey datatable. Should contain only one element. Used for highlighting a path through the graph.  
        virtual_node_update_signal: String used as a signal to indicate that the virtual node addition/deletion was valid. 
        collapse_n_clicks_timestamp: Timestamp of when the collapse button was clicked. Value unused, input only provided to register callback.
        expand_n_clicks_timestamp: Timestamp of when the expand button was clicked. Value unused, input only provided to register callback.
        state_elements: The list of current cytoscape graph elements. This is unused and can be removed in a later change. 
        selected_node_data: The list of data dictionaries for selected nodes. Used to create virtual nodes.
        virtual_node_input_value: The value of the virtual node input box. Used to perform all virtual node operations. 
    Returns:
        A dictionary of cytoscape elements describing the nodes and edges of the graph.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)
    print(triggered_id, triggered_prop, triggered_value)
    if triggered_id == "virtual-node-update-signal" and triggered_value != constants.OK_SIGNAL:
        # No-op if the validation signal isn't OK
        raise PreventUpdate

    node_name_message_map, client_name_message_map = state.get_message_maps()
    virtual_node_map = state.get_virtual_node_map()

    if triggered_id == "refresh-sli-button":
        state.clear_sli_cache(
        )  # in future, conditionally clear this based on timestamp
        sli_list = state.get_slis()
        node_name_message_map = transformers.apply_slis_to_node_map(
            sli_list,
            node_name_message_map)

    # Perform status computation.
    compute_status.reset_node_statuses(node_name_message_map)
    compute_status.reset_client_statuses(client_name_message_map)
    compute_status.reset_node_statuses(virtual_node_map)

    # combine the two maps of nodes into one dictionary
    # use duck typing -- is this pythonic or a hack?
    all_nodes_map = {**node_name_message_map, **virtual_node_map}  #type: ignore
    compute_status.compute_statuses(
        all_nodes_map,
        client_name_message_map,
    )

    state.set_node_name_message_map(node_name_message_map)
    state.set_client_name_message_map(client_name_message_map)
    state.set_virtual_node_map(virtual_node_map)

    # TODO: memoize this call per Ken's suggestion. This will be refactored when implementing server.
    # something like: elements = state.get_cytoscape_elements()
    elements = converters.cytoscape_elements_from_maps(
        node_name_message_map,
        client_name_message_map,
    )

    # For simplicity, we always perform all graph (view) transformations.
    # This greatly simplifies the implementation each individual transformation, since each step doesn't
    # need to account for changes introduced each subsequent step.
    # However, this isn't the most efficient approach.

    # TODO: apply the status styling here instead of in converters. Will be refactored when implementing server.
    # elements = transformers.apply_status_classes(...)

    if triggered_id == "collapse-virtual-node-button":
        state.set_virtual_node_collapsed_state(
            virtual_node_input_value,
            collapsed=True)

    if triggered_id == "expand-virtual-node-button":
        state.set_virtual_node_collapsed_state(
            virtual_node_input_value,
            collapsed=False)

    elements = transformers.apply_virtual_nodes_to_elements(elements)

    # user_journey_table_selected_row_ids == [] when the user journey datatable isn't created yet
    # it equals [None] when the datatable is created but no row is selected
    if user_journey_table_selected_row_ids == [] or user_journey_table_selected_row_ids == [
            None
    ]:
        active_user_journey_name = None
    else:
        active_user_journey_name = user_journey_table_selected_row_ids[0][0]

    elements = transformers.apply_highlighted_edge_class_to_elements(
        elements,
        active_user_journey_name)

    # Workaround for https://github.com/plotly/dash-cytoscape/issues/106
    # Give new ids to Cytoscape to avoid immutability of edges and parent relationships.
    # TODO: fix this to call only when changing an immutable relationship
    # i.e. don't call when selecting client node -> user_journey_table_selected_row_ids changes to [None]
    elements = transformers.apply_uuid_to_elements(elements)
    return elements


@app.callback(
    Output("node-info-panel",
           "children"),
    [Input("cytoscape-graph",
           "tapNode")],
)
def generate_node_info_panel(tap_node) -> List[Any]:
    """ Generate the node info panel.

    This function is called:
        when a node is clicked

    Args:
        tap_node: Cytoscape element of the tapped/clicked node.

    Returns:
        a List of Dash components.
    """

    if tap_node is None or utils.is_client_cytoscape_node(tap_node):
        raise PreventUpdate

    node_name = tap_node["data"]["ujt_id"]
    node_name_message_map = state.get_node_name_message_map()
    virutal_node_map = state.get_virtual_node_map()

    # See https://github.com/python/typing/issues/81
    node = None  # type: Union[Node, VirtualNode]  # type: ignore
    if node_name in node_name_message_map:
        node = node_name_message_map[node_name]
        is_virtual_node = False
    else:
        node = virutal_node_map[node_name]
        is_virtual_node = True

    header = html.H2(
        f"{utils.relative_name(node_name)} ({utils.human_readable_enum_name(node.node_type, NodeType)})"
    )
    sli_info, child_info, dependency_info = [], [], []

    # Use duck typing for virtual nodes
    if node.child_names:
        child_nodes: List[Union[Node, VirtualNode]] = []
        for child_name in node.child_names:
            if child_name in node_name_message_map:
                child_nodes.append(node_name_message_map[child_name])
            else:
                child_nodes.append(virutal_node_map[child_name])

        child_info = [
            html.H3("Child Node Info"),
            converters.datatable_from_nodes(
                child_nodes,
                use_relative_names=True,
                table_id=constants.CHILD_DATATABLE_ID)
        ]

    # Although we generally prefer "asking forgiveness rather than permission" (try/except) rather than
    # "look before you leap", we avoid having an empty except block by checking the is_virtual_node_property.
    if not is_virtual_node and node.slis:  # type: ignore
        sli_info = [
            html.H3("SLI Info"),
            converters.datatable_from_slis(
                node.slis,  # type: ignore
                table_id=constants.SLI_DATATABLE_ID)
        ]

    if not is_virtual_node and node.dependencies:  # type: ignore
        dependency_nodes = [
            node_name_message_map[dependency.target_name]
            for dependency in node.dependencies  # type: ignore
        ]
        dependency_info = [
            html.H3("Dependency Node Info"),
            converters.datatable_from_nodes(
                dependency_nodes,
                use_relative_names=False,
                table_id=constants.DEPENDENCY_DATATABLE_ID)
        ]

    return [header] + sli_info + child_info + dependency_info


@app.callback(
    Output("client-info-panel",
           "children"),
    [Input("cytoscape-graph",
           "tapNode"),
     Input("client-dropdown",
           "value")],
    prevent_initial_call=True,
)
def generate_client_info_panel(tap_node, dropdown_value: str) -> List[Any]:
    """ Generate the client info panel.

    This function is called:
        when a client is clicked
        when the client dropdown value is modified (i.e. a user selects a dropdown option)

    Args:
        tap_node: Cytoscape element of the tapped/clicked node.
        dropdown_value: The value of the client dropdown

    Returns:
        a List of Dash components.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    # ctx.triggered[0] is either "cytoscape-graph.tapNode" or "client-dropdown.value"
    if triggered_id == "cytoscape-graph":
        tap_node = triggered_value
        if not utils.is_client_cytoscape_node(tap_node):
            raise PreventUpdate

        client_name = tap_node["data"]["ujt_id"]
    else:
        client_name = triggered_value

    client_name_message_map = state.get_client_name_message_map()
    client = client_name_message_map[client_name]
    return converters.datatable_from_client(client, "datatable-client")


@app.callback(
    Output("client-dropdown",
           "value"),
    [Input("cytoscape-graph",
           "tapNode")],
)
def update_client_dropdown_value(tap_node) -> str:
    """ Updates the client dropdown value.

    This function is called:
        when a user selects a client in the graph, to ensure the dropdown value matches the selection

    Args:
        tap_node: Cytoscape element of the tapped/clicked node.

    Returns:
        the new value of the client dropdown.
    """
    if tap_node is None or not utils.is_client_cytoscape_node(tap_node):
        raise PreventUpdate
    return tap_node["data"]["ujt_id"]


@app.callback(
    Output("virtual-node-update-signal",
           "children"),
    [
        Input("add-virtual-node-button",
              "n_clicks_timestamp"),
        Input("delete-virtual-node-button",
              "n_clicks_timestamp"),
    ],
    [
        State("cytoscape-graph",
              "selectedNodeData"),
        State("virtual-node-input",
              "value"),
    ],
    prevent_initial_call=True,
)
def validate_selected_nodes_for_virtual_node(
        add_n_clicks_timestamp,
        delete_n_clicks_timestamp,
        selected_node_data,
        virtual_node_name):
    """ Validate the selected nodes before adding them to virutal node.

    Nodes with parents cannot be added directly (their parents must be added instead). 
    Client nodes cannot be added to virtual nodes.
    A single node with no children cannot be collapsed.

    This function is called:
        when the add button is clicked
        when the delete button is clicked

    Args:
        add_n_clicks_timestamp: Timestamp of when the add button was clicked. Value unused, input only provided to register callback.
        delete_n_clicks_timestamp: Timestamp of when the delete button was clicked. Value unused, input only provided to register callback.
        selected_node_data: List of data dictionaries of selected cytoscape elements.
        virtual_node_name: The name of the virtual node to add or delete.

    Returns:
        A string to be placed in the children property of the virtual-node-update-signal hidden div. 
        This hidden div is used to ensure the callbacks to update the error modal visibility and cytoscape graph
        are called in the correct order. 
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_id == "add-virtual-node-button":
        if selected_node_data is None:
            return "Error: Must select at least one node to to add to virtual node."

        node_name_message_map, client_name_message_map = state.get_message_maps()
        for node_data in selected_node_data:
            if node_data["ujt_id"] in client_name_message_map:
                return "Error: Cannot add clients to virtual node."

            if node_data["ujt_id"] in node_name_message_map:
                node = node_name_message_map[node_data["ujt_id"]]
                if node.parent_name != "":
                    return "Error: Cannot add individual child node to virtual node. Try adding the entire parent."

        if len(selected_node_data) == 1 and not node.child_names:
            return "Error: A single node with no children cannot be added to virtual node."

        virtual_node_map = state.get_virtual_node_map()
        if virtual_node_name in virtual_node_map:
            return "Error: A virtual node with that name already exists."

        state.add_virtual_node(virtual_node_name, selected_node_data)
    else:
        virtual_node_map = state.get_virtual_node_map()
        if virtual_node_name not in virtual_node_map:
            return "Error: The entered name doesn't match any existing virtual nodes."

        state.delete_virtual_node(virtual_node_name)

    return constants.OK_SIGNAL


@app.callback(
    [
        Output("collapse-error-modal",
               "is_open"),
        Output("collapse-error-modal-body",
               "children"),
    ],
    [
        Input("collapse-error-modal-close",
              "n_clicks_timestamp"),
        Input("virtual-node-update-signal",
              "children"),
    ],
    prevent_initial_call=True,
)
def toggle_collapse_error_modal(n_clicks_timestamp,
                                signal_message) -> Tuple[bool,
                                                         str]:
    """ Close and open the error modal.

    This function is called:
        when an error occurs during the validation of virtual node creation/deletion
        when the close button is clicked.

    Args:
        n_clicks_timestamp: Timestamp of when the close button was clicked. Value unused, input only provided to register callback.
        signal_message: The valid of the signal from the signal hidden div. Used to determine whether the modal should open.

    Returns:
        A tuple containing a boolean and string.
        The boolean indicates whether the modal should open.
        The string is placed into the body of the modal.
    """
    ctx = dash.callback_context

    triggered_id, triggered_prop = ctx.triggered[0]["prop_id"].split(".")
    triggered_value = ctx.triggered[0]["value"]

    if triggered_id == "collapse-error-modal-close":
        return False, ""

    if triggered_value != "OK":
        return True, triggered_value

    return False, ""
