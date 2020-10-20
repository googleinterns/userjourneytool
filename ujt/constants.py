""" Constants for UJT.

Generally contains constants for styling.
"""
from collections import defaultdict
from typing import Any, Dict

from graph_structures_pb2 import NodeType, Status

from . import id_constants

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

# These styles are hardcoded -- cannot be changed by style map.
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
    {
        "selector": f".{NodeType.Name(NodeType.NODETYPE_SERVICE)}",
        "style": {
            "shape": "rectangle",
            "background-blacken": COMPOUND_BACKGROUND_BLACKEN_FACTOR,
        },
    },
    {
        "selector": f".{NodeType.Name(NodeType.NODETYPE_VIRTUAL)}",
        "style": {
            "border-style": "dashed",
            "shape": "octagon",
            "background-blacken": VIRTUAL_BACKGROUND_BLACKEN_FACTOR,
        },
    },
    {
        "selector": f".{Status.Name(Status.STATUS_HEALTHY)}",
        "style": {
            "background-color": HEALTHY_COLOR,
        },
    },
    {
        "selector": f".{Status.Name(Status.STATUS_WARN)}",
        "style": {
            "background-color": WARN_COLOR,
        },
    },
    {
        "selector": f".{Status.Name(Status.STATUS_ERROR)}",
        "style": {
            "background-color": ERROR_COLOR,
        },
    },
    {
        "selector": f".{HIGHLIGHTED_UJ_EDGE_CLASS}",
        "style": {
            "line-color": HIGHLIGHTED_UJ_EDGE_COLOR,
        },
    },
    {
        "selector": f".{OVERRIDE_CLASS}",
        "style": {
            "shape": "tag",
        },
    },
]

DEFAULT_STYLE_MAP: Dict[str, Dict[str, Any]] = {
    "HIDDEN": {
        "display": "none",
    },
    "HIGHLIGHTED": {
        "border-color": "deeppink",
        "border-width": 5,
        "line-color": "deeppink",
        "width": 5,
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

CLEAR_CACHE_ON_STARTUP = True
CACHE_DEFAULT_VALUES = {
    id_constants.VIRTUAL_NODE_MAP: {},  # Dict[str, VirtualNode]
    id_constants.PARENT_VIRTUAL_NODE_MAP: {},  # Dict[str, str]
    id_constants.COMMENT_MAP: {},  # Dict[str, str]
    id_constants.OVERRIDE_STATUS_MAP: {},  # Dict[str, Status]
    id_constants.TAG_LIST: ["a", "b", "c"],  # List[str] # DEBUG_REMOVE
    id_constants.TAG_MAP: defaultdict(list),  # DefaultDict[str, List[str]]
    id_constants.STYLE_MAP: DEFAULT_STYLE_MAP,  # Dict[str, Dict[str, str]]
    id_constants.VIEW_LIST: [],  # List[List[str]]
}
