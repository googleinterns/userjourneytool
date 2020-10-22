import datetime as dt
from typing import List, Optional

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import ALL, Input, Output, State

from .. import constants, id_constants, utils
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
                id={id_constants.START_TIME_INPUT: id_constants.START_TIME_INPUT},
                placeholder=constants.DATE_FORMAT,
            ),
            html.Div("End Time"),
            dbc.Input(
                id={id_constants.END_TIME_INPUT: id_constants.END_TIME_INPUT},
                placeholder=constants.DATE_FORMAT,
            ),
        ]
    else:
        return [
            html.Div("Window Size"),
            dbc.Input(
                id={id_constants.WINDOW_SIZE_INPUT: id_constants.WINDOW_SIZE_INPUT},
                placeholder="hours",
            ),
        ]


@app.callback(
    Output(id_constants.TIME_RANGE_STORE, "data"),
    [
        Input(id_constants.CHANGE_OVER_TIME_QUERY_BUTTON, "n_clicks_timestamp"),
        Input(id_constants.CHANGE_OVER_TIME_RESET_BUTTON, "n_clicks_timestamp"),
    ],
    [
        State({id_constants.START_TIME_INPUT: ALL}, "value"),
        State({id_constants.END_TIME_INPUT: ALL}, "value"),
        State({id_constants.WINDOW_SIZE_INPUT: ALL}, "value"),
        State(id_constants.CHANGE_OVER_TIME_TAG_DROPDOWN, "value"),
    ],
    prevent_initial_call=True,
)
def update_time_range_store(
    query_n_clicks_timestamp: Optional[int],
    reset_n_clicks_timestamp: Optional[int],
    start_time_input_values: List[str],
    end_time_input_values: List[str],
    window_size_input_values: List[str],
    tag_selection: str,
):
    """Updates the TIME_RANGE_STORE with the selected time range.

    The TIME_RANGE_STORE acts like a signal, updating whenever the Query or Reset button is clicked.
    We choose to store the time range in this store in order to isolate the input parsing functionality here.
    This allows users of the store (namely, update_graph_elements) to avoid having to deal with the
    separate cases of custom time range and window size input.
    Since the SLI Type dropdown doesn't require parsing, update_graph_elements can directly read it as state.

    This function is called:
        when the CHANGE_OVER_TIME_QUERY_BUTTON is clicked
        when the CHANGE_OVER_TIME_RESET_BUTTON is clicked

    Args:
        query_n_clicks_timestamp: Timestamp of when the CHANGE_OVER_TIME_QUERY_BUTTON was clicked
        reset_n_clicks_timestamp: Timestamp of when the CHANGE_OVER_TIME_RESET_BUTTON was clicked
        start_time_input_values: List of values from the START_TIME_INPUT box. Should contain only one value.
        end_time_input_values: List of values from the END_TIME_INPUT box. Should contain only one value.
        window_size_input_values: List of values from the WINDOW_SIZE_INPUT box. Should contain only one value.
        tag_selection: The value from the CHANGE_OVER_TIME_TAG_DROPDOWN. Should be CUSTOM_TIME_RANGE_DROPDOWN_VALUE or a timestamped tag.

    Returns:
        A dictionary to be placed in the TIME_RANGE_STORE.
        The dictionary has keys "start_timestamp" and "end_timestamp", which map
        to the POSIX timestamps of their respective times.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_id == id_constants.CHANGE_OVER_TIME_RESET_BUTTON:
        return {}

    # TODO: improve this parsing -- hard to context switch to write robust parsing right now
    # need to write the callbacks - data flow first
    # make an error toast
    if tag_selection == constants.CUSTOM_TIME_RANGE_DROPDOWN_VALUE:
        start_time = dt.datetime.strptime(
            start_time_input_values[0], constants.DATE_FORMAT_STRING
        )
        end_time = dt.datetime.strptime(
            end_time_input_values[0], constants.DATE_FORMAT_STRING
        )
    else:
        # TODO: fix this
        window_size_timedelta = dt.timedelta(minutes=float(window_size_input_values[0]))
        tag_timestamp_string = tag_selection.split("@")[-1]
        tag_timestamp = dt.datetime.strptime(
            tag_timestamp_string, constants.DATE_FORMAT_STRING
        )
        start_time = tag_timestamp - window_size_timedelta
        end_time = tag_timestamp + window_size_timedelta

    # Dash somehow serializes the objects placed into Stores, but it's not specified
    # in the documentation how it does so.
    # It makes it confusing when we try to store datetime objects directly, so
    # we choose to store their timestamps for a clearer interface.
    return {
        "start_timestamp": start_time.timestamp(),
        "end_timestamp": end_time.timestamp(),
    }
