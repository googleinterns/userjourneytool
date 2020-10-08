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

from typing import Any, Dict, List, Tuple, Union, Set

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import ALL, MATCH, Input, Output, State
from dash.exceptions import PreventUpdate
from graph_structures_pb2 import Node, NodeType, Status, VirtualNode, UserJourney

from . import (
    components,
    compute_status,
    constants,
    converters,
    rpc_client,
    state,
    transformers,
    utils)
from .dash_app import app


@app.callback(
    Output("cytoscape-graph",
           "elements"),
    [
        Input("refresh-sli-button",
              "n_clicks_timestamp"),
        Input({constants.USER_JOURNEY_DATATABLE_ID: ALL},
              "selected_row_ids"),
        Input("virtual-node-update-signal",
              "children"),
        Input("collapse-virtual-node-button",
              "n_clicks_timestamp"),
        Input("expand-virtual-node-button",
              "n_clicks_timestamp"),
        Input({"override-dropdown": ALL},
              "value"),
    ],
    [
        State("cytoscape-graph",
              "elements"),
        State("cytoscape-graph",
              "selectedNodeData"),
        State("virtual-node-input",
              "value"),
        State("cytoscape-graph",
              "tapNode"),
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
        # State
        state_elements: List[Dict[str,
                                  Any]],
        selected_node_data: List[Dict[str,
                                      Any]],
        virtual_node_input_value: str,
        tap_node: Dict[str,
                       Any]):
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
        override_dropdown_value: Status enum value of the status to override for the node.
        
        state_elements: The list of current cytoscape graph elements. This is unused and can be removed in a later change. 
        selected_node_data: The list of data dictionaries for selected nodes. Used to create virtual nodes.
        virtual_node_input_value: The value of the virtual node input box. Used to perform all virtual node operations. 
        tap_node: The cytoscape element of the latest tapped node. Used check which node to override the status of. 
    Returns:
        A dictionary of cytoscape elements describing the nodes and edges of the graph.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)
    #print(ctx.triggered)
    #print(triggered_id, triggered_prop, triggered_value)  # for debugging...

    if (triggered_id == "virtual-node-update-signal" and triggered_value != constants.OK_SIGNAL) or (triggered_id == r"""{"override-dropdown":"override-dropdown-hidden"}"""):
        # No-op if :
        #   the validation signal isn't OK
        #   callback fired from dummy override dropdown
        raise PreventUpdate

    node_name_message_map, client_name_message_map = state.get_message_maps()
    virtual_node_map = state.get_virtual_node_map()

    elements = state.get_cytoscape_elements()

    # This condition determines if we need to recompute node statuses.
    if triggered_id in [
            None,
            "refresh-sli-button",
            "virtual-node-update-signal",
            r"""{"override-dropdown":"override-dropdown"}"""  # Dash provides the value as a stringified dict
    ]:
        if triggered_id == "refresh-sli-button":
            state.clear_sli_cache(
            )  # in future, conditionally clear this based on timestamp
            sli_list = state.get_slis()
            node_name_message_map = transformers.apply_slis_to_node_map(
                sli_list,
                node_name_message_map)

        if triggered_id == r"""{"override-dropdown":"override-dropdown"}""":
            node_name = tap_node["data"]["ujt_id"]
            state.set_node_override_status(
                node_name,
                triggered_value,
                node_name_message_map=node_name_message_map,
                virtual_node_map=virtual_node_map)

        # Perform status computation.
        # We can refactor this block later as well, but no other function should call it...
        compute_status.reset_node_statuses(node_name_message_map)
        compute_status.reset_client_statuses(client_name_message_map)
        compute_status.reset_node_statuses(virtual_node_map)

        # combine the two maps of nodes into one dictionary
        # use duck typing -- is this pythonic or a hack?
        all_nodes_map = {
            **node_name_message_map,
            **virtual_node_map  # type: ignore
        }
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
    if user_journey_table_selected_row_ids in [[], [None]]:
        active_user_journey_name = None
    else:
        active_user_journey_name = user_journey_table_selected_row_ids[0][0]

    elements = transformers.apply_highlighted_edge_class_to_elements(
        elements,
        active_user_journey_name)

    transformers.apply_node_classes(
        elements,
        node_name_message_map,
        client_name_message_map,
        virtual_node_map,
    )

    # Determine if we need to generate a new UUID. This minimizes the choppyness of the animation.
    if triggered_id in [None, "virtual-node-update-signal"]:
        uuid = None
    else:
        uuid = utils.get_existing_uuid(state_elements)

    # Workaround for https://github.com/plotly/dash-cytoscape/issues/106
    # Give new ids to Cytoscape to avoid immutability of edges and parent relationships.
    elements = transformers.apply_uuid_to_elements(elements, this_uuid=uuid)
    return elements


