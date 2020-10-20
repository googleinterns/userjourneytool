""" Callbacks that handle view creation/deletion/modification functionality.
"""


import dash
from dash.dependencies import ALL, Input, Output
from dash.exceptions import PreventUpdate

from .. import constants, id_constants, state, utils
from ..dash_app import app


@app.callback(
    Output(id_constants.SIGNAL_VIEW_CREATE, "children"),
    Input({id_constants.CREATE_VIEW_BUTTON: ALL}, "n_clicks_timestamp"),
)
def create_view(create_timestamps):
    """Handles creating views

    This function is called:
        when the create view button is clicked.

    Args:
        create_timestamps: List of the timestamps of the CREATE_VIEW_BUTTON buttons were called.
            Value unused, input only provided to register callback.
            Should only contain one value.

    Returns:
        A signal to add to the SIGNAL_VIEW_CREATE hidden div.
    """
    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    # When the button is initially added, it fires a callback.
    # We want to prevent this callback from making changes to the update signal.
    if triggered_value is None:
        raise PreventUpdate

    state.create_view("", "")
    return constants.OK_SIGNAL


@app.callback(
    Output(id_constants.SIGNAL_VIEW_DELETE, "children"),
    Input(
        {
            id_constants.DELETE_VIEW_BUTTON: id_constants.DELETE_VIEW_BUTTON,
            "index": ALL,
        },
        "n_clicks_timestamp",
    ),
    prevent_initial_call=True,
)
def delete_view(delete_timestamps):
    """Handles deleting views from the view list.

    This function is called:
        when a delete view button is clicked

    Args:
        delete_timestamps: List of the timestamps of when DELETE_VIEW_BUTTON buttons were called.
            Value unused, input only provided to register callback.
            Should contain only one value.

    Returns:
        A signal to add to the SIGNAL_VIEW_DELETE hidden div.
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
    view_idx = id_dict["index"]
    state.delete_view(view_idx)

    return constants.OK_SIGNAL


@app.callback(
    Output(id_constants.SIGNAL_VIEW_MODIFY, "children"),
    [
        Input(
            {
                id_constants.VIEW_TAG_DROPDOWN: id_constants.VIEW_TAG_DROPDOWN,
                "index": ALL,
            },
            "value",
        ),
        Input(
            {
                id_constants.VIEW_STYLE_DROPDOWN: id_constants.VIEW_STYLE_DROPDOWN,
                "index": ALL,
            },
            "value",
        ),
    ],
    prevent_initial_call=True,
)
def modify_view(tag_dropdown_values, style_dropdown_values):
    """Updates the corresponding applied tag in the tag map.

    This function is called:
        when a VIEW_TAG_DROPDOWN value is updated
        when a VIEW_STYLE_DROPDOWN value is updated

    Args:
        tag_dropdown_values: the values of the VIEW_TAG_DROPDOWN dropdown menus.
        style_dropdown_values: the values of the VIEW_STYLE_DROPDOWN dropdown menus.

    Returns:
        A signal to be placed in the SIGNAL_VIEW_MODIFY.
    """
    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    if triggered_value is None:
        raise PreventUpdate

    # Unfortunately, we have to convert the stringified dict back to a dict.
    # Dash doesn't provide us any other method to see which element triggered the callback.
    # This isn't very elegant, but I don't see any other way to proceed.
    id_dict = utils.string_to_dict(triggered_id)
    view_idx = id_dict["index"]

    tag_value = tag_dropdown_values[view_idx]
    style_value = style_dropdown_values[view_idx]

    state.update_view(view_idx, tag_value, style_value)

    return constants.OK_SIGNAL
