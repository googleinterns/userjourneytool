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
from graph_structures_pb2 import Node, NodeType, VirtualNode

from . import constants, converters, id_constants, state, utils


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
                    dbc.ModalBody(id=id_constants.COLLAPSE_ERROR_MODAL_BODY),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close",
                            id=id_constants.COLLAPSE_ERROR_MODAL_CLOSE,
                            className="ml-auto",
                        ),
                    ),
                ],
                id=id_constants.COLLAPSE_ERROR_MODAL,
            ),
            get_signals(),
        ],
    )


def get_signals():
    signal_ids = [
        id_constants.SIGNAL_VIRTUAL_NODE_UPDATE,
        # ---
        id_constants.SIGNAL_TAG_CREATE,
        id_constants.SIGNAL_TAG_DELETE,
        id_constants.SIGNAL_TAG_SAVE,
        id_constants.SIGNAL_TAG_UPDATE,
        # ---
        id_constants.SIGNAL_APPLIED_TAG_ADD,
        id_constants.SIGNAL_APPLIED_TAG_REMOVE,
        id_constants.SIGNAL_APPLIED_TAG_MODIFY,
        id_constants.SIGNAL_APPLIED_TAG_UPDATE,
        # ---
        id_constants.SIGNAL_VIEW_CREATE,
        id_constants.SIGNAL_VIEW_DELETE,
        id_constants.SIGNAL_VIEW_MODIFY,
        id_constants.SIGNAL_VIEW_UPDATE,
        # ---
        id_constants.SIGNAL_STYLE_SAVE,
        id_constants.SIGNAL_STYLE_DELETE,
        id_constants.SIGNAL_STYLE_UPDATE,
        # ---
        id_constants.SIGNAL_COMPOSITE_TAGGING_UPDATE,
    ]

    signals = [
        html.Div(
            id=signal_id,
            style={"display": "none"},
        )
        for signal_id in signal_ids
    ]

    return html.Div(id=id_constants.SIGNAL_WRAPPER_DIV, children=signals)


def get_top_row_components():
    return html.Div(
        children=[
            dbc.Container(
                dbc.Row(
                    children=[
                        dbc.Col(
                            dbc.Button(
                                id=id_constants.REFRESH_SLI_BUTTON,
                                children="Refresh SLIs",
                            ),
                        ),
                        dbc.Col(
                            children=get_virtual_node_control_components()
                        ),
                        dbc.Col(
                            children=get_batch_apply_tag_components()
                        )
                    ],
                ),
            ),
        ],
    )

def get_virtual_node_control_components():
    components = [
        dbc.Input(
            id=id_constants.VIRTUAL_NODE_INPUT,
            type="text",
            placeholder="Virtual Node Name",
        ),
        dbc.Button(
            id=id_constants.ADD_VIRTUAL_NODE_BUTTON,
            children="Add",
        ),
        dbc.Button(
            id=id_constants.DELETE_VIRTUAL_NODE_BUTTON,
            children="Delete",
        ),
        dbc.Button(
            id=id_constants.COLLAPSE_VIRTUAL_NODE_BUTTON,
            children="Collapse",
        ),
        dbc.Button(
            id=id_constants.EXPAND_VIRTUAL_NODE_BUTTON,
            children="Expand",
        ),
    ]
    return components

def get_batch_apply_tag_components():
    components = [
        dcc.Dropdown(
            id=id_constants.BATCH_APPLIED_TAG_DROPDOWN,
        ),
        dbc.Button(
            id=id_constants.BATCH_ADD_APPLIED_TAG_BUTTON,
            children="Add Tags to Selected"
        ),
        dbc.Button(
            id=id_constants.BATCH_REMOVE_APPLIED_TAG_BUTTON,
            children="Remove Tags from Selected"
        ),
    ]
    return components