@app.callback(
    Output("selected-info-panel",
           "children"),
    [Input("cytoscape-graph",
           "tapNode"),
    Input("cytoscape-graph", "tapEdge"),
    Input("applied-tag-update-signal", "children"),
    ],
    prevent_initial_call=True,
)
def generate_selected_info_panel(tap_node, tap_edge, applied_tag_update_signal) -> List[Any]:
    """ Generate the node info panel.

    This function is called:
        when a node is clicked
        when an edge is clicked

    Args:
        tap_node: Cytoscape element of the tapped/clicked node.
        tap_edge: Cytoscape element of the tapped/clicked edge.
        applied_tag_update_signal: The signal indicating that a tag was added or removed.

    Returns:
        a List of Dash components.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    latest_tapped_element = utils.get_latest_tapped_element(tap_node, tap_edge)
    ujt_id = latest_tapped_element["data"]["ujt_id"]

    out = []
    if latest_tapped_element == tap_node:
        node_name = tap_node["data"]["ujt_id"]
        if not utils.is_client_cytoscape_node(tap_node):
            out += components.get_node_info_panel_components(node_name)
    else:
        # just generate this header here for now,
        # probably don't need to make a new component function for it.
        source, target = ujt_id.split("/")
        header = html.P(f"Edge from {utils.relative_name(source)} to {utils.relative_name(target)}")
        out.append(header)

    out += components.get_apply_tag_components(ujt_id)

    return out

@app.callback(
    Output("user-journey-info-panel",
           "children"),
    Input("user-journey-dropdown",
           "value"),
    prevent_initial_call=True,
)
def generate_user_journey_info_panel(dropdown_value: str) -> List[Any]:
    """ Generate the client info panel.

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
        return converters.user_journey_datatable_from_user_journeys(client.user_journeys, constants.USER_JOURNEY_DATATABLE_ID)

    # associate the name of the user journey with the nodes that it passes through
    node_user_journey_map: Dict[str, List[UserJourney]] = state.get_node_to_user_journey_map()

    if dropdown_value in node_name_message_map:
        return converters.user_journey_datatable_from_user_journeys(node_user_journey_map[dropdown_value], constants.USER_JOURNEY_DATATABLE_ID)
    
    if dropdown_value in virtual_node_map:
        node_names_in_virtual_node = utils.get_all_node_names_within_virtual_node(dropdown_value, node_name_message_map, virtual_node_map)
        user_journeys = []
        for node_name in node_names_in_virtual_node:
            for user_journey in node_user_journey_map[node_name]:
                if user_journey not in user_journeys:  # this is sphagetti
                    user_journeys.append(user_journey)
                    
        return converters.user_journey_datatable_from_user_journeys(user_journeys, constants.USER_JOURNEY_DATATABLE_ID)


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
        if virtual_node_name in node_name_message_map or virtual_node_name in client_name_message_map:
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
    """ Closes and opens the error modal.

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

    if triggered_id == "collapse-error-modal-close":
        return False, ""

    if triggered_value != "OK":
        return True, triggered_value

    return False, ""


@app.callback(
    # We can't use ALL in the output, so we use MATCH.
    # However, since there's only one component with this key, the functionality is identical.
    Output({"node-comment-textarea": MATCH},
           "value"),
    Input({"discard-comment-textarea-button": ALL},
          "n_clicks_timestamp"),
    State("cytoscape-graph",
          "tapNode"),
    prevent_initial_call=True,
)
def discard_comment(discard_n_clicks_timestamp, tap_node):
    """ Handles the functionality for discarding comments.
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
    Output({"save-comment-toast": ALL}, 
           "is_open"),
    Input({"save-comment-textarea-button": ALL},
          "n_clicks_timestamp"),
    [
        State("cytoscape-graph",
              "tapNode"),
        State({"node-comment-textarea": ALL},
              "value"),
    ],
    prevent_initial_call=True,
)
def save_comment(save_n_clicks_timestamp, tap_node, new_comment):
    """ Handles the functionality for saving comments
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
    return [True]  # wrap in a list since we used pattern matching. should only ever be one toast.

@app.callback(
    Output("user-journey-dropdown", "options"),
    [Input("virtual-node-update-signal", "children")],
)
def update_user_journey_dropdown_options(virtual_node_update_signal):
    node_name_message_map, client_name_message_map = state.get_message_maps()
    virtual_node_map = state.get_virtual_node_map()

    return converters.dropdown_options_from_maps(node_name_message_map, client_name_message_map, virtual_node_map)


@app.callback(
    Output({"save-tag-toast": ALL}, "is_open"),
    Input({"save-tag-button": "save-tag-button", "index": ALL}, "n_clicks_timestamp"),
    State({"tag-input": "tag-input", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def save_tag(n_clicks_timestamp, input_values):
    """ Saves the corresponding tag from the input field to the tag list.
    
    Ideally, we would like to use the MATCH function to determine which button was clicked.
    However, since we only have one save tag toast for all the tags, we can't use MATCH in the Output field.
    To use MATCH, Dash requires the Output field to match the same properties as the input field.
    Refer to: https://dash.plotly.com/pattern-matching-callbacks

    This function is called:
        when the save tag button is clicked.

    Args:
        n_clicks_timestamp: List of the timestamps of when save-tag-button buttons were called.
            Value unused, input only provided to register callback.
        input_values: List of the input values in tag-input inputs.

    Returns:
        A boolean indicating whether the save tag successful toast should open.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    # Unfortunately, we have to convert the stringified dict back to a dict.
    # Dash doesn't provide us any other method to see which element triggered the callback.
    # This isn't very elegant, but I don't see any other way to proceed.
    id_dict = utils.string_to_dict(triggered_id)

    tag_idx = id_dict["index"]
    tag_value = input_values[tag_idx]

    if " " in tag_value:
        raise PreventUpdate  # TODO: display an error UI element or something

    state.update_tag(tag_idx, tag_value)
    return [True]  # since we pattern matched the save-tag-toast, we need to provide output as a list

