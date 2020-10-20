""" Callbacks that handle tag application/removal functionality.
"""


import dash
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate

from .. import constants, id_constants, state, utils
from ..dash_app import app


@app.callback(
    Output(id_constants.SIGNAL_APPLIED_TAG_ADD, "children"),
    Input({id_constants.ADD_APPLIED_TAG_BUTTON: ALL}, "n_clicks_timestamp"),
    [
        State(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
        State(id_constants.CYTOSCAPE_GRAPH, "tapEdge"),
    ],
    prevent_initial_call=True,
)
def apply_new_empty_tag(add_timestamps, tap_node, tap_edge):
    """Handles applying a new empty tag to the tag map.

    This function is called:
        when the add applied tag button is clicked.

    Args:
        add_timestamps: List of the timestamps of the ADD_APPLIED_TAG_BUTTON buttons was called.
            Value unused, input only provided to register callback.
            Should only contain one value.
        tap_node: The cytoscape element of the latest tapped node.
        tap_edge: The cytoscape element of the latest tapped edge.

    Returns:
        A signal to add to the SIGNAL_APPLIED_TAG_ADD hidden div.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    # When the button is initially added, it fires a callback.
    # We want to prevent this callback from making changes to the update signal.
    if triggered_value is None:
        raise PreventUpdate

    ujt_id = utils.get_latest_tapped_element(tap_node, tap_edge)["data"]["ujt_id"]

    state.add_tag_to_element(ujt_id, "")
    return constants.OK_SIGNAL


@app.callback(
    Output(id_constants.SIGNAL_APPLIED_TAG_REMOVE, "children"),
    Input(
        {
            id_constants.REMOVE_APPLIED_TAG_BUTTON: id_constants.REMOVE_APPLIED_TAG_BUTTON,
            "index": ALL,
        },
        "n_clicks_timestamp",
    ),
    [
        State(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
        State(id_constants.CYTOSCAPE_GRAPH, "tapEdge"),
    ],
    prevent_initial_call=True,
)
def remove_applied_tag(
    remove_timestamps,
    tap_node,
    tap_edge,
):
    """Handles removing tags from the tag map.

    This function is called:
        when a REMOVE_APPLIED_TAG_BUTTON is clicked

    Args:
        remove_timestamps: List of the timestamps of when REMOVE_APPLIED_TAG_BUTTON buttons were called.
            Value unused, input only provided to register callback.
            Should only contain one value.
        tap_node: The cytoscape element of the latest tapped node.
        tap_edge: The cytoscape element of the latest tapped edge.

    Returns:
        A signal to add to the SIGNAL_APPLIED_TAG_REMOVE hidden div.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    # When the button is initially added, it fires a callback.
    # We want to prevent this callback from making changes to the update signal.
    if triggered_value is None:
        raise PreventUpdate

    # Unfortunately, we have to convert the stringified dict back to a dict.
    # Dash doesn't provide us any other method to see which element triggered the callback.
    # This isn't very elegant, but I don't see any other way to proceed.
    id_dict = utils.string_to_dict(triggered_id)

    ujt_id = utils.get_latest_tapped_element(tap_node, tap_edge)["data"]["ujt_id"]

    tag_idx = id_dict["index"]
    state.remove_tag_from_element(ujt_id, tag_idx)

    return constants.OK_SIGNAL


@app.callback(
    Output(id_constants.SIGNAL_APPLIED_TAG_MODIFY, "children"),
    Input(
        {
            id_constants.APPLY_TAG_DROPDOWN: id_constants.APPLY_TAG_DROPDOWN,
            "index": ALL,
        },
        "value",
    ),
    [
        State(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
        State(id_constants.CYTOSCAPE_GRAPH, "tapEdge"),
    ],
    prevent_initial_call=True,
)
def modify_applied_tag(dropdown_values, tap_node, tap_edge):
    """Updates the corresponding applied tag in the tag map.

    This function is called:
        when an APPLY_TAG_DROPDOWN value is updated

    Args:
        dropdown_values: the values of the APPLY_TAG_DROPDOWN dropdown menus.
        tap_node: Cytoscape element of the tapped/clicked node.
        tap_edge: Cytoscape element of the tapped/clicked edge.

    Returns:
        A signal to be placed in the SIGNAL_APPLIED_TAG_MODIFY hidden div.
    """
    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_value is None:
        raise PreventUpdate

    # Unfortunately, we have to convert the stringified dict back to a dict.
    # Dash doesn't provide us any other method to see which element triggered the callback.
    # This isn't very elegant, but I don't see any other way to proceed.
    id_dict = utils.string_to_dict(triggered_id)

    ujt_id = utils.get_latest_tapped_element(tap_node, tap_edge)["data"]["ujt_id"]

    tag_idx = id_dict["index"]
    tag_value = dropdown_values[tag_idx]

    state.update_applied_tag(ujt_id, tag_idx, tag_value)
    return constants.OK_SIGNAL
