""" Constants for UJT.

Generally contains constants for styling.
"""
from graph_structures_pb2 import NodeType, Status

CLEAR_CACHE_ON_STARTUP = True

CLIENT_CLASS = "CLIENT"
HIGHLIGHTED_UJ_EDGE_CLASS = "HIGHLIGHTED_UJ_EDGE"
OVERRIDE_CLASS = "OVERRIDE"
OK_SIGNAL = "OK"

HEALTHY_COLOR = "green"
WARN_COLOR = "orange"
ERROR_COLOR = "red"
HIGHLIGHTED_UJ_EDGE_COLOR = "purple"

COMPOUND_BACKGROUND_BLACKEN_FACTOR = -0.5
VIRTUAL_BACKGROUND_BLACKEN_FACTOR = -0.8
SELECTED_NODE_BORDER_WIDTH = 1
SELECTED_NODE_BORDER_COLOR = "black"

GRAPH_BACKGROUND_COLOR = "azure"
GRAPH_WIDTH = "100%"
GRAPH_HEIGHT = "600px"

BOOTSTRAP_BUTTON_COLUMN_CLASSES = "m-1 d-flex justify-content-center"

CYTO_LAYOUT = {
    "name": "dagre",
    "nodeDimensionsIncludeLabels": "true",
    "animate": "true",
}

CYTO_STYLE = {
    "width": GRAPH_WIDTH,
    "height": GRAPH_HEIGHT,
    "backgroundColor": GRAPH_BACKGROUND_COLOR,
}

# These selectors are hardcoded -- cannot be changed by style map.
BASE_CYTO_STYLESHEET = [
    {
        "selector": "node",
        "style": {
            "content": "data(label)",
        },
    },
    {
        "selector": "edge",
        "style": {
            "curve-style": "straight",
            "target-arrow-shape": "triangle",
            "arrow-scale": 2,
        },
    },
    {
        "selector": ":selected",
        "style": {
            "border-width": SELECTED_NODE_BORDER_WIDTH,
            "border-color": SELECTED_NODE_BORDER_COLOR,
        },
    },
]

DEFAULT_STYLE_MAP = {
    NodeType.Name(NodeType.NODETYPE_SERVICE): {
        "shape": "rectangle",
        "background-blacken": COMPOUND_BACKGROUND_BLACKEN_FACTOR,
    },
    NodeType.Name(NodeType.NODETYPE_VIRTUAL): {
        "border-style": "dashed",
        "shape": "octagon",
        "background-blacken": VIRTUAL_BACKGROUND_BLACKEN_FACTOR,
    },
    Status.Name(Status.STATUS_HEALTHY): {
        "background-color": HEALTHY_COLOR,
    },
    Status.Name(Status.STATUS_WARN): {
        "background-color": WARN_COLOR,
    },
    Status.Name(Status.STATUS_ERROR): {
        "background-color": ERROR_COLOR,
    },
    HIGHLIGHTED_UJ_EDGE_CLASS: {
        "line-color": HIGHLIGHTED_UJ_EDGE_COLOR,
    },
    OVERRIDE_CLASS: {
        "shape": "tag",
    },
}

DATATABLE_CONDITIONAL_STYLE = [
    {
        "if": {"column_id": "Status", "filter_query": "{Status} = HEALTHY"},
        "color": HEALTHY_COLOR,
    },
    {
        "if": {"column_id": "Status", "filter_query": "{Status} = WARN"},
        "color": WARN_COLOR,
    },
    {
        "if": {"column_id": "Status", "filter_query": "{Status} = ERROR"},
        "color": ERROR_COLOR,
    },
]
