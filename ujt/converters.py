from typing import Any, Collection, Dict, List, Union

import dash_bootstrap_components as dbc
import dash_table
from graph_structures_pb2 import (
    Client,
    Dependency,
    Node,
    NodeType,
    SLIType,
    Status)

from . import utils, constants


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
                "classes": constants.CLIENT_CLASS,
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


def datatable_from_nodes(nodes, use_relative_names, table_id):
    columns = [{"name": name, "id": name} for name in ["Node", "Status"]]
    data = [
        {
            "Node":
                utils.relative_name(node.name)
                if use_relative_names else node.name,
            "Status":
                utils.human_readable_enum_name(node.status,
                                               Status),
        } for node in nodes
    ]

    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=data,
        style_data_conditional=constants.DATATABLE_CONDITIONAL_STYLE,
    )


def datatable_from_slis(slis, table_id):
    columns = [
        {
            "name": name,
            "id": name,
        } for name in ["Type",
                       "Status",
                       "Value",
                       "Warn Range",
                       "Error Range"]
    ]
    data = [
        {
            "Type":
                utils.human_readable_enum_name(sli.sli_type,
                                               SLIType),
            "Status":
                utils.human_readable_enum_name(sli.status,
                                               Status),
            "Value":
                round(sli.sli_value,
                      2),
            "Warn Range":
                f"({sli.slo_warn_lower_bound}, {sli.slo_warn_upper_bound})",
            "Error Range":
                f"({sli.slo_error_lower_bound}, {sli.slo_error_upper_bound})",
        } for sli in slis
    ]

    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=data,
        style_data_conditional=constants.DATATABLE_CONDITIONAL_STYLE,
    )


def datatable_from_client(client, table_id):
    columns = [
        {
            "name": name,
            "id": name,
        } for name in ["User Journey",
                       "Status"]
    ]
    data = [
        {
            "User Journey":
                utils.relative_name(user_journey.name),
            "Status":
                utils.human_readable_enum_name(user_journey.status,
                                               Status),
        } for user_journey in client.user_journeys
    ]
    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=data,
        style_data_conditional=constants.DATATABLE_CONDITIONAL_STYLE,
    )
