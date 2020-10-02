from collections import defaultdict
from typing import TYPE_CHECKING, Dict

from graph_structures_pb2 import SLI, Client, Node, Status

if TYPE_CHECKING:
    from graph_structures_pb2 import \
        StatusValue  # pylint: disable=no-name-in-module  # pragma: no cover


def reset_node_statuses(node_name_message_map):
    for node in node_name_message_map.values():
        node.status = Status.STATUS_UNSPECIFIED


def reset_client_statuses(client_name_message_map):
    for client in client_name_message_map.values():
        for user_journey in client.user_journeys:
            user_journey.status = Status.STATUS_UNSPECIFIED


def compute_statuses(
        node_name_message_map: Dict[str,
                                    Node],
        client_name_message_map: Dict[str,
                                      Client]):
    """ Annotates Node status based on their dependencies.

    Args:
        node_name_message_map: A dictionary mapping Node names to their corresponding Node protobuf message.
        client_name_message_map: A dictionary mapping Client names to the corresponding Client protobuf message.
    """

    # starting at the clients, perform a DFS through the graph.
    # update the node's status before popping a stack frame.
    # not strictly required to start at clients, but more efficient and easier to think about
    for client in client_name_message_map.values():
        for user_journey in client.user_journeys:
            status_count_map: Dict["StatusValue", int] = defaultdict(int)
            for dependency in user_journey.dependencies:
                status_count_map[compute_single_node_status(
                    node_name_message_map,
                    dependency.target_name)] += 1
            user_journey.status = compute_status_from_count_map(
                status_count_map)

    # annotate remaining nodes (those not connected as part of a user journey)
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

    if node.status != Status.STATUS_UNSPECIFIED:  # if the current node's status was already computed
        return node.status

    status_count_map: Dict["StatusValue", int] = defaultdict(int)
    for child_name in node.child_names:
        status_count_map[compute_single_node_status(
            node_name_message_map,
            child_name)] += 1

    try:
        for dependency in node.dependencies:
            status_count_map[compute_single_node_status(
                node_name_message_map,
                dependency.target_name)] += 1
    except AttributeError:
        pass

    try:
        for sli in node.slis:
            status_count_map[compute_sli_status(sli)] += 1
    except AttributeError:
        pass

    node.status = compute_status_from_count_map(status_count_map)

    if node.override_status != Status.STATUS_UNSPECIFIED:  # if the current node's status was manually overwritten
        # notice we place this at the end, since we still want to compute the node's status
        # to display in the dropdown menu (regardless of the override)
        return node.override_status

    return node.status


def compute_status_from_count_map(status_count_map):
    if status_count_map[Status.STATUS_ERROR] > 0:
        return Status.STATUS_ERROR
    elif status_count_map[Status.STATUS_WARN] > 0:
        return Status.STATUS_WARN
    else:
        return Status.STATUS_HEALTHY


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
