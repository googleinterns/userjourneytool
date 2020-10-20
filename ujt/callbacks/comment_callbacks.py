""" Callbacks that handle comment functionality.
"""


from dash.dependencies import ALL, MATCH, Input, Output, State

from .. import id_constants, state
from ..dash_app import app


@app.callback(
    # We can't use ALL in the output, so we use MATCH.
    # However, since there's only one component with this key, the functionality is identical.
    Output({id_constants.NODE_COMMENT_TEXTAREA: MATCH}, "value"),
    Input({id_constants.DISCARD_COMMENT_TEXTAREA_BUTTON: ALL}, "n_clicks_timestamp"),
    State(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
    prevent_initial_call=True,
)
def discard_comment(discard_n_clicks_timestamp, tap_node):
    """Handles the functionality for discarding comments.
    .
        This function is called:
            when the discard comment is clicked.

        Args:
            discard_n_clicks_timestamp: List of the timestamps of when components matching the close id were clicked.
                Should only contain one element if the key is unique.
                Value unused, input only provided to register callback.
            tap_node: Cytoscape element of the tapped/clicked node.

        Returns:
            The updated value of the textarea.
    """

    node_name = tap_node["data"]["ujt_id"]
    node_name_message_map = state.get_node_name_message_map()
    virtual_node_map = state.get_virtual_node_map()

    if node_name in node_name_message_map:
        return node_name_message_map[node_name].comment
    else:
        return virtual_node_map[node_name].comment


@app.callback(
    Output({id_constants.SAVE_COMMENT_TOAST: ALL}, "is_open"),
    Input({id_constants.SAVE_COMMENT_TEXTAREA_BUTTON: ALL}, "n_clicks_timestamp"),
    [
        State(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
        State({id_constants.NODE_COMMENT_TEXTAREA: ALL}, "value"),
    ],
    prevent_initial_call=True,
)
def save_comment(save_n_clicks_timestamp, tap_node, new_comment):
    """Handles the functionality for saving comments
    .
        This function is called:
            when the save comment button is clicked.

        Args:
            save_n_clicks_timestamp: List of the timestamps of when components matching the save id were clicked.
                Should only contain one element if the key is unique.
                Value unused, input only provided to register callback.
            tap_node: Cytoscape element of the tapped/clicked node.
            new_comment: List of values of components matching the textarea id.
                Should only contain one element if the key is unique.

        Returns:
            The updated value of the textarea.
    """

    new_comment = new_comment[0]
    node_name = tap_node["data"]["ujt_id"]
    state.set_comment(node_name, new_comment)

    # wrap output in a list since we used pattern matching. should only ever be one toast.
    return [True]
