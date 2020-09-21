from typing import Any, Collection, Dict, List, Union

import dash_bootstrap_components as dbc
from graph_structures_pb2 import (
    Client,
    Dependency,
    Node,
    NodeType,
    SLIType,
    Status)

from . import utils

CLIENT_CLASS = "CLIENT"


def cytoscape_elements_from_nodes(node_name_message_map: Dict[str, Node]):
    """ Converts a dictionary of Node protobufs to a cytoscape graph format.

    Args:
        node_name_message_map: A dictionary mapping Node names to their corresponding Node protobuf message.
    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service) or edge (Dependency).
    """

    node_elements: List[Dict[str, Any]] = []
    edge_elements: List[Dict[str, Any]] = []

    for name, node in node_name_message_map.items():
        node_element: Dict[str,
                           Any] = {
                               "data":
                                   {
                                       "id":
                                           name,
                                       "label":
                                           name.split(".")
                                           [-1]  # the node's relative name
                                   },
                               "classes":
                                   " ".join(
                                       [
                                           NodeType.Name(node.node_type),
                                           Status.Name(node.status),
                                       ])
                           }
        if node.parent_name:
            node_element["data"]["parent"] = node.parent_name
        node_elements.append(node_element)

        for dependency in node.dependencies:
            edge_element = {
                "data": {
                    "source": name,
                    "target": dependency.target_name,
                }
            }
            edge_elements.append(edge_element)

    return node_elements + edge_elements


def cytoscape_elements_from_clients(client_name_message_map: Dict[str, Client]):
    """ Converts a dictionary  of Client protobufs to a cytoscape graph format.

    Args:
        client_name_message_map: A dictionary mapping Client names to the corresponding Client protobuf message.
    Returns:
        A list of dictionary objects, each containing information regarding a single node (Client) or edge (Dependency).
    """

    node_elements: List[Dict[str, Collection[str]]] = []
    edge_elements: List[Dict[str, Collection[str]]] = []

    for name, message in client_name_message_map.items():
        node_elements.append(
            {
                "data": {
                    "id": name,
                    "label": name,
                },
                "classes": CLIENT_CLASS,
            })
        for user_journey in message.user_journeys:
            for dependency in user_journey.dependencies:
                edge_elements.append({
                    "data": {
                        "source":
                            name,  # careful! cytoscape element source is the Client node, but the Dependency's source_name should be a fully qualified UserJourney name 
                        "target": dependency.target_name,
                    }
                })

    return node_elements + edge_elements


def bootstrap_info_table_from_nodes(nodes, use_relative_names=False):
    node_rows = [
        dbc.Row(
            children=[
                dbc.Col("Node"),
                dbc.Col("Status"),
            ],
            className="header-row"
        ),
    ]

    for node in nodes:
        node_row = dbc.Row(
            children=[
                dbc.Col(
                    utils.relative_name(node.name
                                       ) if use_relative_names else node.name),
                dbc.Col(
                    children=utils.human_readable_enum_name(
                        node.status,
                        Status),
                    className=Status.Name(node.status),
                ),
            ],
            className="data-row",
        )
        node_rows.append(node_row)

    return node_rows


def bootstrap_info_table_from_slis(slis):
    sli_rows = [
        dbc.Row(
            children=[
                dbc.Col("SLI"),
                dbc.Col("SLI Type"),
                dbc.Col("SLI Status"),
                dbc.Col("Warn Range"),
                dbc.Col("Error Range"),
            ],
            className="header-row",
        ),
    ]

    for sli in slis:
        sli_row = dbc.Row(
            children=[
                dbc.Col(utils.human_readable_enum_name(sli.sli_type,
                                                       SLIType)),
                dbc.Col(
                    children=utils.human_readable_enum_name(sli.status,
                                                            Status),
                    className=Status.Name(sli.status),
                ),
                dbc.Col(round(sli.sli_value,
                              2)),
                dbc.Col(
                    f"({sli.slo_warn_lower_bound}, {sli.slo_warn_upper_bound})"
                ),
                dbc.Col(
                    f"({sli.slo_error_lower_bound}, {sli.slo_error_upper_bound})"
                ),
            ],
            className="data-row",
        )
        sli_rows.append(sli_row)

    return sli_rows
