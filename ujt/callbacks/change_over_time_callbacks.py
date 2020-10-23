import datetime as dt
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import google.protobuf.json_format as json_format
from dash.dependencies import ALL, Input, Output, State
from graph_structures_pb2 import SLI

from .. import constants, converters, id_constants, rpc_client, transformers, utils
from ..dash_app import app

if TYPE_CHECKING:
    from graph_structures_pb2 import (
        SLITypeValue,  # pylint: disable=no-name-in-module  # pragma: no cover
    )


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
                placeholder=constants.WINDOW_SIZE_FORMAT,
            ),
        ]


@app.callback(
    [
        Output(id_constants.CHANGE_OVER_TIME_SLI_STORE, "data"),
        Output(id_constants.CHANGE_OVER_TIME_ERROR_TOAST, "is_open"),
        Output(id_constants.CHANGE_OVER_TIME_ERROR_TOAST, "header"),
    ],
    [
        Input(id_constants.CHANGE_OVER_TIME_QUERY_BUTTON, "n_clicks_timestamp"),
        Input(id_constants.CHANGE_OVER_TIME_RESET_BUTTON, "n_clicks_timestamp"),
    ],
    [
        State({id_constants.START_TIME_INPUT: ALL}, "value"),
        State({id_constants.END_TIME_INPUT: ALL}, "value"),
        State({id_constants.WINDOW_SIZE_INPUT: ALL}, "value"),
        State(id_constants.CHANGE_OVER_TIME_TAG_DROPDOWN, "value"),
        State(id_constants.CHANGE_OVER_TIME_SLI_TYPE_DROPDOWN, "value"),
    ],
    prevent_initial_call=True,
)
def update_change_over_time_sli_store(
    query_n_clicks_timestamp: Optional[int],
    reset_n_clicks_timestamp: Optional[int],
    start_time_input_values: List[str],
    end_time_input_values: List[str],
    window_size_input_values: List[str],
    tag_selection: str,
    sli_type: Optional["SLITypeValue"],
):
    """Updates the CHANGE_OVER_TIME_SLI_STORE with the selected time range.

    The CHANGE_OVER_TIME_SLI_STORE acts like a signal, updating whenever the Query or Reset button is clicked.
    We choose to store the time range in this store in order to isolate the input parsing functionality here.
    This allows users of the store (namely, update_graph_elements) to avoid having to deal with the
    separate cases of custom time range and window size input.

    Notice we also validate the SLI type dropdown here as well.

    Finally, this callback makes the RPC to the reporting server to get SLIs for the time range.
    This approach avoids making repeated RPC calls if multiple components need to update based on the SLI data,
    namely, the cytoscape graph and the CHANGE_OVER_TIME_TEXT_OUTPUT_PANEL.

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
        sli_type; The value from the CHANGE_OVER_TIME_SLI_TYPE_DROPDOWN. Used for input validation.

    Returns:
        A dictionary to be placed in the CHANGE_OVER_TIME_SLI_STORE.
        The dictionary has keys "start_timestamp" and "end_timestamp", which map
        to the POSIX timestamps of their respective times.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_id == id_constants.CHANGE_OVER_TIME_RESET_BUTTON:
        return [{}, dash.no_update, dash.no_update]

    if sli_type is None:
        return [dash.no_update, True, "Please select a SLI type."]

    try:
        if tag_selection == constants.CUSTOM_TIME_RANGE_DROPDOWN_VALUE:
            start_time = dt.datetime.strptime(
                start_time_input_values[0], constants.DATE_FORMAT_STRING
            )
            end_time = dt.datetime.strptime(
                end_time_input_values[0], constants.DATE_FORMAT_STRING
            )
        else:
            temp_datetime = dt.datetime.strptime(
                window_size_input_values[0], constants.WINDOW_SIZE_FORMAT_STRING
            )
            window_size_timedelta = dt.timedelta(
                hours=temp_datetime.hour,
                minutes=temp_datetime.minute,
                seconds=temp_datetime.second,
            )

            tag_timestamp_string = tag_selection.split("@")[-1]
            tag_timestamp = dt.datetime.strptime(
                tag_timestamp_string, constants.DATE_FORMAT_STRING
            )
            start_time = tag_timestamp - window_size_timedelta
            end_time = tag_timestamp + window_size_timedelta
    except (ValueError, TypeError):
        # ValueError occurs when input format is incorrect
        # TypeError occurs when input box is blank
        return dash.no_update, True, "Error parsing time input, please check format."

    sli_response = rpc_client.get_slis(
        start_time=start_time,
        end_time=end_time,
        sli_types=[sli_type],
    )

    dict_slis: List[Dict[str, Any]] = [
        json_format.MessageToDict(sli) for sli in sli_response.slis
    ]

    # Dash serializes the objects placed into Stores via json, but this can lead to
    # unexpected behavior with objects (particularly datetimes).
    # This can make it confusing to store objects directly, so we choose to store
    # timestamps instead of datetimes for a clearer interface from the reader's perspective.
    # We are forced to convert SLI protos to dictionaries to store them as well.
    return [
        {
            "start_timestamp": start_time.timestamp(),
            "end_timestamp": end_time.timestamp(),
            "dict_slis": dict_slis,
        },
        False,
        None,
    ]


@app.callback(
    Output(id_constants.CHANGE_OVER_TIME_TEXT_OUTPUT_PANEL, "children"),
    Input(id_constants.CHANGE_OVER_TIME_SLI_STORE, "data"),
    prevent_initial_call=True,
)
def update_change_over_time_text_output_panel(change_over_time_data):
    if change_over_time_data == {}:
        return None

    start_time = dt.datetime.fromtimestamp(change_over_time_data["start_timestamp"])
    end_time = dt.datetime.fromtimestamp(change_over_time_data["end_timestamp"])
    dict_slis = change_over_time_data["dict_slis"]
    slis = [json_format.ParseDict(dict_sli, SLI()) for dict_sli in dict_slis]

    node_name_sli_map = defaultdict(list)
    for sli in slis:
        node_name_sli_map[sli.node_name].append(sli)

    composite_slis = [
        transformers.generate_before_after_composite_slis(slis, start_time, end_time)
        for slis in node_name_sli_map.values()
    ]
    return converters.change_over_time_datatable_from_composite_slis(
        composite_slis, id_constants.CHANGE_OVER_TIME_DATATABLE
    )
