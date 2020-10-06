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
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import ALL, MATCH, Input, Output, State
from dash.exceptions import PreventUpdate
from graph_structures_pb2 import Node, NodeType, Status, VirtualNode

from . import (
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
        Input({constants.CLIENT_DATATABLE_ID: ALL},
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

    # print(triggered_id, triggered_prop, triggered_value)  # for debugging...

    if triggered_id == "virtual-node-update-signal" and triggered_value != constants.OK_SIGNAL:
        # No-op if the validation signal isn't OK
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

    status_override_components = [
        html.H3("Status"),
        dcc.Dropdown(
            id={"override-dropdown": "override-dropdown"},
            clearable=False,
            searchable=False,
            options=converters.override_dropdown_options_from_node(node),
            value=node.override_status)
    ]

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

    # We let the id fields be dictionaries here, to prevent Dash errors
    # when registering callbacks to dynamically created components.
    # Although we can directly assign an id and register a callback,
    # an error appears in the Dash app saying that no such ID exists.
    # The callback still works despite the error.
    # It can be supressed, but only at a global granularity (for all callbacks),
    # which seems too heavy handed.

    # Instead, we use the pattern matching callback feature to
    # match the dictionary fields in the id.
    # This is the same approach taken in update_graph_elements to
    # register the callback from the client datatable.

    # Notice that the value of the dictionary doesn't matter,
    # since we keep the key unique and match the value with ALL.
    # Unfortunately, we can't do something like id={"id": "component-unique-id"},
    # and match with Output/Input/State({"id": "component-unique-id"})
    # since the callback requires a wildcard (ALL/MATCH) to match.
    # We have to add an unused field, such as
    # id={"id": "component-unique-id", "index": 0} and match with
    # Output/Input/State({"id": "component-unique-id", "index": ALL/MATCH})
    # Neither solution is ideal, but have to work with it.

    comment_components = [
        dbc.Textarea(
            id={"node-comment-textarea": "node-comment-textarea"},
            value=node.comment,
        ),
        dbc.Button(
            id={"save-comment-textarea-button": "save-comment-textarea-button"},
            children="Save Comment",
        ),
        dbc.Button(
            id={
                "discard-comment-textarea-button":
                    "discard-comment-textarea-button"
            },
            children="Discard Comment Changes",
        ),
        dbc.Toast(
            id={"save-comment-toast": "save-comment-toast"},
            header="Successfully saved comment!",
            icon="success",
            duration=3000,
            dismissable=True,
            body_style={"display": "none"},
            is_open=False)
    ]

    return (
        [header] + status_override_components + sli_info + child_info +
        dependency_info + comment_components)


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
    Output({"save-comment-toast": MATCH},
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
    return True
