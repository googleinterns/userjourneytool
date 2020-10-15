""" Main entry point for UJT. """

from . import components, constants, state

# Ask python reviewer about this.
# from .callbacks import * doesn't import all modules, but import * isn't recommended anyway
# is there a way to programatically specify this?
# Python importing is confusing...
from .callbacks import (  # noqa
    apply_tag_callbacks,
    comment_callbacks,
    create_tag_callbacks,
    graph_callbacks,
    panel_callbacks,
    signal_callbacks,
    style_callbacks,
    view_callbacks,
    virtual_node_callbacks,
)
from .dash_app import app, cache


def initialize_ujt():
    signal_callbacks.generate_composite_signals()

    if constants.CLEAR_CACHE_ON_STARTUP:
        cache.clear()

    # If first time running server, set these persisted properties as dicts
    for cache_key, default_value in constants.CACHE_DEFAULT_VALUES.items():
        if cache.get(cache_key) is None:
            cache.set(cache_key, default_value)

    # Request and cache the dependency topology from the reporting server
    state.get_message_maps()


if __name__ == "__main__":
    initialize_ujt()
    app.layout = components.get_layout()
    app.run_server(debug=True)
