from collections import deque
from typing import Any, Deque, Dict, List, Set, Tuple, cast

from graph_structures_pb2 import SLI, Client, Node, NodeType, VirtualNode

from . import compute_status, generate_data, utils
from .dash_app import cache


def clear_cache():
    cache.clear()


@cache.memoize()
def get_local_topology() -> Tuple[Dict[str, Node], Dict[str, Client]]:
    """ Reads protobufs in text format from ../data directory into protobuf objects.

    This is simply used as a proof-of-concept/test implementation. 
    In actual usage, this method should not be used. Instead, protobufs should be read from a reporting server.
    This is highly coupled with implementation of mock data storage conventions.

    Returns:
        A tuple of two dictionaries.
        The first dictionary contains a mapping from Node name to the actual Node protobuf message.
        The second dictionary contains a mapping from Client name to the actual Client protobuf message.
    """

    service_names = generate_data.SERVICE_ENDPOINT_NAME_MAP.keys()
    client_names = generate_data.CLIENT_USER_JOURNEY_NAME_MAP.keys()

    flattened_endpoint_names = []
    for service_name, endpoint_names in generate_data.SERVICE_ENDPOINT_NAME_MAP.items(
    ):
        flattened_endpoint_names += [
            f"{service_name}.{endpoint_name}"
            for endpoint_name in endpoint_names
        ]

    node_names = list(service_names) + flattened_endpoint_names

    node_name_message_map: Dict[str,
                                Node] = {
                                    name: cast(
                                        Node,
                                        utils.read_proto_from_file(
                                            utils.named_proto_file_name(
                                                name,
                                                Node),
                                            Node,
                                        ))
                                    for name in node_names
                                }

    client_name_message_map: Dict[str,
                                  Client] = {
                                      name: cast(
                                          Client,
                                          utils.read_proto_from_file(
                                              utils.named_proto_file_name(
                                                  name,
                                                  Client),
                                              Client))
                                      for name in client_names
                                  }

    return node_name_message_map, client_name_message_map


@cache.memoize()
def get_slis() -> List[SLI]:
    """ Gets a list of updated SLIs.

    Returns:
        A list of SLIs.
    """

    # Should read from remote server here.
    print("Get SLIs")
    return []


def get_message_maps() -> Tuple[Dict[str, Node], Dict[str, Client]]:
    """ Gets Node and Client protobufs, computes their internal statuses, and return their maps.

    In future versions, the call to get_local_topology should be replaced by a RPC call to a reporting server. 

    Returns:
        A tuple of two dictionaries.
        The first dictionary contains a mapping from Node name to the actual Node protobuf message.
        The second dictionary contains a mapping from Client name to the actual Client protobuf message.
    """
    node_name_message_map = cache.get("node_name_message_map")
    client_name_message_map = cache.get("client_name_message_map")

    if node_name_message_map is None or client_name_message_map is None:
        # Put topology loading here for now. We may want to refactor this (?)
        node_name_message_map, client_name_message_map = get_local_topology()
        cache.set("node_name_message_map", node_name_message_map)
        cache.set("client_name_message_map", client_name_message_map)

    return node_name_message_map, client_name_message_map


def get_node_name_message_map() -> Dict[str, Node]:
    """ Gets a dictionary mapping Node names to Node messages.

    Returns:
        A dictionary mapping Node names to Node messages.
    """

    return get_message_maps()[0]


def set_node_name_message_map(node_name_message_map):
    return cache.set("node_name_message_map", node_name_message_map)


def get_client_name_message_map() -> Dict[str, Client]:
    """ Gets a dictionary mapping Client names to Client messages.

    Returns:
        A dictionary mapping Client names to Client messages.
    """
    return get_message_maps()[1]


def set_client_name_message_map(client_name_message_map):
    cache.set("client_name_message_map", client_name_message_map)


def get_virtual_node_map() -> Dict[str, VirtualNode]:
    """ Gets a dictionary mapping virtual node names to virtual node messages.

    Returns:
        A dictionary mapping virtual node names to virtual node objects.
    """
    return cache.get("virtual_node_map")


def set_virtual_node_map(virtual_node_map: Dict[str, VirtualNode]):
    """ Sets a dictionary mapping virtual node names to virtual node objects.
    
    Args:
        virutal_node_map: The new virtual node map to be saved in the cache.
    """
    cache.set("virtual_node_map", virtual_node_map)


