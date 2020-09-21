from .dash_app import cache

from typing import Dict, Tuple, cast

from graph_structures_pb2 import Node, Client

from . import generate_data, utils, compute_status

def clear_cache():
    cache.clear()

@cache.memoize()
def read_local_data() -> Tuple[Dict[str, Node], Dict[str, Client]]:
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
def get_message_maps() -> Tuple[Dict[str, Node], Dict[str, Client]]:
    """ Gets Node and Client protobufs, computes their internal statuses, and return their maps.

    In future versions, the call to read_local_data should be replaced by a RPC call to a reporting server. 

    Returns:
        A tuple of two dictionaries.
        The first dictionary contains a mapping from Node name to the actual Node protobuf message.
        The second dictionary contains a mapping from Client name to the actual Client protobuf message.
    """
    
    message_maps = read_local_data()
    compute_status.compute_statuses(*message_maps)
    
    return message_maps

@cache.memoize()
def get_node_name_message_map() -> Dict[str, Node]:
    """ Gets a dictionary mapping Node names to Node messages.

    Node statuses have already been computed.

    Returns:
        A dictionary mapping Node names to Node messages.
    """

    return get_message_maps()[0]


@cache.memoize()
def get_client_name_message_map() -> Dict[str, Client]:
    """ Gets a dictionary mapping Client names to Client messages.

    User Journey statuses have already been computed. 

    Returns:
        A dictionary mapping Client names to Client messages.
    """
    return get_message_maps()[1]
