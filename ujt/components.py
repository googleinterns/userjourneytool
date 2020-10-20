""" Generates components for use in the frontend. 

In general, these functions usually produce a list of components (e.g. selected panel),
 or a single toplevel component (e.g. the cytoscape graph). 

This is in contrast to converters, which generally produce 
a single component to be nested within an wrapping component,
or an intermediate data structure (e.g. a list of dropdown options).

Admittedly, this line is blurry, but it's nice to have a separate module to contain some higher
level functions to generate components, rather than placing them in ujt or callbacks.
"""

from typing import List, Union

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
import dash_table
from graph_structures_pb2 import Node, NodeType, VirtualNode

from . import callbacks, constants, converters, state, utils


def get_layout():
    """Generate the top-level layout for the Dash app.

    Returns:
        a Dash HTML Div component containing the top-level layout for the app.
    """

    return html.Div(
        children=[
            html.H1(
                children="User Journey Tool",
                style={
                    "textAlign": "center",
                },
            ),
            get_top_row_components(),
            get_cytoscape_graph(),
            get_bottom_panel_components(),
            dbc.Modal(
                children=[
                    dbc.ModalHeader("Error"),
                    dbc.ModalBody(id="collapse-error-modal-body"),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close",
                            id="collapse-error-modal-close",
                            className="ml-auto",
                        ),
                    ),
                ],
                id="collapse-error-modal",
            ),
            get_signals(),
        ],
    )


def get_signals():
    signal_ids = [
        "virtual-node-update-signal",
        # ---
        "create-tag-signal",
        "delete-tag-signal",
        "save-tag-signal",
        "tag-update-signal",
        # ---
        "add-applied-tag-signal",
        "remove-applied-tag-signal",
        "modify-applied-tag-signal",
        "applied-tag-update-signal",
        # ---
        "create-view-signal",
        "delete-view-signal",
        "modify-view-signal",
        "view-update-signal",
        # ---
        "save-style-signal",
        "delete-style-signal",
        "style-update-signal",
        # ---
        "composite-tagging-update-signal",
    ]

    signals = [
        html.Div(
            id=signal_id,
            style={"display": "none"},
        )
        for signal_id in signal_ids
    ]

    return html.Div(id="signal-wrapper-div", children=signals)


