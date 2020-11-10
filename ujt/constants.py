""" Constants for UJT.

Generally contains constants for styling.
"""
from collections import defaultdict
from typing import Any, Dict

from graph_structures_pb2 import NodeType, Status

from . import id_constants

# configurable constants -- move this to a config file
CLEAR_CACHE_ON_STARTUP = True
REFRESH_TOPOLOGY_ON_STARTUP = True
REFRESH_SLI_ON_INTERVAL = True
CLIENT_SLI_REFRESH_INTERVAL_MILLIS = 30 * 1000  # ms
SERVER_SLI_REFRESH_INTERVAL_SECONDS = 30

# functional constants
CLIENT_CLASS = "CLIENT"
HIGHLIGHTED_UJ_EDGE_CLASS = "HIGHLIGHTED_UJ_EDGE"
OVERRIDE_CLASS = "OVERRIDE"

OK_SIGNAL = "OK"

ALL_USER_JOURNEY_DROPDOWN_VALUE = "ALL"

CUSTOM_TIME_RANGE_DROPDOWN_VALUE = "Custom Range"
DATE_FORMAT = "YYYY-MM-DDTHH:MM:SS"  # ISO 8601
DATE_FORMAT_STRING = "%Y-%m-%dT%H:%M:%S"

WINDOW_SIZE_FORMAT = "HH:MM:SS"
WINDOW_SIZE_FORMAT_STRING = "%H:%M:%S"

NO_DATA_SUBCLASS = "NODATA"
IMPROVED_SUBCLASS = "IMPROVED"
WORSENED_SUBCLASS = "WORSENED"

# styling constants
HEALTHY_COLOR = "green"
HEALTHY_IMPROVED_COLOR = "lightgreen"
HEALTHY_WORSENED_COLOR = "#005216"

WARN_COLOR = "orange"
WARN_IMPROVED_COLOR = "sandybrown"
WARN_WORSENED_COLOR = "darkorange"

ERROR_COLOR = "red"
ERROR_IMPROVED_COLOR = "salmon"
ERROR_WORSENED_COLOR = "darkred"

NO_DATA_COLOR = "black"

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

# Generate the necessary gradient styles for change over time feature
subclasses = [
    Status.Name(Status.STATUS_HEALTHY),
    f"{Status.Name(Status.STATUS_HEALTHY)}_{IMPROVED_SUBCLASS}",
    f"{Status.Name(Status.STATUS_HEALTHY)}_{WORSENED_SUBCLASS}",
    Status.Name(Status.STATUS_WARN),
    f"{Status.Name(Status.STATUS_WARN)}_{IMPROVED_SUBCLASS}",
    f"{Status.Name(Status.STATUS_WARN)}_{WORSENED_SUBCLASS}",
    Status.Name(Status.STATUS_ERROR),
    f"{Status.Name(Status.STATUS_ERROR)}_{IMPROVED_SUBCLASS}",
    f"{Status.Name(Status.STATUS_ERROR)}_{WORSENED_SUBCLASS}",
    NO_DATA_SUBCLASS,
]
subclass_colors = [
    HEALTHY_COLOR,
    HEALTHY_IMPROVED_COLOR,
    HEALTHY_WORSENED_COLOR,
    WARN_COLOR,
    WARN_IMPROVED_COLOR,
    WARN_WORSENED_COLOR,
    ERROR_COLOR,
    ERROR_IMPROVED_COLOR,
    ERROR_WORSENED_COLOR,
    NO_DATA_COLOR,
]
for before_subclass, before_color in zip(subclasses, subclass_colors):
    for after_subclass, after_color in zip(subclasses, subclass_colors):
        BASE_CYTO_STYLESHEET.append(
            {
                "selector": f".{before_subclass}_{after_subclass}",
                "style": {
                    "background-fill": "linear-gradient",
                    "background-gradient-stop-colors": f"{before_color} {after_color}",
                    "background-gradient-direction": "to-right",
                },
            }
        )

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

DATATABLE_STYLE = {
    "overflowX": "auto",
}

DATATABLE_CSS = [
    {
        "selector": ".row",
        "rule": "margin: 0",
    },
]

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
