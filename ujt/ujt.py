""" Main entry point for UJT. """


from . import callbacks, components, constants, state  # noqa
from .dash_app import app, cache


def initialize_ujt():
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
