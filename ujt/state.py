from typing import Any, Dict, Tuple, cast, List
from collections import deque

from graph_structures_pb2 import Client, Node, SLI

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
    pass


@cache.memoize()
def get_message_maps() -> Tuple[Dict[str, Node], Dict[str, Client]]:
    """ Gets Node and Client protobufs, computes their internal statuses, and return their maps.

    In future versions, the call to get_local_topology should be replaced by a RPC call to a reporting server. 

    Returns:
        A tuple of two dictionaries.
        The first dictionary contains a mapping from Node name to the actual Node protobuf message.
        The second dictionary contains a mapping from Client name to the actual Client protobuf message.
    """

    message_maps = get_local_topology()

    """
    slis = get_slis()
    # apply slis to protobufs in message maps
    """

    compute_status.compute_statuses(*message_maps)

    return message_maps


def get_node_name_message_map() -> Dict[str, Node]:
    """ Gets a dictionary mapping Node names to Node messages.

    Node statuses have already been computed.

    Returns:
        A dictionary mapping Node names to Node messages.
    """

    return get_message_maps()[0]


def get_client_name_message_map() -> Dict[str, Client]:
    """ Gets a dictionary mapping Client names to Client messages.

    User Journey statuses have already been computed. 

    Returns:
        A dictionary mapping Client names to Client messages.
    """
    return get_message_maps()[1]


def get_virtual_node_map() -> Dict[str, Any]:
    """ Gets a dictionary mapping virtual node names to virtual node objects.

    Virtual node objects are currently dictionaries with the keys:
        name
        child_names
        collapsed

    THe exact implementation of virtual node objects may change to a UJT specific class, or a new proto.

    Returns:
        A dictionary mapping virtual node names to virtual node objects.
    """
    return cache.get("virtual_node_map")


def set_virtual_node_map(virtual_node_map: Dict[str, Any]):
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


def add_virtual_node(virtual_node_name: str, selected_node_data: Dict[str, Any]):
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

    virtual_node_child_names = set()
    node_frontier = deque()  # use this queue to do BFS to flatten non-virtual nodes
    for node_data in selected_node_data:
        if node_data["id"] in virtual_node_map:  # nested virtual node
            virtual_node_child_names.add(node_data["id"])
            parent_virtual_node_map[node_data["id"]] = virtual_node_name
        else:
            node_frontier.append(node_name_message_map[node_data["id"]])
          
    while node_frontier:
        node = node_frontier.popleft()
        virtual_node_child_names.add(node.name)
        parent_virtual_node_map[node.name] = virtual_node_name
        for child_name in node.child_names:
            node_frontier.append(node_name_message_map[child_name])

    virtual_node = {
        "name": virtual_node_name,
        "child_names": virtual_node_child_names,
        "collapsed": True,
    }
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
    for child_name in virtual_node["child_names"]:
        del parent_virtual_node_map[child_name]

    del virtual_node_map[virtual_node_name]

    set_virtual_node_map(virtual_node_map)
    set_parent_virtual_node_map(parent_virtual_node_map)


def set_virtual_node_collapsed_state(virtual_node_name: str, collapsed: bool):
    """ Sets the collapsed state of a virtual node.

    Updates the corresponding virtual node object within the virtual node map.

    Args:
        virutal_node_name: The name of the virtual node to update.
        collapsed: The new collapsed 
    """
    virtual_node_map = get_virtual_node_map()
    virtual_node = virtual_node_map[virtual_node_name]
    virtual_node["collapsed"] = collapsed
    set_virtual_node_map(virtual_node_map)