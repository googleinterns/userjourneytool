""" Main entry point for UJT. """

import argparse
import os

from . import components, config, constants, id_constants, rpc_client, state
from .callbacks import (  # noqa
    apply_tag_callbacks,
    change_over_time_callbacks,
    comment_callbacks,
    create_tag_callbacks,
    graph_callbacks,
    panel_callbacks,
    signal_callbacks,
    sli_refresh_callbacks,
    style_callbacks,
    view_callbacks,
    virtual_node_callbacks,
)
from .dash_app import app, cache


def initialize_ujt():
    signal_callbacks.generate_composite_signals()

    if config.CLEAR_CACHE_ON_STARTUP:
        cache.clear()

    # If first time running server, set these persisted properties as dicts
    for cache_key, default_value in constants.CACHE_DEFAULT_VALUES.items():
        if cache.get(cache_key) is None:
            cache.set(cache_key, default_value)

    if config.REFRESH_TOPOLOGY_ON_STARTUP:
        cache.set(id_constants.NODE_NAME_MESSAGE_MAP, None)
        cache.set(id_constants.CLIENT_NAME_MESSAGE_MAP, None)

    # Request and cache the dependency topology from the reporting server
    state.get_message_maps()


def parse_args():
    def file_exists(parser, path):
        if not os.path.exists(path):
            raise parser.error(f"{path} does not exist!")
        return path

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-c",
        "--config-path",
        help="path to configuration file (default: config.ini)",
        default="config.ini",
        type=lambda x: file_exists(arg_parser, x),
        metavar="FILE_PATH",
    )
    arguments = arg_parser.parse_args()

    return arguments


if __name__ == "__main__":
    args = parse_args()
    config.load_config(args.config_path)
    rpc_client.connect()
    initialize_ujt()
    app.layout = components.get_layout()
    app.run_server(debug=True)
