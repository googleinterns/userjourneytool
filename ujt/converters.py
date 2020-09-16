from typing import Collection, Dict, List

from generated import graph_structures_pb2


def cytoscape_elements_from_services(
        services: List[graph_structures_pb2.Service]):
    """ Converts a list of Service protobufs to a cytoscape graph format.

    Args:
        services: A client of Service protobufs.
    Returns:
        A list of dictionary objects, each containing information regarding a single node (Service) or edge (Dependency).
    """

    parent_nodes: List[Dict[str, Collection[str]]] = []
    child_nodes: List[Dict[str, Collection[str]]] = []
    edges: List[Dict[str, Collection[str]]] = []

    for service in services:
        parent_nodes.append({
            "data": {
                "id": service.name,
                "label": service.name,
            },
            "classes": "service",
        })
        for endpoint in service.endpoints:
            child_nodes.append({
                "data": {
                    "id": endpoint.name,
                    "label": endpoint.name,
                    "parent": service.name,
                }
            })
            for dependency in endpoint.dependencies:
                edges.append({
                    "data": {
                        "source":
                            endpoint.name,
                        "target": (dependency.target_endpoint_name
                                   if dependency.target_endpoint_name else
                                   dependency.target_service_name)
                    }
                })

    return parent_nodes + child_nodes + edges


def cytoscape_elements_from_clients(clients: List[graph_structures_pb2.Client]):
    """ Converts a list of Client protobufs to a cytoscape graph format.

    Args:
        clients: A list of Client protobufs.
    Returns:
        A list of dictionary objects, each containing information regarding a single node (Client) or edge (Dependency).
    """

    nodes: List[Dict[str, Collection[str]]] = []
    edges: List[Dict[str, Collection[str]]] = []

    for client in clients:
        nodes.append({
            "data": {
                "id": client.name,
                "label": client.name,
            },
            "classes": "client",
        })
        for user_journey in client.user_journeys:
            for dependency in user_journey.dependencies:
                edges.append({
                    "data": {
                        "source":
                            client.name,
                        "target": (dependency.target_endpoint_name
                                   if dependency.target_endpoint_name else
                                   dependency.target_service_name)
                    }
                })

    return nodes + edges
