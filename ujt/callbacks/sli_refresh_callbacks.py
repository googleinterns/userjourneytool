import dash
from dash.dependencies import Input, Output

from .. import id_constants, utils
from ..dash_app import app


@app.callback(
    Output(id_constants.SIGNAL_SLI_REFRESH, "children"),
    [
        Input(id_constants.REFRESH_SLI_BUTTON, "n_clicks_timestamp"),
        Input(id_constants.REFRESH_SLI_INTERVAL, "n_intervals"),
    ],
    prevent_initial_call=True,
)
def update_sli_refresh_signal(n_clicks_timestamp: int, n_intervals: int):
    """Updates the SLI refresh signal.

    Args:
        n_clicks_timestamp: the timestamp when the SLI refresh button was clicked
        n_intervals: the amount of times the interval component was updated

    Returns:
        a constant to be placed into the SLI refresh signal
    """
    ctx = dash.callback_context
    triggered_id, triggered_prop, triggered_value = utils.ctx_triggered_info(ctx)
    return triggered_id
