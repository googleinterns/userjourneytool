""" Callbacks that handle tag creation/deletion functionality.
"""


import dash
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate

from .. import constants, converters, id_constants, state, utils
from ..dash_app import app


@app.callback(
    Output(id_constants.SIGNAL_TAG_CREATE, "children"),
    Input({id_constants.CREATE_TAG_BUTTON: ALL}, "n_clicks_timestamp"),
    prevent_initial_call=True,
)
def create_tag(create_timestamps):
    """Handles creating tags from the tag list.

    This function is called:
        when the create tag button is clicked.

    Args:
        create_timestamps: List of the timestamps of the CREATE_TAG_BUTTON buttons was called.
            Value unused, input only provided to register callback.
            Should only contain one value.

    Returns:
        A signal to add to the SIGNAL_TAG_CREATE hidden div.
    """
    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    # When the button is initially added, it fires a callback.
    # We want to prevent this callback from making changes to the update signal.
    if triggered_value is None:
        raise PreventUpdate

    state.create_tag("")
    return constants.OK_SIGNAL


@app.callback(
    Output(id_constants.SIGNAL_TAG_DELETE, "children"),
    Input(
        {id_constants.DELETE_TAG_BUTTON: id_constants.DELETE_TAG_BUTTON, "index": ALL},
        "n_clicks_timestamp",
    ),
    prevent_initial_call=True,
)
def delete_tag(delete_timestamps):
    """Handles deleting tags from the tag list.

    This function is called:
        when a delete tag button is clicked

    Args:
        delete_timestamps: List of the timestamps of when DELETE_TAG_BUTTON buttons were called.
            Value unused, input only provided to register callback.
            Should contain only one value.

    Returns:
        A signal to add to the SIGNAL_TAG_DELETE hidden div.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    # When the button is initially added, it fires a callback.
    # We want to prevent this callback from making changes to the update signal.
    if triggered_value is None:
        raise PreventUpdate

    # Unfortunately, we have to convert the stringified dict back to a dict.
    # Dash doesn't provide us any other method to see which element triggered the callback.
    # This isn't very elegant, but I don't see any other way to proceed.
    id_dict = utils.string_to_dict(triggered_id)
    tag_idx = id_dict["index"]
    state.delete_tag(tag_idx)

    return constants.OK_SIGNAL


@app.callback(
    [
        Output({id_constants.SAVE_TAG_TOAST: ALL}, "is_open"),
        Output(id_constants.SIGNAL_TAG_SAVE, "children"),
    ],
    Input(
        {id_constants.SAVE_TAG_BUTTON: id_constants.SAVE_TAG_BUTTON, "index": ALL},
        "n_clicks_timestamp",
    ),
    State({id_constants.TAG_INPUT: id_constants.TAG_INPUT, "index": ALL}, "value"),
    prevent_initial_call=True,
)
def save_tag(n_clicks_timestamp, input_values):
    """Saves the corresponding tag from the input field to the tag list.

    Ideally, we would like to use the MATCH function to determine which button was clicked.
    However, since we only have one save tag toast for all the tags, we can't use MATCH in the Output field.
    To use MATCH, Dash requires the Output field to match the same properties as the input field.
    Refer to: https://dash.plotly.com/pattern-matching-callbacks

    This function is called:
        when the save tag button is clicked.

    Args:
        n_clicks_timestamp: List of the timestamps of when SAVE_TAG_BUTTON buttons were called.
            Value unused, input only provided to register callback.
        input_values: List of the input values in TAG_INPUT inputs.

    Returns:
        A boolean indicating whether the save tag successful toast should open.
        A signal to save in the SIGNAL_TAG_SAVE component.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_value is None:
        raise PreventUpdate

    # Unfortunately, we have to convert the stringified dict back to a dict.
    # Dash doesn't provide us any other method to see which element triggered the callback.
    # This isn't very elegant, but I don't see any other way to proceed.
    id_dict = utils.string_to_dict(triggered_id)

    tag_idx = id_dict["index"]
    tag_value = input_values[tag_idx]

    if " " in tag_value:
        raise PreventUpdate  # TODO: display an error UI element or something

    state.update_tag(tag_idx, tag_value)
    # since we pattern matched the SAVE_TAG_TOAST, we need to provide output as a list
    return [True], constants.OK_SIGNAL


@app.callback(
    Output(id_constants.BATCH_APPLIED_TAG_DROPDOWN, "options"),
    Input(id_constants.SIGNAL_TAG_UPDATE, "children"),
)
def update_batch_applied_tag_dropdown_options(tag_update_signal):
    """Updates the options in the batch applied tag dropdown on tag changes.

    Notice that we don't need to have a similar callback to update the options of the
    non-batch applied tag dropdowns.
    This is because the whole selected info panel is dynamically generated.

    This function is called:
        when a tag node is updated.

    Args:
        tag_update_signal: Signal indicating a virtual node was modified.

    Returns:
        A list of options for the batch applied tag dropdown journey dropdown.
    """
    tag_list = state.get_tag_list()
    return converters.tag_dropdown_options_from_tags(tag_list)
