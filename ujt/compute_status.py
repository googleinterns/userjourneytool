from collections import defaultdict
from typing import TYPE_CHECKING, Dict

from graph_structures_pb2 import SLI, Client, Node, Status

if TYPE_CHECKING:
    from graph_structures_pb2 import \
        StatusValue  # pylint: disable=no-name-in-module


def compute_node_statuses(
        node_name_message_map: Dict[str,
                                    Node],
        client_name_message_map: Dict[str,
                                      Client]):
    """ Annotates Node status based on their dependencies.

    Args:
        node_name_message_map: A dictionary mapping Node names to their corresponding Node protobuf message.
        client_name_message_map: A dictionary mapping Client names to the corresponding Client protobuf message.
    """

    # initially mark all nodes as unspecified
    for node in node_name_message_map.values():
        node.status = Status.STATUS_UNSPECIFIED

    # starting at the clients, perform a DFS through the graph.
    # update the node's status before popping a stack frame.
    # not strictly required to start at clients, but more efficient and easier to think about
    for client in client_name_message_map.values():
        for user_journey in client.user_journeys:
            for dependency in user_journey.dependencies:
                compute_single_node_status(
                    node_name_message_map,
                    dependency.target_name)

    # annottate remaining nodes (those not connected as part of a user journey)
    for node in node_name_message_map.values():
        if node.status == Status.STATUS_UNSPECIFIED:
            compute_single_node_status(node_name_message_map, node.name)


def compute_single_node_status(
        node_name_message_map: Dict[str,
                                    Node],
        node_name: str) -> "StatusValue":
    """ Annotates and returns the status of a single Node based on its dependencies. 

    Args:
        node_name_message_map: A dictionary mapping Node names to their corresponding Node protobuf message.
        node_name: The name of the node to annotate.

    Returns:
        The status of the annotated node.
    """

    node = node_name_message_map[node_name]
    if node.status != Status.STATUS_UNSPECIFIED:
        return node.status

    status_count_map: Dict["StatusValue", int] = defaultdict(int)
    for child_name in node.child_names:
        status_count_map[compute_single_node_status(
            node_name_message_map,
            child_name)] += 1

    for dependency in node.dependencies:
        status_count_map[compute_single_node_status(
            node_name_message_map,
            dependency.target_name)] += 1

    for sli in node.slis:
        status_count_map[compute_sli_status(sli)] += 1

    if status_count_map[Status.STATUS_ERROR] > 0:
        status_value = Status.STATUS_ERROR
    elif status_count_map[Status.STATUS_WARN] > 0:
        status_value = Status.STATUS_WARN
    else:
        status_value = Status.STATUS_HEALTHY

    node.status = status_value
    return status_value


def compute_sli_status(sli: SLI) -> "StatusValue":
    """ Annotates and returns the status of a SLI based on its values. 

    If the sli value is in the range (warn_lower_bound, warn_upper_bound), the its status is healthy.
    If the sli value is in the range (error_lower_bound, error_upper_bound), the its status is warn.
    Otherwise, its status is error.

    Args:
        sli: A SLI message.

    Returns:
        The status of the annotated SLI.
    """
    if sli.slo_warn_lower_bound < sli.sli_value < sli.slo_warn_upper_bound:
        status_value = Status.STATUS_HEALTHY
    elif sli.slo_error_lower_bound < sli.sli_value < sli.slo_error_upper_bound:
        status_value = Status.STATUS_WARN
    else:
        status_value = Status.STATUS_ERROR

    sli.status = status_value
    return status_value
