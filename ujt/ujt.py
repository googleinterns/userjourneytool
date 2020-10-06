""" Main entry point for UJT. """

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
import dash_table

from . import callbacks, constants, converters, state
from .dash_app import app, cache


def get_top_row_components():
    return html.Div(
        children=[
            dbc.Container(
                dbc.Row(
                    children=[
                        dbc.Col(
                            dbc.Button(
                                id="refresh-sli-button",
                                children="Refresh SLIs"),
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
                                                    placeholder=
                                                    "Virtual Node Name"),
                                            ],
                                            className="mr-3",
                                        ),
                                        dbc.Button(
                                            id="add-virtual-node-button",
                                            children="Add"),
                                        dbc.Button(
                                            id="delete-virtual-node-button",
                                            children="Delete"),
                                        dbc.Button(
                                            id="collapse-virtual-node-button",
                                            children="Collapse"),
                                        dbc.Button(
                                            id="expand-virtual-node-button",
                                            children="Expand"),
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
        stylesheet=constants.CYTO_STYLESHEET,
    )


def get_bottom_panels():
    return html.Div(
        children=[
            dbc.Container(
                dbc.Row(
                    children=[
                        dbc.Col(
                            [
                                html.H1("Tagging"),
                                html.Div(id="tagging-panel"),
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
                            ]),
                    ],
                ),
            ),
        ],
        className="mb-5",
    )


def get_layout():
    """ Generate the top-level layout for the Dash app.

    We place this function here (instead of dash_app.py) to enable to use of converters.py and state.py
    In dash_app.py, we run into circular dependency issues related to the cache object.

    Returns:
        a Dash HTML Div component containing the top-level layout for the app.
    """

    return html.Div(
        children=[
            html.H1(
                children="User Journey Tool",
                style={
                    "textAlign": "center",
                }),
            get_top_row_components(),
            get_cytoscape_graph(),
            get_bottom_panels(),
            dbc.Modal(
                children=[
                    dbc.ModalHeader("Error"),
                    dbc.ModalBody(id="collapse-error-modal-body"),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close",
                            id="collapse-error-modal-close",
                            className="ml-auto"),
                    ),
                ],
                id="collapse-error-modal",
            ),
            html.Div(
                id="virtual-node-update-signal",
                style={"display": "none"}),
        ],
    )


def initialize_ujt():
    if constants.CLEAR_CACHE_ON_STARTUP:
        cache.clear()
    # If first time running server, set these persisted properties as dicts
    map_names = [
        "virtual_node_map",
        "parent_virtual_node_map",
        "comment_map",
        "override_status_map"
    ]
    for map_name in map_names:
        if cache.get(map_name) is None:
            cache.set(map_name, {})

    # Request and cache the dependency topology from the reporting server
    state.get_message_maps()


if __name__ == "__main__":
    initialize_ujt()
    app.layout = get_layout()
    app.run_server(debug=True)
