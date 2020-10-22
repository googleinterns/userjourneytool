""" Callbacks that handle view creation/deletion/modification functionality.
"""

from typing import List, Tuple

import dash
from dash.dependencies import ALL, Input, Output
from dash.exceptions import PreventUpdate

from .. import constants, id_constants, utils
from ..dash_app import app


@app.callback(
    [
        Output(id_constants.VIEW_STORE, "data"),
        Output(id_constants.SIGNAL_VIEW_UPDATE, "children"),
    ],
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
        Input(
            {
                id_constants.CREATE_VIEW_BUTTON: ALL,
            },
            "n_clicks_timestamp",
        ),
        Input(
            {
                id_constants.DELETE_VIEW_BUTTON: id_constants.DELETE_VIEW_BUTTON,
                "index": ALL,
            },
            "n_clicks_timestamp",
        ),
    ],
)
def update_view_store(
    tag_dropdown_values, style_dropdown_values, create_timestamps, delete_timestamps
) -> Tuple[List[Tuple[str, str]], str]:
    """Saves the current list of views to the VIEW_STORE .

    Notice that the style of this callback is different from the apply tag or create tag callbacks,
    even though they both handle the same type of UI elements (dynamically creating rows).
    This callback updates the VIEW_STORE by reading the current state of the rows of dropdown menus.
    In turn, the generate_view_panel callback updates the dropdown menus based on the contents of the VIEW_STORE.

    Views are written to the VIEW_STORE in order to make them local for each user.
    Thus, we must combine all the functionality into a single callback to write to the component.
    This is in contrast to styles, tags, and applied tags, callbacks, which write
    their respective data structure to the Dash server via the state module as a side effect.

    We could theoretically refactor the tag creation panel and tag application panel to be in this style.
    It would probably be a little cleaner in the case of the tag creation panel, since the panel only
    changes in response to create or delete tag buttons.
    In contrast, the tag application panel changes based on any tag update, its own apply/remove buttons, and
    user interactions with the cytoscape graph.

    This style offers a more functional approach, so we can be a little more confident in the correctness of
    the state of our data structures.
    Moreover, it's relatively clean.

    However, the complexity would probably increase dramatically in the apply tag callbacks case.
    We also lose the granularity of output signals. (In theory, we could assign different values to the output
    signal, but each callback that registers the signal would have to check the signal value.)

    I think we can just accept this inconsistency in the view case and leave the other callbacks as-is.

    This function is called:
        when a VIEW_TAG_DROPDOWN value is updated
        when a VIEW_STYLE_DROPDOWN value is updated
        when a view row is created
        when a view row is deleted

    Args:
        tag_dropdown_values: the values of the VIEW_TAG_DROPDOWN dropdown menus.
        style_dropdown_values: the values of the VIEW_STYLE_DROPDOWN dropdown menus.
        create_timestamps: the timestamp of when the CREATE_VIEW_BUTTON was clicked
            Should contain only one element.
        delete_timestamps: the timestamp of when the DELETE_VIEW_BUTTON was clicked
            Should contain only one element.

    Returns:
        A signal to be placed in the SIGNAL_VIEW_MODIFY.
    """
    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)
    if triggered_id is None:
        raise PreventUpdate

    tag_inputs = ctx.inputs_list[0]
    style_inputs = ctx.inputs_list[1]

    tag_inputs = sorted(tag_inputs, key=lambda x: x["id"]["index"])
    style_inputs = sorted(style_inputs, key=lambda x: x["id"]["index"])

    view_list = [
        (tag_input["value"], style_input["value"])
        for tag_input, style_input in zip(tag_inputs, style_inputs)
    ]

    # Unfortunately, we have to convert the stringified dict back to a dict.
    # Dash doesn't provide us any other method to see which element triggered the callback.
    # This isn't very elegant, but I don't see any other way to proceed.

    id_dict = utils.string_to_dict(triggered_id)

    if id_constants.CREATE_VIEW_BUTTON in id_dict and triggered_value is not None:
        view_list.append(("", ""))
    elif id_constants.DELETE_VIEW_BUTTON in id_dict and triggered_value is not None:
        del view_list[id_dict["index"]]

    return view_list, constants.OK_SIGNAL
