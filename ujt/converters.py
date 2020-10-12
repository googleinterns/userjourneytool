""" Module holding converter functions.

In general, we consider converters to modify some UJT-specific data structure
(e.g. a protobuf, or List/Dict of protobufs) into a Dash-specific data structure
(e.g. cytoscape elements, dropdown options.)
"""

from typing import Any, Collection, Dict, List

import dash_table
from graph_structures_pb2 import (
    Client,
    Node,
    NodeType,
    SLIType,
    Status,
    VirtualNode)

from . import constants, utils


def cytoscape_elements_from_maps(
        node_name_message_map: Dict[str,
                                    Node],
        client_name_message_map: Dict[str,
                                      Client]):
    """ Generates a cytoscape elements dictionary from Service, SLI, and Client protobufs.

    Args:
        node_name_message_map: A dictionary mapping Node names to their corresponding Node protobuf message.
        client_name_message_map: A dictionary mapping Client names to the corresponding Client protobuf message.

    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service or Client) or edge (Dependency).
    """

    return (
        cytoscape_elements_from_node_map(node_name_message_map) +
        cytoscape_elements_from_client_map(client_name_message_map))


def cytoscape_element_from_node(node):
    """ Generates a cytoscape element from a Node proto.

    Args:
        node: A Node proto.
    
    Returns:
        A cytoscape element dictionary with values derived from the proto.
    """
    node_element: Dict[str,
                       Any] = {
                           "data":
                               {
                                   "id": node.name,  # this field later modified by appending guid
                                   "label": utils.relative_name(node.name),
                                   # ujt_id is left unmodified, used for internal indexing into maps
                                   "ujt_id": node.name,
                               },
                       }
    if node.parent_name:
        node_element["data"]["parent"] = node.parent_name
    return node_element


def cytoscape_element_from_client(client):
    """ Generates a cytoscape element from a Client proto.

    Args:
        client: A Client proto.
    
    Returns:
        A cytoscape element dictionary with values derived from the proto.
    """
    client_element = {
        "data":
            {
                "id": client.name,
                "label": client.name,
                "ujt_id": client.name,
            },
    }
    return client_element


def cytoscape_element_from_dependency(dependency):
    """ Generates a cytoscape element from a Dependency proto.

    Args:
        dependency: A Dependency proto.
    
    Returns:
        A cytoscape element dictionary with values derived from the proto.
    """
    edge_element = {
        "data":
            {
                "source": dependency.source_name,
                "target": dependency.target_name,
            }
    }
    # careful! cytoscape element source is the Client node, but the Dependency's source_name should be a fully qualified UserJourney name
    if dependency.toplevel:
        edge_element["data"]["source"] = utils.parent_full_name(
            dependency.source_name)
        edge_element["data"]["user_journey_name"] = dependency.source_name

    edge_element["data"][
        "id"] = f"{edge_element['data']['source']}/{edge_element['data']['target']}"
    edge_element["data"][
        "ujt_id"] = f"{edge_element['data']['source']}/{edge_element['data']['target']}"
    return edge_element


def cytoscape_elements_from_node_map(node_name_message_map: Dict[str, Node]):
    """ Converts a dictionary of Node protobufs to a cytoscape graph format.

    Args:
        node_name_message_map: A dictionary mapping Node names to their corresponding Node protobuf message.
    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service) or edge (Dependency).
    """

    node_elements: List[Dict[str, Any]] = []
    edge_elements: List[Dict[str, Any]] = []

    for node in node_name_message_map.values():
        node_elements.append(cytoscape_element_from_node(node))
        for dependency in node.dependencies:
            edge_elements.append(cytoscape_element_from_dependency(dependency))

    return node_elements + edge_elements


def cytoscape_elements_from_client_map(
        client_name_message_map: Dict[str,
                                      Client]):
    """ Converts a dictionary of Client protobufs to a cytoscape graph format.

    Args:
        client_name_message_map: A dictionary mapping Client names to the corresponding Client protobuf message.
    Returns:
        A list of dictionary objects, each containing information regarding a single node (Client) or edge (Dependency).
    """

    node_elements: List[Dict[str, Collection[str]]] = []
    edge_elements: List[Dict[str, Collection[str]]] = []

    for client in client_name_message_map.values():
        node_elements.append(cytoscape_element_from_client(client))
        for user_journey in client.user_journeys:
            for dependency in user_journey.dependencies:
                edge_elements.append(
                    cytoscape_element_from_dependency(dependency))

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


def user_journey_datatable_from_user_journeys(user_journeys, table_id):
    columns = [
        {
            "name": name,
            "id": name,
        } for name in ["User Journey",
                       "Status",
                       "Originating Client"]
    ]
    data = [
        {
            "User Journey":
                utils.relative_name(user_journey.name),
            "Status":
                utils.human_readable_enum_name(user_journey.status,
                                               Status),
            "Originating Client":
                user_journey.client_name,
            "id":
                user_journey.name,
        } for user_journey in user_journeys
    ]
    return dash_table.DataTable(
        # We provide a dict as an id here to utilize the callback
        # pattern matching functionality, since no datatable exists on startup
        id={table_id: table_id},
        columns=columns,
        data=data,
        row_selectable="single",
        style_data_conditional=constants.DATATABLE_CONDITIONAL_STYLE,
    )


def dropdown_options_from_maps(
        node_name_message_map: Dict[str,
                                    Node],
        client_name_message_map: Dict[str,
                                      Client],
        virtual_node_map: Dict[str,
                               VirtualNode]):

    type_labels = ["NODE", "CLIENT", "VIRTUAL NODE"]
    maps: List[Dict[str,
                    Any]] = [
                        node_name_message_map,
                        client_name_message_map,
                        virtual_node_map
                    ]

    options = []

    for type_label, proto_map in zip(type_labels, maps):
        options += [
            {
                "label": f"{type_label}: {name}",
                "value": name,
            } for name in sorted(proto_map.keys())
        ]

    return options


def override_dropdown_options_from_node(node):
    options = [
        {
            "label":
                f"OVERRIDE: {utils.human_readable_enum_name(value_descriptor.number, Status)}",
            "value":
                value_descriptor.number,
        }
        for value_descriptor in Status.DESCRIPTOR.values
        if value_descriptor.number != Status.STATUS_UNSPECIFIED
    ]
    options.append(
        {
            "label":
                f"AUTOMATIC ({utils.human_readable_enum_name(node.status, Status)})",
            "value":
                Status.STATUS_UNSPECIFIED  # this should be zero
        })
    return options


def tag_dropdown_options_from_tags(tags):
    return [{
        "label": tag,
        "value": tag,
    } for tag in tags]


def style_dropdown_options_from_styles(styles):
    return [{
        "label": style,
        "value": style,
    } for style in styles]


def cytoscape_stylesheet_from_style_map(style_map):
    return [
        {
            "selector": f".{style_name}",
            "style": style_value,
        } for style_name,
        style_value in style_map.items()
    ]
