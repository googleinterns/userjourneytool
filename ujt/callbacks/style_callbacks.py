""" Callbacks that handle style creation/deletion/modification functionality.
"""

import json

import dash
from dash.dependencies import Input, Output, State

from .. import constants, id_constants, state, utils
from ..dash_app import app


@app.callback(
    [
        Output(id_constants.SAVE_STYLE_TOAST, "is_open"),
        Output(id_constants.SAVE_STYLE_TOAST, "header"),
        Output(id_constants.SAVE_STYLE_TOAST, "icon"),
        Output(id_constants.SIGNAL_STYLE_SAVE, "children"),
    ],
    Input(id_constants.SAVE_STYLE_TEXTAREA_BUTTON, "n_clicks_timestamp"),
    [
        State(id_constants.STYLE_NAME_INPUT, "value"),
        State(id_constants.STYLE_TEXTAREA, "value"),
    ],
    prevent_initial_call=True,
)
def save_style(save_n_clicks_timestamps, style_name, style_str):
    """Handles saving styles to the style map.

    This function is called:
        when the save style button is clicked

    Args:
        save_n_clicks_timestamps: List of the timestamps of when SAVE_STYLE_TEXTAREA_BUTTON buttons were called.
            Should contain only one value.
            Value unused, input only provided to register callback.
        style_name_list: List of style names. Should contain only one value, from the STYLE_NAME_INPUT component.
        style_str_list: List of strings encoding styles. Should contain only one value, from the STYLE_TEXTAREA component.

    Returns:
        A 4 tuple, containing:
            A boolean indicating whether the save tag successful toast should open.
            A message to be placed in the header of the toast.
            A string to determine the toast icon.
            An updated signal to be placed in the SIGNAL_STYLE_SAVE signal.
    """

    if " " in style_name:
        return True, "Style name cannot contain spaces!", "danger", dash.no_update

    try:
        style_dict = utils.string_to_dict(style_str)
    except json.decoder.JSONDecodeError:
        return (
            True,
            "Error decoding string into valid Cytoscape style format!",
            "danger",
            dash.no_update,
        )

    state.update_style(style_name, style_dict)
    return True, "Successfully saved style!", "success", constants.OK_SIGNAL


@app.callback(
    [
        Output(id_constants.STYLE_NAME_INPUT, "value"),
        Output(id_constants.STYLE_TEXTAREA, "value"),
        Output(id_constants.SIGNAL_STYLE_DELETE, "children"),
    ],
    [
        Input(id_constants.LOAD_STYLE_TEXTAREA_BUTTON, "n_clicks_timestamp"),
        Input(id_constants.DELETE_STYLE_BUTTON, "n_clicks_timestamp"),
    ],
    State(id_constants.STYLE_NAME_INPUT, "value"),
    prevent_initial_call=True,
)
def update_style_input_fields(
    load_n_clicks_timestamp, delete_n_clicks_timestamp, style_name
):
    """Handles loading and deleting styles from the style map.

    Notice this function handles both loading and deleting, since these operations both affect
    the state of the style name and style textarea.
    We don't dynamically generate the style panel since there's always one input and one textarea.
    This makes it more inconvenient to split these cases into two callbacks, each producing their own update signal,
    because we don't use a callback (that reads from the composite update signal) to dynamically generate the style panel.

    This is slightly inconsistent with the tag creation and application callback organization, where each callback
    produces its own signal, and another callback rerenders the respective panel.
    Despite the inconsistency, I feel this method for static components makes more sense and reduces complexity.

    This function is called:
        when the load style button is clicked
        when the delete style button is clicked

    Args:
        load_n_clicks_timestamps: List of the timestamps of when LOAD_STYLE_TEXTAREA_BUTTON buttons were called.
            Should contain only one value.
            Value unused, input only provided to register callback.
        delete_n_clicks_timestamp: List of the timestamps of when DELETE_STYLE_BUTTON buttons were called.
            Should contain only one value.
            Value unused, input only provided to register callback.
        style_names: List of style names. Should contain only one value, from the STYLE_NAME_INPUT component.

    Returns:
        A 3 tuple, containing:
            The updated string to be placed in the STYLE_NAME_INPUT component.
            The updated string to be placed in the STYLE_TEXTAREA component.
            The updated signal to be placed in the SIGNAL_STYLE_DELETE signal.
    """
    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_id == id_constants.LOAD_STYLE_TEXTAREA_BUTTON:
        style_map = state.get_style_map()
        textarea_value = (
            utils.dict_to_str(style_map[style_name]) if style_name in style_map else ""
        )
        return style_name, textarea_value, dash.no_update

    if triggered_id == id_constants.DELETE_STYLE_BUTTON:
        state.delete_style(style_name)
        return "", "", constants.OK_SIGNAL

    raise ValueError
