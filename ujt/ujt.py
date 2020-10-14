""" Main entry point for UJT. """

from collections import defaultdict

from . import components, constants, state
from .dash_app import app, cache


def initialize_ujt():
    if constants.CLEAR_CACHE_ON_STARTUP:
        cache.clear()

    # If first time running server, set these persisted properties as dicts
    cache_key_default_values = [
        ("virtual_node_map", {}),  # Dict[str, VirtualNode]
        ("parent_virtual_node_map", {}),  # Dict[str, str]
        ("comment_map", {}),  # Dict[str, str]
        ("override_status_map", {}),  # Dict[str, Status]
        (
            "tag_list",
            ["a", "b", "c", "d"],
        ),  # List[str] # set to a, b, c, d for testing only
        ("tag_map", defaultdict(list)),  # DefaultDict[str, List[str]]
        ("style_map", constants.DEFAULT_STYLE_MAP),
        ("view_list", []),  # List[Tuple[str, str]]
    ]
    for cache_key, default_value in cache_key_default_values:
        if cache.get(cache_key) is None:
            cache.set(cache_key, default_value)

    # Request and cache the dependency topology from the reporting server
    state.get_message_maps()


if __name__ == "__main__":
    initialize_ujt()
    app.layout = components.get_layout()
    app.run_server(debug=True)
