from graph_structures_pb2 import NodeType, Status


CLIENT_CLASS = "CLIENT"

HEALTHY_COLOR = "green"
WARN_COLOR = "orange"
ERROR_COLOR = "red"

COMPOUND_BACKGROUND_BLACKEN_FACTOR = -.5
SELECTED_NODE_BORDER_WIDTH = 1
SELECTED_NODE_BORDER_COLOR = "black"


GRAPH_BACKGROUND_COLOR = "azure"
GRAPH_WIDTH = "100%"
GRAPH_HEIGHT = "600px"

CYTO_STYLESHEET = [
    {
        "selector": "node",
        "style": {
            "content": "data(label)",
        }
    },
    {
        "selector": "edge",
        "style": {
            "curve-style": "straight",
            "target-arrow-shape": "triangle",
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
        "selector": ":selected:",
        "style":
            {
                "border-width": SELECTED_NODE_BORDER_WIDTH,
                "border-color": SELECTED_NODE_BORDER_COLOR,
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