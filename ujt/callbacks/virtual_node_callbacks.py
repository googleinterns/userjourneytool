""" Callbacks that handle virtual node functionality.
"""

from typing import Tuple

import dash
from dash.dependencies import Input, Output, State

from .. import constants, converters, id_constants, state, utils
from ..dash_app import app


@app.callback(
    Output(id_constants.SIGNAL_VIRTUAL_NODE_UPDATE, "children"),
    [
        Input(id_constants.ADD_VIRTUAL_NODE_BUTTON, "n_clicks_timestamp"),
        Input(id_constants.DELETE_VIRTUAL_NODE_BUTTON, "n_clicks_timestamp"),
    ],
    [
        State(id_constants.CYTOSCAPE_GRAPH, "selectedNodeData"),
        State(id_constants.VIRTUAL_NODE_INPUT, "value"),
    ],
    prevent_initial_call=True,
)
def validate_selected_nodes_for_virtual_node(
    add_n_clicks_timestamp,
    delete_n_clicks_timestamp,
    selected_node_data,
    virtual_node_name,
):
    """Validate the selected nodes before adding them to virutal node.

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
        A string to be placed in the children property of the SIGNAL_VIRTUAL_NODE_UPDATE hidden div.
        This hidden div is used to ensure the callbacks to update the error modal visibility and cytoscape graph
        are called in the correct order.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_id == id_constants.ADD_VIRTUAL_NODE_BUTTON:
        if selected_node_data is None:
            return "Error: Must select at least one node to to add to virtual node."

        node_name_message_map, client_name_message_map = state.get_message_maps()
        if (
            virtual_node_name in node_name_message_map
            or virtual_node_name in client_name_message_map
        ):
            return "Error: Virtual node cannot share a name with a real node or client."

        for node_data in selected_node_data:
            if node_data["ujt_id"] in client_name_message_map:
                return "Error: Cannot add clients to virtual node."

            if node_data["ujt_id"] in node_name_message_map:
                node = node_name_message_map[node_data["ujt_id"]]
                if node.parent_name != "":
                    return "Error: Cannot add individual child node to virtual node. Try adding the entire parent."

        if len(selected_node_data) == 1 and not node.child_names:
            return (
                "Error: A single node with no children cannot be added to virtual node."
            )

        virtual_node_map = state.get_virtual_node_map()
        if virtual_node_name in virtual_node_map:
            return "Error: A virtual node with that name already exists."

        state.add_virtual_node(virtual_node_name, selected_node_data)
    elif triggered_id == id_constants.DELETE_VIRTUAL_NODE_BUTTON:
        virtual_node_map = state.get_virtual_node_map()
        if virtual_node_name not in virtual_node_map:
            return "Error: The entered name doesn't match any existing virtual nodes."

        state.delete_virtual_node(virtual_node_name)
    else:
        raise ValueError

    return constants.OK_SIGNAL


@app.callback(
    [
        Output(id_constants.COLLAPSE_ERROR_MODAL, "is_open"),
        Output(id_constants.COLLAPSE_ERROR_MODAL_BODY, "children"),
    ],
    [
        Input(id_constants.COLLAPSE_ERROR_MODAL_CLOSE, "n_clicks_timestamp"),
        Input(id_constants.SIGNAL_VIRTUAL_NODE_UPDATE, "children"),
    ],
    prevent_initial_call=True,
)
def toggle_collapse_error_modal(n_clicks_timestamp, signal_message) -> Tuple[bool, str]:
    """Closes and opens the error modal.

    This function is called:
        when an error occurs during the validation of virtual node creation/deletion
        when the close button is clicked.

    Args:
        n_clicks_timestamp: Timestamp of when the close button was clicked. Value unused, input only provided to register callback.
        signal_message: The value of the signal from the signal hidden div. Used to determine whether the modal should open.

    Returns:
        A tuple containing a boolean and string.
        The boolean indicates whether the modal should open.
        The string is placed into the body of the modal.
    """
    ctx = dash.callback_context

    triggered_id, triggered_prop = ctx.triggered[0]["prop_id"].split(".")
    triggered_value = ctx.triggered[0]["value"]

    if triggered_id == id_constants.COLLAPSE_ERROR_MODAL_CLOSE:
        return False, ""

    if triggered_value != "OK":
        return True, triggered_value

    return False, ""

@app.callback(
    Output(id_constants.USER_JOURNEY_DROPDOWN, "options"),
    Input(id_constants.SIGNAL_VIRTUAL_NODE_UPDATE, "children"),
)
def update_user_journey_dropdown_options(virtual_node_update_signal):
    """Updates the options in the user journey dropdown on virtual node changes.

    This function is called:
        when a virtual node is created or deleted.

    Args:
        virtual_node_update_signal: Signal indicating a virtual node was modified.

    Returns:
        A list of options for the user journey dropdown.
    """
    node_name_message_map, client_name_message_map = state.get_message_maps()
    virtual_node_map = state.get_virtual_node_map()

    return converters.dropdown_options_from_maps(
        node_name_message_map, client_name_message_map, virtual_node_map
    )