def get_parent_virtual_node_map() -> Dict[str, str]:
    """ Gets a dictionary mapping node names to the name of their direct virtual node parent.

    The keys of the dictionary can be names of virtual and non-virtual nodes.
    The values are always virtual nodes. 
    This dictionary can be used to re-construct the chain of the virtual nodes that contain a given node. 

    Returns:
        A dictionary mapping node names to the name of their direct virtual node parent.
    """
    return cache.get("parent_virtual_node_map")


def set_parent_virtual_node_map(parent_virtual_node_map: Dict[str, str]):
    """ Sets a dictionary mapping node names to the name of their direct virtual node parent.
    
    Args:
        parent_virutal_node_map: The new parent virtual node map to be saved in the cache.
    """
    cache.set("parent_virtual_node_map", parent_virtual_node_map)


def add_virtual_node(
    virtual_node_name: str,
    selected_node_data: List[Dict[str,
                                  Any]],
):
    """ Adds a virtual node.

    Updates the virtual node map with the newly created virtual node object.
    Updates the entries in the parent virtual node map corresponding to the virtual node's children,
    to point to the new virtual node.

    The interface could be refactored to take node_names instead of selected_node_data to be cleaner.
    However, this function is currently only called in the callback to update the elements of the cytoscape graph.
    It would be an extraneous transformation that doesn't offer any additional convenience or benefit, currently.

    Args:
        virutal_node_name: The name of the virtual node to create.
        selected_node_data: A list of node data dictionaries to include in the virtual node.

    """
    virtual_node_map = get_virtual_node_map()
    parent_virtual_node_map = get_parent_virtual_node_map()
    node_name_message_map = get_node_name_message_map()

    virtual_node_child_names: Set[str] = set()
    # use this queue to do BFS to flatten non-virtual nodes
    node_frontier: Deque[Node] = deque()
    for node_data in selected_node_data:
        if node_data["ujt_id"] in virtual_node_map:  # nested virtual node
            virtual_node_child_names.add(node_data["ujt_id"])
            parent_virtual_node_map[node_data["ujt_id"]] = virtual_node_name
        else:
            node_frontier.append(node_name_message_map[node_data["ujt_id"]])

    while node_frontier:
        node = node_frontier.popleft()
        virtual_node_child_names.add(node.name)
        parent_virtual_node_map[node.name] = virtual_node_name
        for child_name in node.child_names:
            node_frontier.append(node_name_message_map[child_name])

    virtual_node = VirtualNode(
        name=virtual_node_name,
        child_names=virtual_node_child_names,
        collapsed=True,
        node_type=NodeType.NODETYPE_VIRTUAL,
    )
    virtual_node_map[virtual_node_name] = virtual_node

    set_virtual_node_map(virtual_node_map)
    set_parent_virtual_node_map(parent_virtual_node_map)


def delete_virtual_node(virtual_node_name: str):
    """ Deletes a virtual node.

    Updates the virtual node map to remove the corresponding virtual node object.
    Updates the entries in the parent virtual node map corresponding to the virtual node's children,
    to no longer point to the new virtual node.

    Args:
        virutal_node_name: The name of the virtual node to delete.
    """
    virtual_node_map = get_virtual_node_map()
    parent_virtual_node_map = get_parent_virtual_node_map()

    virtual_node = virtual_node_map[virtual_node_name]
    # child_names property is convenient but not strictly necessary.
    for child_name in virtual_node.child_names:
        del parent_virtual_node_map[child_name]

    del virtual_node_map[virtual_node_name]

    set_virtual_node_map(virtual_node_map)
    set_parent_virtual_node_map(parent_virtual_node_map)


def set_virtual_node_collapsed_state(virtual_node_name: str, collapsed: bool):
    """ Sets the collapsed state of a virtual node.

    Updates the corresponding virtual node object within the virtual node map.

    Args:
        virutal_node_name: The name of the virtual node to update.
        collapsed: The new collapsed state
    """
    virtual_node_map = get_virtual_node_map()
    virtual_node = virtual_node_map[virtual_node_name]
    virtual_node.collapsed = collapsed
    set_virtual_node_map(virtual_node_map)
