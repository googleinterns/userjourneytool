""" Main entry point for UJT. """

from collections import defaultdict

from . import callbacks, components, constants, converters, state
from .dash_app import app, cache


def initialize_ujt():
    if constants.CLEAR_CACHE_ON_STARTUP:
        cache.clear()
    # If first time running server, set these persisted properties as dicts
    map_names = [
        "virtual_node_map",  # Dict[str, VirtualNode]
        "parent_virtual_node_map",  # Dict[str, str]
        "comment_map",  # Dict[str, str]
        "override_status_map",  # Dict[str, Status]
    ]
    for map_name in map_names:
        if cache.get(map_name) is None:
            cache.set(map_name, {})

    list_names = ["tag_list"]
    for list_name in list_names:
        if cache.get(list_name) is None:
            cache.set(list_name, ["a", "b", "c", "d"])

    defaultdict_names = [
        "tag_map",
    ]
    for defaultdict_name in defaultdict_names:
        if cache.get(defaultdict_name) is None:
            cache.set(defaultdict_name, defaultdict(list))

    # Request and cache the dependency topology from the reporting server
    state.get_message_maps()


if __name__ == "__main__":
    initialize_ujt()
    app.layout = components.get_layout()
    app.run_server(debug=True)