def get_top_row_components():
    return html.Div(
        children=[
            dbc.Container(
                dbc.Row(
                    children=[
                        dbc.Col(
                            dbc.Button(
                                id="refresh-sli-button", children="Refresh SLIs"
                            ),
                        ),
                        dbc.Col(
                            children=[
                                dbc.Form(
                                    children=[
                                        dbc.FormGroup(
                                            children=[
                                                dbc.Input(
                                                    id="virtual-node-input",
                                                    type="text",
                                                    placeholder="Virtual Node Name",
                                                ),
                                            ],
                                            className="mr-3",
                                        ),
                                        dbc.Button(
                                            id="add-virtual-node-button", children="Add"
                                        ),
                                        dbc.Button(
                                            id="delete-virtual-node-button",
                                            children="Delete",
                                        ),
                                        dbc.Button(
                                            id="collapse-virtual-node-button",
                                            children="Collapse",
                                        ),
                                        dbc.Button(
                                            id="expand-virtual-node-button",
                                            children="Expand",
                                        ),
                                    ],
                                    inline=False,
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )


def get_cytoscape_graph():
    return cyto.Cytoscape(
        id="cytoscape-graph",
        layout={
            "name": "dagre",
            "nodeDimensionsIncludeLabels": "true",
            "animate": "true",
        },
        style={
            "width": constants.GRAPH_WIDTH,
            "height": constants.GRAPH_HEIGHT,
            "backgroundColor": constants.GRAPH_BACKGROUND_COLOR,
        },
        # stylesheet=*constants.DEF
    )


def get_bottom_panel_components():
    return html.Div(
        children=[
            dbc.Container(
                dbc.Row(
                    children=[
                        dbc.Col(
                            [
                                html.H1("Tagging"),
                                html.Div(
                                    id="create-tag-panel",
                                ),
                                html.Div(
                                    id="view-panel",
                                ),
                                html.Div(
                                    id="style-panel",
                                    children=get_create_style_components(),
                                ),
                            ],
                        ),
                        dbc.Col(
                            [
                                html.H1("Selected Info"),
                                html.Div(
                                    id="selected-info-panel",
                                ),
                            ],
                        ),
                        dbc.Col(
                            [
                                html.H1("User Journey Info"),
                                dcc.Dropdown(
                                    id="user-journey-dropdown",
                                    clearable=False,
                                    searchable=False,
                                ),
                                html.Div(
                                    id="user-journey-info-panel",
                                ),
                            ]
                        ),
                    ],
                ),
                fluid=True,
            ),
        ],
        className="mb-5",  # add margin to bottom
    )


def get_node_info_panel_components(node_name):
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
            value=node.override_status,
        ),
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
                table_id=constants.CHILD_DATATABLE_ID,
            ),
        ]

    # Although we generally prefer "asking forgiveness rather than permission" (try/except) rather than
    # "look before you leap", we avoid having an empty except block by checking the is_virtual_node_property.
    if not is_virtual_node and node.slis:  # type: ignore
        sli_info = [
            html.H3("SLI Info"),
            converters.datatable_from_slis(
                node.slis, table_id=constants.SLI_DATATABLE_ID  # type: ignore
            ),
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
                table_id=constants.DEPENDENCY_DATATABLE_ID,
            ),
        ]

    comment_components = get_comment_components(initial_value=node.comment)

    return (
        [header]
        + status_override_components
        + sli_info
        + child_info
        + dependency_info
        + comment_components
    )


def get_comment_components(initial_value=""):
    """Generates a list of components for use in comment related interactions.

    We let the id fields be dictionaries here, to prevent Dash errors
    when registering callbacks to dynamically created components.
    Although we can directly assign an id and register a callback,
    an error appears in the Dash app saying that no such ID exists.
    The callback still works despite the error.
    It can be supressed, but only at a global granularity (for all callbacks),
    which seems too heavy handed.

    Instead, we use the pattern matching callback feature to
    match the dictionary fields in the id.
    This is the same approach taken in update_graph_elements to
    register the callback from the client datatable.

    Notice that the value of the dictionary doesn't matter,
    since we keep the key unique and match the value with ALL.
    Unfortunately, we can't do something like id={"id": "component-unique-id"},
    and match with Output/Input/State({"id": "component-unique-id"})
    since the callback requires a wildcard (ALL/MATCH) to match.
    We have to add an unused field, such as
    id={"id": "component-unique-id", "index": 0} and match with
    Output/Input/State({"id": "component-unique-id", "index": ALL/MATCH})
    Neither solution is ideal, but have to work with it.

    Returns:
        A list of Dash components.
    """

    comment_components = [
        html.H3("Comments"),
        dbc.Textarea(
            id={"node-comment-textarea": "node-comment-textarea"},
            value=initial_value,
        ),
        dbc.Button(
            id={"save-comment-textarea-button": "save-comment-textarea-button"},
            children="Save Comment",
        ),
        dbc.Button(
            id={"discard-comment-textarea-button": "discard-comment-textarea-button"},
            children="Discard Comment Changes",
        ),
        dbc.Toast(
            id={"save-comment-toast": "save-comment-toast"},
            header="Successfully saved comment!",
            icon="success",
            duration=3000,
            dismissable=True,
            body_style={"display": "none"},
            is_open=False,
        ),
    ]
    return comment_components


def get_apply_tag_components(ujt_id):
    tag_map = state.get_tag_map()
    tag_list = state.get_tag_list()

    out = [html.H2("Tagging")]
    for idx, tag in enumerate(tag_map[ujt_id]):
        out += [
            dbc.Row(
                children=[
                    dbc.Col(
                        children=dcc.Dropdown(
                            id={
                                "apply-tag-dropdown": "apply-tag-dropdown",
                                "index": idx,
                            },
                            options=converters.tag_dropdown_options_from_tags(tag_list),
                            value=tag,
                        ),
                        width=10,
                        className="m-1",
                    ),
                    dbc.Col(
                        children=dbc.Button(
                            children="x",
                            id={
                                "remove-applied-tag-button": "remove-applied-tag-button",
                                "index": idx,
                            },
                        ),
                        width="auto",
                        className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
                    ),
                ],
                no_gutters=True,
                justify="end",
            ),
        ]

    add_button_row = dbc.Row(
        children=[
            dbc.Col(
                children=dbc.Button(
                    children="+",
                    id={"add-applied-tag-button": "add-applied-tag-button"},
                ),
                width="auto",
                className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
            ),
        ],
        no_gutters=True,
        justify="end",
    )

    # This is a pretty bad hack.
    # The update_graph_elements callback is called (via pattern matching)
    # when the override-dropdown component is removed (a node was previously selected, then a client/edge was selected).
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
        id={"override-dropdown": "override-dropdown-hidden"},
        style={"display": "none"},
    )

    return out + [add_button_row, dummy_override_dropdown]


def get_create_tag_components():
    tag_list = state.get_tag_list()

    tag_rows = []
    for idx, tag in enumerate(tag_list):
        tag_rows += [
            dbc.Row(
                children=[
                    dbc.Col(
                        children=dbc.Input(
                            id={"tag-input": "tag-input", "index": idx},
                            placeholder="Tag name",
                            value=tag,
                        ),
                        width=9,
                        className="m-1",  # margin around all sides https://getbootstrap.com/docs/4.0/utilities/spacing/
                    ),
                    dbc.Col(
                        children=dbc.Button(
                            children="x",
                            id={"delete-tag-button": "delete-tag-button", "index": idx},
                        ),
                        width="auto",
                        className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
                    ),
                    dbc.Col(
                        children=dbc.Button(
                            children="\N{CHECK MARK}",
                            id={"save-tag-button": "save-tag-button", "index": idx},
                        ),
                        width="auto",
                        className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
                    ),
                ],
                no_gutters=True,
                justify="end",  # right justify to make it easier to line up the add button row
            ),
        ]

    add_button_row = dbc.Row(
        children=[
            dbc.Col(
                children=dbc.Button(
                    children="+",
                    id={"create-tag-button": "create-tag-button"},
                ),
                width="auto",
                className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
            ),
        ],
        no_gutters=True,
        justify="end",
    )

    save_tag_toast = dbc.Toast(
        id={"save-tag-toast": "save-tag-toast"},
        header="Successfully saved tag!",
        icon="success",
        duration=3000,
        dismissable=True,
        body_style={"display": "none"},
        is_open=False,
    )

    header = html.H2("Tags")

    return [header] + tag_rows + [add_button_row, save_tag_toast]


def get_view_components():
    tag_list = state.get_tag_list()
    style_map = state.get_style_map()
    view_list = state.get_view_list()

    view_rows = []
    for idx, view_tuple in enumerate(view_list):
        view_rows += [
            dbc.Row(
                children=[
                    dbc.Col(
                        children=dcc.Dropdown(
                            id={"view-tag-dropdown": "view-tag-dropdown", "index": idx},
                            options=converters.tag_dropdown_options_from_tags(tag_list),
                            value=view_tuple[0],
                        ),
                        width=5,
                        className="m-1",
                    ),
                    dbc.Col(
                        children=dcc.Dropdown(
                            id={
                                "view-style-dropdown": "view-style-dropdown",
                                "index": idx,
                            },
                            options=converters.style_dropdown_options_from_styles(
                                style_map
                            ),
                            value=view_tuple[1],
                        ),
                        width=5,
                        className="m-1",
                    ),
                    dbc.Col(
                        children=dbc.Button(
                            children="x",
                            id={
                                "delete-view-button": "delete-view-button",
                                "index": idx,
                            },
                        ),
                        width="auto",
                        className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
                    ),
                ],
                no_gutters=True,
                justify="end",  # right justify to make it easier to line up the add button row
            ),
        ]

    add_button_row = dbc.Row(
        children=[
            dbc.Col(
                children=dbc.Button(
                    children="+",
                    id={"create-view-button": "create-view-button"},
                ),
                width="auto",
                className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
            ),
        ],
        no_gutters=True,
        justify="end",
    )

    header = html.H3("Views")

    return [header] + view_rows + [add_button_row]


def get_create_style_components():
    style_components = [
        html.H3("Styles"),
        html.A(
            children="Style Reference",
            href="https://js.cytoscape.org/#style",
            target="_blank",
        ),
        dbc.Input(
            id="style-name-input",
            type="text",
            placeholder="Style Name",
        ),
        dbc.Textarea(id="style-textarea"),
        dbc.Button(
            id="load-style-textarea-button",
            children="Load Style",
        ),
        dbc.Button(
            id="save-style-textarea-button",
            children="Save Style",
        ),
        dbc.Button(
            id="delete-style-button",
            children="Delete Style",
        ),
        dbc.Toast(
            id="save-style-toast",
            duration=3000,
            dismissable=True,
            body_style={"display": "none"},
            is_open=False,
        ),
    ]
    return style_components