def get_cytoscape_graph():
    return cyto.Cytoscape(
        id=id_constants.CYTOSCAPE_GRAPH,
        layout=constants.CYTO_LAYOUT,
        style=constants.CYTO_STYLE,
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
                                    id=id_constants.CREATE_TAG_PANEL,
                                ),
                                html.Div(
                                    id=id_constants.VIEW_PANEL,
                                ),
                                html.Div(
                                    id=id_constants.STYLE_PANEL,
                                    children=get_create_style_components(),
                                ),
                            ],
                        ),
                        dbc.Col(
                            [
                                html.H1("Selected Info"),
                                html.Div(
                                    id=id_constants.SELECTED_INFO_PANEL,
                                ),
                            ],
                        ),
                        dbc.Col(
                            [
                                html.H1("User Journey Info"),
                                dcc.Dropdown(
                                    id=id_constants.USER_JOURNEY_DROPDOWN,
                                    clearable=False,
                                    searchable=False,
                                ),
                                html.Div(
                                    id=id_constants.USER_JOURNEY_INFO_PANEL,
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
            id={id_constants.OVERRIDE_DROPDOWN: id_constants.OVERRIDE_DROPDOWN},
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
                table_id=id_constants.CHILD_DATATABLE,
            ),
        ]

    # Although we generally prefer "asking forgiveness rather than permission" (try/except) rather than
    # "look before you leap", we avoid having an empty except block by checking the is_virtual_node_property.
    if not is_virtual_node and node.slis:  # type: ignore
        sli_info = [
            html.H3("SLI Info"),
            converters.datatable_from_slis(
                node.slis, table_id=id_constants.SLI_DATATABLE  # type: ignore
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
                table_id=id_constants.DEPENDENCY_DATATABLE,
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
            id={id_constants.NODE_COMMENT_TEXTAREA: id_constants.NODE_COMMENT_TEXTAREA},
            value=initial_value,
        ),
        dbc.Button(
            id={
                id_constants.SAVE_COMMENT_TEXTAREA_BUTTON: id_constants.SAVE_COMMENT_TEXTAREA_BUTTON
            },
            children="Save Comment",
        ),
        dbc.Button(
            id={
                id_constants.DISCARD_COMMENT_TEXTAREA_BUTTON: id_constants.DISCARD_COMMENT_TEXTAREA_BUTTON
            },
            children="Discard Comment Changes",
        ),
        dbc.Toast(
            id={id_constants.SAVE_COMMENT_TOAST: id_constants.SAVE_COMMENT_TOAST},
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
                                id_constants.APPLIED_TAG_DROPDOWN: id_constants.APPLIED_TAG_DROPDOWN,
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
                                id_constants.REMOVE_APPLIED_TAG_BUTTON: id_constants.REMOVE_APPLIED_TAG_BUTTON,
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
                    id={
                        id_constants.ADD_APPLIED_TAG_BUTTON: id_constants.ADD_APPLIED_TAG_BUTTON
                    },
                ),
                width="auto",
                className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
            ),
        ],
        no_gutters=True,
        justify="end",
    )

    return out + [add_button_row]


def get_create_tag_components():
    tag_list = state.get_tag_list()

    tag_rows = []
    for idx, tag in enumerate(tag_list):
        tag_rows += [
            dbc.Row(
                children=[
                    dbc.Col(
                        children=dbc.Input(
                            id={
                                id_constants.TAG_INPUT: id_constants.TAG_INPUT,
                                "index": idx,
                            },
                            placeholder="Tag name",
                            value=tag,
                        ),
                        width=9,
                        className="m-1",  # margin around all sides https://getbootstrap.com/docs/4.0/utilities/spacing/
                    ),
                    dbc.Col(
                        children=dbc.Button(
                            children="x",
                            id={
                                id_constants.DELETE_TAG_BUTTON: id_constants.DELETE_TAG_BUTTON,
                                "index": idx,
                            },
                        ),
                        width="auto",
                        className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
                    ),
                    dbc.Col(
                        children=dbc.Button(
                            children="\N{CHECK MARK}",
                            id={
                                id_constants.SAVE_TAG_BUTTON: id_constants.SAVE_TAG_BUTTON,
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
                    id={id_constants.CREATE_TAG_BUTTON: id_constants.CREATE_TAG_BUTTON},
                ),
                width="auto",
                className=constants.BOOTSTRAP_BUTTON_COLUMN_CLASSES,
            ),
        ],
        no_gutters=True,
        justify="end",
    )

    save_tag_toast = dbc.Toast(
        id={id_constants.SAVE_TAG_TOAST: id_constants.SAVE_TAG_TOAST},
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
                            id={
                                id_constants.VIEW_TAG_DROPDOWN: id_constants.VIEW_TAG_DROPDOWN,
                                "index": idx,
                            },
                            options=converters.tag_dropdown_options_from_tags(tag_list),
                            value=view_tuple[0],
                        ),
                        width=5,
                        className="m-1",
                    ),
                    dbc.Col(
                        children=dcc.Dropdown(
                            id={
                                id_constants.VIEW_STYLE_DROPDOWN: id_constants.VIEW_STYLE_DROPDOWN,
                                "index": idx,
                            },
                            options=converters.style_dropdown_options_from_style_names(
                                style_map.keys()
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
                                id_constants.DELETE_VIEW_BUTTON: id_constants.DELETE_VIEW_BUTTON,
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
                    id={
                        id_constants.CREATE_VIEW_BUTTON: id_constants.CREATE_VIEW_BUTTON
                    },
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
            id=id_constants.STYLE_NAME_INPUT,
            type="text",
            placeholder="Style Name",
        ),
        dbc.Textarea(id=id_constants.STYLE_TEXTAREA),
        dbc.Button(
            id=id_constants.LOAD_STYLE_TEXTAREA_BUTTON,
            children="Load Style",
        ),
        dbc.Button(
            id=id_constants.SAVE_STYLE_TEXTAREA_BUTTON,
            children="Save Style",
        ),
        dbc.Button(
            id=id_constants.DELETE_STYLE_BUTTON,
            children="Delete Style",
        ),
        dbc.Toast(
            id=id_constants.SAVE_STYLE_TOAST,
            duration=3000,
            dismissable=True,
            body_style={"display": "none"},
            is_open=False,
        ),
    ]
    return style_components
