""" Callbacks that handle virtual node functionality.
"""

from typing import Any, Optional, Tuple

import dash
from dash.dependencies import Input, Output, State

from .. import constants, converters, id_constants, state, utils
from ..dash_app import app


@app.callback(
    Output(id_constants.SIGNAL_VIRTUAL_NODE_ADD, "children"),
    Input(id_constants.ADD_VIRTUAL_NODE_BUTTON, "n_clicks_timestamp"),
    [
        State(id_constants.CYTOSCAPE_GRAPH, "selectedNodeData"),
        State(id_constants.VIRTUAL_NODE_INPUT, "value"),
    ],
    prevent_initial_call=True,
)
def add_virtual_node(add_n_clicks_timestamp, selected_node_data, virtual_node_name):
    """Validates and creates a virtual nodes with the the selected cytoscape nodes.

    Nodes with parents cannot be added directly (their parents must be added instead).
    Client nodes cannot be added to virtual nodes.
    A single node with no children cannot be collapsed.

    This function is called:
        when the add button is clicked

    Args:
        add_n_clicks_timestamp: Timestamp of when the add button was clicked. Value unused, input only provided to register callback.
        selected_node_data: List of data dictionaries of selected cytoscape elements.
        virtual_node_name: The name of the virtual node to add or delete.

    Returns:
        A string to be placed in the children property of the SIGNAL_VIRTUAL_NODE_ADD hidden div.
        This hidden div is used to ensure the callbacks to update the error modal visibility and cytoscape graph
        are called in the correct order.
    """
    if selected_node_data is None or selected_node_data == []:
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
        return "Error: A single node with no children cannot be added to virtual node."

    virtual_node_map = state.get_virtual_node_map()
    if virtual_node_name in virtual_node_map:
        return "Error: A virtual node with that name already exists."

    state.add_virtual_node(virtual_node_name, selected_node_data)

    return constants.OK_SIGNAL


@app.callback(
    Output(id_constants.SIGNAL_VIRTUAL_NODE_DELETE, "children"),
    Input(id_constants.DELETE_VIRTUAL_NODE_BUTTON, "n_clicks_timestamp"),
    State(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
    prevent_initial_call=True,
)
def delete_virtual_node(
    delete_n_clicks_timestamp,
    tap_node,
):
    """Handles deleting virtual nodes.

    This function is called:
        when the delete button is clicked

    Args:
        delete_n_clicks_timestamp: Timestamp of when the delete button was clicked. Value unused, input only provided to register callback.
        tap_node: The last clicked graph node.

    Returns:
        A string to be placed in the children property of the SIGNAL_VIRTUAL_NODE_DELETE hidden div.
        This hidden div is used to ensure the callbacks to update the error modal visibility and cytoscape graph
        are called in the correct order.
    """

    virtual_node_map = state.get_virtual_node_map()

    if tap_node is None or tap_node["data"]["ujt_id"] not in virtual_node_map:
        return "Error: Please select a virtual node."

    state.delete_virtual_node(tap_node["data"]["ujt_id"])

    return constants.OK_SIGNAL


@app.callback(
    Output(id_constants.SIGNAL_VIRTUAL_NODE_EXPAND, "children"),
    Input(id_constants.EXPAND_VIRTUAL_NODE_BUTTON, "n_clicks_timestamp"),
    State(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
    prevent_initial_call=True,
)
def expand_virtual_node(
    expand_n_clicks_timestamp,
    tap_node,
) -> str:
    """Expands a virtual node.

    This function is called:
        when the expand virtual node button is clicked

    Args:
        expand_n_clicks_timestamp: Timestamp of when the virtual node button was clicked.
            Value unused, input only provided to register callback.
        tap_node: The last clicked graph node.

    Returns:
        OK_SIGNAL or an error message to be placed in the error modal.
    """
    virtual_node_map = state.get_virtual_node_map()

    if tap_node is None or tap_node["data"]["ujt_id"] not in virtual_node_map:
        return "Error: Please select a virtual node."

    state.set_virtual_node_collapsed_state(tap_node["data"]["ujt_id"], collapsed=False)

    return constants.OK_SIGNAL


@app.callback(
    Output(id_constants.SIGNAL_VIRTUAL_NODE_COLLAPSE, "children"),
    Input(id_constants.COLLAPSE_VIRTUAL_NODE_BUTTON, "n_clicks_timestamp"),
    State(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
    prevent_initial_call=True,
)
def collapse_virtual_node(
    collapse_n_clicks_timestamp,
    tap_node,
) -> str:
    """Collapses a virtual node.

    This function is called:
        when the collapse virtual node button is clicked

    Args:
        expand_n_clicks_timestamp: Timestamp of when the virtual node button was clicked.
            Value unused, input only provided to register callback.
        tap_node: The last clicked graph node.

    Returns:
        OK_SIGNAL or an error message to be placed in the error modal.
    """
    virtual_node_map = state.get_virtual_node_map()

    if tap_node is None or tap_node["data"]["ujt_id"] not in virtual_node_map:
        return "Error: Please select a virtual node."

    state.set_virtual_node_collapsed_state(tap_node["data"]["ujt_id"], collapsed=True)

    return constants.OK_SIGNAL


@app.callback(
    Output(id_constants.SIGNAL_VIRTUAL_NODE_TOGGLE_ALL, "children"),
    Input(id_constants.TOGGLE_ALL_VIRTUAL_NODE_BUTTON, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_all_collapse_virtual_node(toggle_all_n_clicks: int) -> str:
    """Collapses and expands all virtual nodes.

    This function is called:
        when the toggle all virtual node button is clicked

    Args:
        toggle_all_n_clicks: Number of times the toggle all virtual node button was clicked.

    Returns:
        OK_SIGNAL.
    """

    collapsed = toggle_all_n_clicks % 2 == 0
    virtual_node_map = state.get_virtual_node_map()
    for virtual_node_name in virtual_node_map:
        state.set_virtual_node_collapsed_state(virtual_node_name, collapsed=collapsed)

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
def update_virtual_node_error_modal(
    n_clicks_timestamp,
    signal_message,
) -> Tuple[bool, Optional[Any]]:
    """Updates the error modal message and open state.

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
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_id == id_constants.COLLAPSE_ERROR_MODAL_CLOSE:
        return False, ""

    if triggered_value != constants.OK_SIGNAL:
        return True, triggered_value

    return False, ""


@app.callback(
    Output(id_constants.USER_JOURNEY_DROPDOWN, "options"),
    [
        Input(id_constants.SIGNAL_VIRTUAL_NODE_ADD, "children"),
        Input(id_constants.SIGNAL_VIRTUAL_NODE_DELETE, "children"),
    ],
)
def update_user_journey_dropdown_options(
    virtual_node_add_signal,
    virtual_node_delete_signal,
):
    """Updates the options in the user journey dropdown on virtual node changes.

    This function is called:
        when a virtual node is created or deleted.

    Args:
        virtual_node_add_signal: Signal indicating a virtual node was added.
        virtual_node_delete_signal: Signal indicating a virtual node was deleted.

    Returns:
        A list of options for the user journey dropdown.
    """
    node_name_message_map, client_name_message_map = state.get_message_maps()
    virtual_node_map = state.get_virtual_node_map()

    return converters.user_journey_dropdown_options_from_maps(
        node_name_message_map, client_name_message_map, virtual_node_map
    )
