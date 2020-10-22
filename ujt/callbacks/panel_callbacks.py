""" Callbacks that generate the panels below the cytoscape graph.
"""

from typing import Any, Dict, List, Tuple

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from graph_structures_pb2 import UserJourney

from .. import components, converters, id_constants, state, utils
from ..dash_app import app


@app.callback(
    Output(id_constants.SELECTED_INFO_PANEL, "children"),
    [
        Input(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
        Input(id_constants.CYTOSCAPE_GRAPH, "tapEdge"),
        Input(id_constants.SIGNAL_TAG_UPDATE, "children"),
        Input(id_constants.SIGNAL_APPLIED_TAG_UPDATE, "children"),
    ],
    prevent_initial_call=True,
)
def generate_selected_info_panel(
    tap_node, tap_edge, tag_update_signal, applied_tag_update_signal
) -> List[Any]:
    """Generate the node info panel.

    This function is called:
        when a node is clicked
        when an edge is clicked

    Args:
        tap_node: Cytoscape element of the tapped/clicked node.
        tap_edge: Cytoscape element of the tapped/clicked edge.
        tag_update_signal: The signal indicating a tag was created or deleted. Used to update dropdown options.
        applied_tag_update_signal: The signal indicating that a tag was added or removed to the selected element.


    Returns:
        a List of Dash components.
    """

    if tap_node is None and tap_edge is None:
        raise PreventUpdate

    latest_tapped_element = utils.get_latest_tapped_element(tap_node, tap_edge)
    ujt_id = latest_tapped_element["data"]["ujt_id"]

    out = []
    includes_override_dropdown = False
    if latest_tapped_element == tap_node:
        node_name = tap_node["data"]["ujt_id"]
        if not utils.is_client_cytoscape_node(tap_node):
            out += components.get_node_info_panel_components(node_name)
            includes_override_dropdown = True
    else:
        # just generate this header here for now,
        # probably don't need to make a new component function for it.
        source, target = ujt_id.split("/")
        header = html.Div(
            f"Edge from {utils.relative_name(source)} to {utils.relative_name(target)}"
        )
        out.append(header)

    out += components.get_apply_tag_components(ujt_id)

    if not includes_override_dropdown:
        # This is a pretty bad hack.
        # The update_graph_elements callback is called (via pattern matching)
        # when the OVERRIDE_DROPDOWN component is removed (a node was previously selected, then a client/edge was selected).
        # This causes us to update the UUID and re-render the graph, which is functionally OK but visually distracting.
        # The callback is fired with triggered_id = triggered_prop = triggered_value = None, making it indistinguishible
        # from the initial callback (at load time) from the arguments only (without perhaps creating an additional flag).

        # By providing this hidden override dropdown with the same ID key, the callback fires but we can indicate that
        # it was triggered by the removal of the override dropdown.
        # The other workaround is to implement more complicated logic in determining when we need to append the UUID.
        # There are a lot of different cases because the callback handles a wide variety of inputs.
        # Although this is a hack, I feel it's preferable to complicating the logic in update_graph_elements further.
        # I'd like to keep complexity out of update_graph_elements to ensure that it's flexible and maintainable, as
        # that function is likely to be modified when adding additional features in the future.

        dummy_override_dropdown = dcc.Dropdown(
            id={id_constants.OVERRIDE_DROPDOWN: id_constants.OVERRIDE_DROPDOWN_HIDDEN},
            style={"display": "none"},
        )
        out.append(dummy_override_dropdown)

    return out


@app.callback(
    Output(id_constants.USER_JOURNEY_INFO_PANEL, "children"),
    Input(id_constants.USER_JOURNEY_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def generate_user_journey_info_panel(dropdown_value: str) -> List[Any]:
    """Generate the client info panel.

    This function is called:
        when the user journey dropdown value is modified (i.e. a user selects a dropdown option)

    Args:
        dropdown_value: The value of the client dropdown

    Returns:
        a List of Dash components.
    """

    node_name_message_map, client_name_message_map = state.get_message_maps()
    virtual_node_map = state.get_virtual_node_map()

    if dropdown_value in client_name_message_map:
        client = client_name_message_map[dropdown_value]
        return converters.user_journey_datatable_from_user_journeys(
            client.user_journeys, id_constants.USER_JOURNEY_DATATABLE
        )

    # associate the name of the user journey with the nodes that it passes through
    node_user_journey_map: Dict[
        str, List[UserJourney]
    ] = state.get_node_to_user_journey_map()

    if dropdown_value in node_name_message_map:
        return converters.user_journey_datatable_from_user_journeys(
            node_user_journey_map[dropdown_value], id_constants.USER_JOURNEY_DATATABLE
        )

    if dropdown_value in virtual_node_map:
        node_names_in_virtual_node = utils.get_all_node_names_within_virtual_node(
            dropdown_value, node_name_message_map, virtual_node_map
        )
        user_journeys = []
        # maybe we can try to improve this if the input size is large
        for node_name in node_names_in_virtual_node:
            for user_journey in node_user_journey_map[node_name]:
                if user_journey not in user_journeys:
                    user_journeys.append(user_journey)

        return converters.user_journey_datatable_from_user_journeys(
            user_journeys, id_constants.USER_JOURNEY_DATATABLE
        )

    raise ValueError


@app.callback(
    Output(id_constants.CREATE_TAG_PANEL, "children"),
    Input(id_constants.SIGNAL_TAG_CREATE, "children"),
    Input(id_constants.SIGNAL_TAG_DELETE, "children"),
)
def generate_create_tag_panel(create_tag_signal, delete_tag_signal):
    """Handles generating the tag creation and deletion panel.

    This function is called:
        when a new tag is created.
        when a tag is deleted.

    Args:
        create_tag_signal: Signal indicating that a tag was created.
            Value unused, input only provided to register callback.
        delete_tag_signal: Signal indicating that a tag was deleted.
            Value unused, input only provided to register callback.

    Returns:
        A list of components to be placed in the CREATE_TAG_PANEL.
    """
    return components.get_create_tag_components()


@app.callback(
    Output(id_constants.VIEW_PANEL, "children"),
    [
        Input(id_constants.SIGNAL_VIEW_UPDATE, "children"),
        Input(id_constants.SIGNAL_TAG_UPDATE, "children"),
        Input(id_constants.SIGNAL_STYLE_UPDATE, "children"),
    ],
    State(id_constants.VIEW_STORE, "data"),
)
def generate_view_panel(
    view_update_signal,
    tag_update_signal,
    style_update_signal,
    view_list: List[Tuple[str, str]],
):
    """Handles generating the view creation and deletion panel.

    This function is called:
        when a view is updated.
        when a tag is updated.
        when a style is updated

    Args:
        view_update_signal: Signal indicating that a view was updated.
            Value unused, input only provided to register callback.
        tag_update_signal: Signal indicating that a tag was updated.
            Value unused, input only provided to register callback.
        style_update_signal: Signal indicating that a style was updated.
            Value unused, input only provided to register callback.
        view_list: The current list of views.

    Returns:
        A list of components to be placed in the VIEW_PANEL.
    """
    return components.get_view_components(view_list)
