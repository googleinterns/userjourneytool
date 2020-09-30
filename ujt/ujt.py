""" Main entry point for UJT. """

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
import dash_table

from . import callbacks, constants, converters, state
from .dash_app import app


def get_top_row_components():
    return html.Div(
        children=[
            dbc.Container(
                dbc.Row(
                    children=[
                        dbc.Col(
                            dbc.Button(id="refresh-button",
                                       children="Refresh"),
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


def get_bottom_info_panels():
    return html.Div(
        children=[
            dbc.Container(
                dbc.Row(
                    children=[
                        dbc.Col(
                            [
                                html.H1("Node Info"),
                                html.Div(
                                    id="node-info-panel",
                                    className="info-panel",
                                ),
                            ],
                        ),
                        dbc.Col(
                            [
                                html.H1("Client Info"),
                                dcc.Dropdown(
                                    id="client-dropdown",
                                    clearable=False,
                                    searchable=False,
                                    options=converters.
                                    dropdown_options_from_client_map(
                                        state.get_client_name_message_map())),
                                html.Div(
                                    id="client-info-panel",
                                    className="info-panel",
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
            get_bottom_info_panels(),
            html.Div(
                id="virtual-node-update-signal",
                style={"display": "none"}),
            dbc.Modal(
                children=[
                    dbc.ModalHeader("Error"),
                    dbc.ModalBody(id="collapse-error-modal-body"),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close",
                            id="collapse-error-modal-close",
                            className="ml-auto")),
                ],
                id="collapse-error-modal",
            ),
        ],
    )


if __name__ == "__main__":
    app.layout = get_layout()
    app.run_server(debug=True)
