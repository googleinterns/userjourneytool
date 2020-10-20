import dash
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_bootstrap_components as dbc

from .. import constants, converters, id_constants, state, utils
from ..dash_app import app


@app.callback(
    Output(id_constants.TIME_SELECT_PANEL, "children"),
    Input(id_constants.CHANGE_OVER_TIME_TAG_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def update_time_select_panel(tag):
    """Updates the time select panel.

    The time select panel displays two input boxes to input start
    and end time if custom range is selected.
    Otherwise (a timestamped tag is selected), it displays one input
    to input the window size before and after the timestamp.

    Alternatively, we could declare all three input boxes in components,
    and use this callback to change their visibility.
    This allows us to avoid pattern matching, but is inconsistent with
    other parts of our application.

    This function is called:
        when the CHANGE_OVER_TIME_TAG_DROPDOWN value is updated 

    Args:
        tag: Dropdown value in the CHANGE_OVER_TIME_TAG_DROPDOWN.

    Returns:
        A list of components for the TIME_SELECT_PANEL.
    """

    if tag == constants.CUSTOM_TIME_RANGE_DROPDOWN_VALUE:
        return [
            html.Div("Start Time"),
            dbc.Input(
                id=id_constants.START_TIME_INPUT,
                placeholder=constants.DATE_FORMAT,
            ),
            html.Div("End Time"),
            dbc.Input(
                id=id_constants.END_TIME_INPUT,
                placeholder=constants.DATE_FORMAT,
            ),
        ]
    else:
        return [
            html.Div("Window Size"),
            dbc.Input(
                id=id_constants.WINDOW_SIZE_INPUT,
                placeholder="hours",
            ),
        ]
