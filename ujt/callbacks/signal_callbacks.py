""" Provides a function to register callbacks connecting the relevant signals.
"""

import dash
from dash.dependencies import Input, Output

from .. import id_constants, utils
from ..dash_app import app

# We don't place this in constants or id_constants since it's more relevant here.
COMPOSITE_SIGNAL_MAP = {
    id_constants.SIGNAL_VIRTUAL_NODE_UPDATE: (
        id_constants.SIGNAL_VIRTUAL_NODE_ADD,
        id_constants.SIGNAL_VIRTUAL_NODE_DELETE,
        id_constants.SIGNAL_VIRTUAL_NODE_EXPAND,
        id_constants.SIGNAL_VIRTUAL_NODE_COLLAPSE,
    ),
    id_constants.SIGNAL_TAG_UPDATE: (
        id_constants.SIGNAL_TAG_CREATE,
        id_constants.SIGNAL_TAG_DELETE,
        id_constants.SIGNAL_TAG_SAVE,
    ),
    id_constants.SIGNAL_APPLIED_TAG_UPDATE: (
        id_constants.SIGNAL_APPLIED_TAG_ADD,
        id_constants.SIGNAL_APPLIED_TAG_REMOVE,
        id_constants.SIGNAL_APPLIED_TAG_MODIFY,
        id_constants.SIGNAL_APPLIED_TAG_BATCH_ADD,
        id_constants.SIGNAL_APPLIED_TAG_BATCH_REMOVE,
    ),
    id_constants.SIGNAL_STYLE_UPDATE: (
        id_constants.SIGNAL_STYLE_SAVE,
        id_constants.SIGNAL_STYLE_DELETE,
    ),
    id_constants.SIGNAL_COMPOSITE_TAGGING_UPDATE: (
        id_constants.SIGNAL_TAG_UPDATE,
        id_constants.SIGNAL_APPLIED_TAG_UPDATE,
        id_constants.SIGNAL_VIEW_UPDATE,
        id_constants.SIGNAL_STYLE_UPDATE,
    ),
}


def generate_generic_update_signal(*args, **kwargs):
    """Combines individual signals into a composite update signal.

    This allows other callbacks to avoid having to register each individual type of signal
    (create, remove, etc...) when they are interested in any change to the underlying data structure.
    However, callbacks have the flexibility to only listen to the signals that correspond to
    specific types of operations.

    For example, consider the style functionality.
    The save style button callback needs to update the properties of the save toast,
    and saves the style as a side effect. This callback updates the SIGNAL_STYLE_SAVE signal.
    The load and delete callback needs to update the properties of the text fields,
    and deletes the style as a side effect. This callback updates the SIGNAL_STYLE_DELETE signal.

    The SIGNAL_STYLE_UPDATE is used to trigger the update_cytoscape_stylesheet callback.
    If we want to update the SIGNAL_STYLE_UPDATE directly from the save and delete buttons,
    we have to combine the two callbacks to saving and deleting (since Dash only supports assigning
    to an output with a single callback).
    In order to avoid combining the callbacks, we let them each produce their own update signals
    and combine them with this callback is a workaround.

    Returns:
        The value of the signal that caused the composite signal to update.
    """

    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)

    return triggered_value


def generate_composite_signals():
    for output_signal_id, input_signal_ids in COMPOSITE_SIGNAL_MAP.items():
        dash_output = Output(output_signal_id, "children")
        dash_inputs = [
            Input(input_signal_id, "children") for input_signal_id in input_signal_ids
        ]
        # Usually we use app.callback as a decorator, which is syntatic sugar
        # app.callback(outputs=..., inputs=..., state=..., prevent_initial_call=...)(decorated_function)
        # Here we call the decorator directly to programatically register the callbacks.
        app.callback(dash_output, dash_inputs, prevent_initial_call=True)(
            generate_generic_update_signal
        )
