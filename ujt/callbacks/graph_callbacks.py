""" Callbacks that modify properties of the cytoscape graph. 
"""

import datetime as dt
from typing import Any, Dict, List, Tuple

import dash
import google.protobuf.json_format as json_format
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate
from graph_structures_pb2 import SLI

from .. import (
    compute_status,
    constants,
    converters,
    id_constants,
    state,
    transformers,
    utils,
)
from ..dash_app import app


@app.callback(
    Output(id_constants.CYTOSCAPE_GRAPH, "elements"),
    [
        Input(id_constants.REFRESH_SLI_BUTTON, "n_clicks_timestamp"),
        Input({id_constants.USER_JOURNEY_DATATABLE: ALL}, "selected_row_ids"),
        Input(id_constants.SIGNAL_VIRTUAL_NODE_UPDATE, "children"),
        Input(id_constants.COLLAPSE_VIRTUAL_NODE_BUTTON, "n_clicks_timestamp"),
        Input(id_constants.EXPAND_VIRTUAL_NODE_BUTTON, "n_clicks_timestamp"),
        Input({id_constants.OVERRIDE_DROPDOWN: ALL}, "value"),
        Input(id_constants.SIGNAL_COMPOSITE_TAGGING_UPDATE, "children"),
        Input(id_constants.CHANGE_OVER_TIME_SLI_STORE, "data"),
    ],
    [
        State(id_constants.CYTOSCAPE_GRAPH, "elements"),
        State(id_constants.CYTOSCAPE_GRAPH, "selectedNodeData"),
        State(id_constants.VIRTUAL_NODE_INPUT, "value"),
        State(id_constants.CYTOSCAPE_GRAPH, "tapNode"),
        State(id_constants.VIEW_STORE, "data"),
    ],
)
def update_graph_elements(
    # Input
    refresh_n_clicks_timestamp: int,
    user_journey_table_selected_row_ids: List[str],
    virtual_node_update_signal: str,
    collapse_n_clicks_timestamp: int,
    expand_n_clicks_timestamp: int,
    override_dropdown_value: int,
    composite_tagging_update_signal: str,
    change_over_time_data: Dict[str, Any],
    # State
    state_elements: List[Dict[str, Any]],
    selected_node_data: List[Dict[str, Any]],
    virtual_node_input_value: str,
    tap_node: Dict[str, Any],
    view_list: List[Tuple[str, str]],
):
    """Update the elements of the cytoscape graph.

    This function is called:
        on startup to generate the graph
        when the refresh button is clicked to regenerate the graph
        when row is selected in the User Journey Datatable to highlight the User Journey edges through the path
        when a virtual node is added or deleted (via the SIGNAL_VIRTUAL_NODE_UPDATE)
        when the collapse button is clicked virtual node
        when the expand button is clicked to expand virtual nodes
        when a tag, style, or view is updated.

    We need this callback to handle these (generally unrelated) situations because Dash only supports assigning
    a single callback to a given output element.

    Args:
        refresh_n_clicks_timestamp: Timestamp of when the refresh button was clicked.
            Value unused, input only provided to register callback.
        user_journey_table_selected_row_ids: List of selected row ids from the user journey datatable.
            Should contain only one element. Used for highlighting a path through the graph.
        virtual_node_update_signal: String used as a signal to indicate that the virtual node addition/deletion was valid.
        collapse_n_clicks_timestamp: Timestamp of when the collapse button was clicked.
            Value unused, input only provided to register callback.
        expand_n_clicks_timestamp: Timestamp of when the expand button was clicked.
            Value unused, input only provided to register callback.
        override_dropdown_value: Status enum value of the status to override for the node.
        change_over_time_data: Either an empty dictionary, or a dictionary with keys
            "start_timestamp" mapped to a float POSIX timestamp,
            "end_timestamp" mapped to a float POSIX timestamp, and
            "dict_slis" mapped to a list of SLIs represented as dictionaries.
            The SLIs as dictionaries need to be parsed by the json_format module.
            Used to apply styles for the Change Over Time feature.

        state_elements: The list of current cytoscape graph elements.
        selected_node_data: The list of data dictionaries for selected nodes.
            Used to create virtual nodes.
        virtual_node_input_value: The value of the virtual node input box.
            Used to perform all virtual node operations.
        tap_node: The cytoscape element of the latest tapped node.
            Used to check which node to override the status of.
        view_list: The current list of views (specific to each browser).
    Returns:
        A dictionary of cytoscape elements describing the nodes and edges of the graph.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)
    # print("updating elements:", ctx.triggered)  # DEBUG_REMOVE
    if (
        triggered_id == id_constants.SIGNAL_VIRTUAL_NODE_UPDATE
        and triggered_value != constants.OK_SIGNAL
    ) or (
        triggered_id
        == f"""{{"{id_constants.OVERRIDE_DROPDOWN}":"{id_constants.OVERRIDE_DROPDOWN_HIDDEN}"}}"""
    ):
        # No-op if :
        #   the validation signal isn't OK
        #   callback fired from dummy override dropdown
        raise PreventUpdate

    node_name_message_map, client_name_message_map = state.get_message_maps()
    virtual_node_map = state.get_virtual_node_map()

    elements = state.get_cytoscape_elements()

    # This condition determines if we need to recompute node statuses.
    if triggered_id in [
        None,  # initial call
        id_constants.REFRESH_SLI_BUTTON,
        id_constants.SIGNAL_VIRTUAL_NODE_UPDATE,
        f"""{{"{id_constants.OVERRIDE_DROPDOWN}":"{id_constants.OVERRIDE_DROPDOWN}"}}""",  # Dash provides the value as a stringified dict
    ]:
        if triggered_id == id_constants.REFRESH_SLI_BUTTON:
            state.clear_sli_cache()  # in future, conditionally clear this based on timestamp
            sli_list = state.get_slis()
            node_name_message_map = transformers.apply_slis_to_node_map(
                sli_list, node_name_message_map
            )

        if (
            triggered_id
            == f"""{{"{id_constants.OVERRIDE_DROPDOWN}":"{id_constants.OVERRIDE_DROPDOWN}"}}"""
        ):
            node_name = tap_node["data"]["ujt_id"]
            state.set_node_override_status(
                node_name,
                triggered_value,  # type: ignore
                node_name_message_map=node_name_message_map,
                virtual_node_map=virtual_node_map,
            )

        # Perform status computation.
        # We can refactor this block later as well, but no other function should call it...
        compute_status.reset_node_statuses(node_name_message_map)
        compute_status.reset_client_statuses(client_name_message_map)
        compute_status.reset_node_statuses(virtual_node_map)

        # combine the two maps of nodes into one dictionary
        # use duck typing -- is this pythonic or a hack?
        all_nodes_map = {**node_name_message_map, **virtual_node_map}  # type: ignore
        compute_status.compute_statuses(
            all_nodes_map,
            client_name_message_map,
        )

        state.set_node_name_message_map(node_name_message_map)
        state.set_client_name_message_map(client_name_message_map)
        state.set_virtual_node_map(virtual_node_map)

    # For simplicity, we always perform all graph (view) transformations.
    # This greatly simplifies the implementation each individual transformation, since each step doesn't
    # need to account for changes introduced each subsequent step.
    # However, this isn't the most efficient approach.

    if triggered_id == id_constants.COLLAPSE_VIRTUAL_NODE_BUTTON:
        state.set_virtual_node_collapsed_state(virtual_node_input_value, collapsed=True)

    if triggered_id == id_constants.EXPAND_VIRTUAL_NODE_BUTTON:
        state.set_virtual_node_collapsed_state(
            virtual_node_input_value, collapsed=False
        )

    elements = transformers.apply_virtual_nodes_to_elements(elements)

    # user_journey_table_selected_row_ids == [] when the user journey datatable isn't created yet
    # it equals [None] when the datatable is created but no row is selected
    if user_journey_table_selected_row_ids in [[], [None]]:
        active_user_journey_name = None
    else:
        active_user_journey_name = user_journey_table_selected_row_ids[0][0]

    elements = transformers.apply_highlighted_edge_class_to_elements(
        elements, active_user_journey_name
    )

    if change_over_time_data == {}:
        # The following calls to apply classes to elements, which are then matched to styles
        transformers.apply_node_property_classes(
            elements,
            node_name_message_map,
            client_name_message_map,
            virtual_node_map,
        )

        tag_map = state.get_tag_map()
        transformers.apply_view_classes(
            elements,
            tag_map,
            view_list,
        )
    else:
        start_time = dt.datetime.fromtimestamp(change_over_time_data["start_timestamp"])
        end_time = dt.datetime.fromtimestamp(change_over_time_data["end_timestamp"])
        dict_slis = change_over_time_data["dict_slis"]
        slis = [json_format.ParseDict(dict_sli, SLI()) for dict_sli in dict_slis]
        elements = transformers.apply_change_over_time_classes(
            elements,
            slis,
            start_time,
            end_time,
        )
    # print(elements)  # for debugging

    # Determine if we need to generate a new UUID. This minimizes the choppyness of the animation.
    if triggered_id in [None, id_constants.SIGNAL_VIRTUAL_NODE_UPDATE]:
        uuid = None
    else:
        uuid = utils.get_existing_uuid(state_elements)

    # Workaround for https://github.com/plotly/dash-cytoscape/issues/106
    # Give new ids to Cytoscape to avoid immutability of edges and parent relationships.
    elements = transformers.apply_uuid_to_elements(elements, this_uuid=uuid)
    elements = transformers.sort_nodes_by_parent_relationship(elements)
    return elements


@app.callback(
    Output(id_constants.CYTOSCAPE_GRAPH, "stylesheet"),
    Input(id_constants.SIGNAL_STYLE_UPDATE, "children"),
)
def update_cytoscape_stylesheet(style_update_signal):
    """Updates the cytoscape stylesheet.

    This function is called:
        when a style is updated.

    Args:
        style_update_signal: Signal indicating a style was updated.

    Returns:
        A dictionary encoding a cytoscape format stylesheet.
    """
    style_map = state.get_style_map()
    stylesheet = [
        *constants.BASE_CYTO_STYLESHEET,
        *converters.cytoscape_stylesheet_from_style_map(style_map),
    ]
    return stylesheet
