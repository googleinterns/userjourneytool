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

COMPOUND_BACKGROUND_BLACKEN_FACTOR = -.5
VIRTUAL_BACKGROUND_BLACKEN_FACTOR = -.8
SELECTED_NODE_BORDER_WIDTH = 1
SELECTED_NODE_BORDER_COLOR = "black"

GRAPH_BACKGROUND_COLOR = "azure"
GRAPH_WIDTH = "100%"
GRAPH_HEIGHT = "600px"

USER_JOURNEY_DATATABLE_ID = "user-journey-datatable"
SLI_DATATABLE_ID = "datatable-slis"
CHILD_DATATABLE_ID = "datatable-child-nodes"
DEPENDENCY_DATATABLE_ID = "datatable-dependency-nodes"

BOOTSTRAP_BUTTON_COLUMN_CLASSES = "m-1 d-flex justify-content-center"

CYTO_STYLESHEET = [
    {
        "selector": "node",
        "style": {
            "content": "data(label)",
        }
    },
    {
        "selector": "edge",
        "style":
            {
                "curve-style": "straight",
                "target-arrow-shape": "triangle",
                "arrow-scale": 2,
            }
    },
    {
        "selector": f".{NodeType.Name(NodeType.NODETYPE_SERVICE)}",
        "style":
            {
                "shape": "rectangle",
                "background-blacken": COMPOUND_BACKGROUND_BLACKEN_FACTOR,
            }
    },
    {
        "selector": f".{Status.Name(Status.STATUS_HEALTHY)}",
        "style": {
            "background-color": HEALTHY_COLOR,
        }
    },
    {
        "selector": f".{Status.Name(Status.STATUS_WARN)}",
        "style": {
            "background-color": WARN_COLOR,
        }
    },
    {
        "selector": f".{Status.Name(Status.STATUS_ERROR)}",
        "style": {
            "background-color": ERROR_COLOR,
        }
    },
    {
        "selector": ":selected",
        "style":
            {
                "border-width": SELECTED_NODE_BORDER_WIDTH,
                "border-color": SELECTED_NODE_BORDER_COLOR,
            }
    },
    {
        "selector": f".{HIGHLIGHTED_UJ_EDGE_CLASS}",
        "style": {
            "line-color": HIGHLIGHTED_UJ_EDGE_COLOR,
        }
    },
    {
        "selector": f".{NodeType.Name(NodeType.NODETYPE_VIRTUAL)}",
        "style":
            {
                "border-style": "dashed",
                "shape": "octagon",
                "background-blacken": VIRTUAL_BACKGROUND_BLACKEN_FACTOR,
            }
    },
    {
        "selector": f".{OVERRIDE_CLASS}",
        "style": {
            "shape": "tag",
        }
    }
]

DATATABLE_CONDITIONAL_STYLE = [
    {
        "if": {
            "column_id": "Status",
            "filter_query": "{Status} = HEALTHY"
        },
        "color": HEALTHY_COLOR,
    },
    {
        "if": {
            "column_id": "Status",
            "filter_query": "{Status} = WARN"
        },
        "color": WARN_COLOR,
    },
    {
        "if": {
            "column_id": "Status",
            "filter_query": "{Status} = ERROR"
        },
        "color": ERROR_COLOR,
    }
]
