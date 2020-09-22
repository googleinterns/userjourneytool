""" Main entry point for UJT. """

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
import dash_table

from . import callbacks, constants, converters, state
from .dash_app import app


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
            cyto.Cytoscape(
                id="cytoscape-graph",
                layout={
                    "name": "dagre",
                    "nodeDimensionsIncludeLabels": "true",
                },
                style={
                    "width": constants.GRAPH_WIDTH,
                    "height": constants.GRAPH_HEIGHT,
                    "backgroundColor": constants.GRAPH_BACKGROUND_COLOR,
                },
                stylesheet=constants.CYTO_STYLESHEET,
            ),
            dbc.Button(id="refresh-button",
                       children="Refresh"),
            html.Div(
                children=[
                    dbc.Container(
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H1("Node Info"),
                                        html.Div(
                                            id="node-info-panel",
                                            className="info-panel"),
                                    ]),
                                dbc.Col(
                                    [
                                        html.H1("Client Info"),
                                        dcc.Dropdown(
                                            id="client-dropdown",
                                            clearable=False,
                                            searchable=False,
                                            options=converters.
                                            dropdown_options_from_client_map(
                                                state.
                                                get_client_name_message_map())),
                                        html.Div(
                                            id="client-info-panel",
                                            className="info-panel",
                                        ),
                                    ]),
                            ])),
                ],
                className="mb-5"),
        ],
    )


if __name__ == "__main__":
    app.layout = get_layout()
    app.run_server(debug=True)
