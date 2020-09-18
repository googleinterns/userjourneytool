from typing import Any, Collection, Dict, List, Union

from graph_structures_pb2 import Client, Dependency, Node, NodeType, Status

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
        node_element: Dict[str, Any] = {
            "data": {
                "id": name,
                "label":
                    name.split(".")[-1]  # the node's relative name
            },
            "classes":
                " ".join([
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
        node_elements.append({
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