@app.callback(
    Output("tag-update-signal", "children"),
    [
        Input({"delete-tag-button": "delete-tag-button", "index": ALL}, "n_clicks_timestamp"),
        Input({"create-tag-button": ALL}, "n_clicks_timestamp"),
    ],
    prevent_initial_call=True,
)
def create_delete_tag(remove_timestamps, add_timestamps):
    """ Handles creating and deleting tags from the tag list.

    This function is called:
        when the create tag button is clicked.
        while a delete tag button is clicked

    Args:
        remove_timestamps: List of the timestamps of when delete-tag-button buttons were called.
            Value unused, input only provided to register callback.
        add_timestamps: List of the timestamps of the create-tag-button buttons was called.
            Value unused, input only provided to register callback.

    Returns:
        A signal to add to the tag-update-signal hidden div.
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
    if "create-tag-button" in id_dict:
        state.create_tag("")
    elif "delete-tag-button" in id_dict:
        tag_idx = id_dict["index"]
        state.delete_tag(tag_idx)
    else:
        raise ValueError

    return constants.OK_SIGNAL

@app.callback(
    Output("tag-panel", "children"),
    Input("tag-update-signal", "children"),
)
def generate_tag_panel(tag_update_signal):
    """ Handles generating the tag creation and deletion panel.

    This function is called:
        when a new tag is created.
        when a tag is deleted.

    Args:
        tag-update-signal: Signal indicating that the list of tags was modified.
            Value unused, input only provided to register callback.
        
    Returns:
        A list of components to be placed in the tag-panel.
    """
    return components.get_tag_panel()


@app.callback(
    Output("applied-tag-update-signal", "children"),
    [
        Input({"remove-applied-tag-button": "remove-applied-tag-button", "index": ALL}, "n_clicks_timestamp"),
        Input({"add-applied-tag-button": ALL}, "n_clicks_timestamp"),
    ],
    [
        State("cytoscape-graph", "tapNode"),
        State("cytoscape-graph",
              "tapEdge"),
    ],
    prevent_initial_call=True,
)
def apply_empty_tag_remove_tag(remove_timestamps, add_timestamps, tap_node, tap_edge):
    """ Handles applying empty tags and removing tags from the tag map.

    This function is called:
        when the add tag button is clicked.
        while a delete tag button is clicked

    Args:
        remove_timestamps: List of the timestamps of when delete-applied-tag-button buttons were called.
            Value unused, input only provided to register callback.
        add_timestamps: List of the timestamps of the add-applied-tag-button buttons was called.
            Value unused, input only provided to register callback.
        tap_node: The last cytoscape node element that was tapped.
        tap_edge: The last cytoscape edge element that was tapped.
        
    Returns:
        A signal to add to the applied-tag-update-signal hidden div.
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

    if "add-applied-tag-button" in id_dict:
        state.add_tag_to_element(ujt_id, "")
    elif "remove-applied-tag-button" in id_dict:
        tag_idx = id_dict["index"]
        state.remove_tag_from_element(ujt_id, tag_idx)
    else:
        raise ValueError

    return constants.OK_SIGNAL

@app.callback(
    Output("update-applied-tag-dummy-signal", "children"),
    Input({"apply-tag-dropdown": "apply-tag-dropdown", "index": ALL}, "value"),
    [
        State("cytoscape-graph",
           "tapNode"),
        State("cytoscape-graph", "tapEdge"),
    ],
    prevent_initial_call=True,
)
def update_applied_tag(dropdown_values, tap_node, tap_edge):
    """ Updates the corresponding applied tag in the tag map.

    This function is called:
        when an apply-tag-dropdown value is updated

    Args:
        dropdown_values: the values of the apply-tag-dropdown dropdown menus.
        tap_node: Cytoscape element of the tapped/clicked node.
        tap_edge: Cytoscape element of the tapped/clicked edge.

    Returns:
        A boolean indicating whether the save tag successful toast should open.
    """
    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_value is None:
        raise PreventUpdate

    # Unfortunately, we have to convert the stringified dict back to a dict.
    # Dash doesn't provide us any other method to see which element triggered the callback.
    # This isn't very elegant, but I don't see any other way to proceed.
    id_dict = utils.string_to_dict(triggered_id)

    tag_idx = id_dict["index"]
    tag_value = dropdown_values[tag_idx]

    latest_tapped_element = utils.get_latest_tapped_element(tap_node, tap_edge)
    ujt_id = latest_tapped_element["data"]["ujt_id"]

    state.update_applied_tag(ujt_id, tag_idx, tag_value)
