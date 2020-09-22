""" Module holding transformer functions.

Transformer functions take a Dash-specific data structure or an intermediate data structure,
make a change, and return the same type of data structure.
"""

from collections import deque

from . import constants, state


def apply_highlighted_edge_class_to_elements(elements, user_journey_name):
    edges_map = {}
    nodes_list = []

    for element in elements:
        element_data = element["data"]
        if "source" in element_data.keys():
            edges_map[(element_data["source"],
                       element_data["target"])] = element
        else:
            nodes_list.append(element)

    updated_edges_map = remove_highlighted_class_from_edges(edges_map)

    if user_journey_name:
        updated_edges_map = apply_highlighted_class_to_edges(
            updated_edges_map,
            user_journey_name)

    return list(updated_edges_map.values()) + nodes_list


def remove_highlighted_class_from_edges(edges_map):
    for edge in edges_map.values():
        edge["classes"] = ""
    return edges_map


def apply_highlighted_class_to_edges(edges_map, user_journey_name):
    node_name_message_map, client_name_message_map = state.get_message_maps()
    client_name = user_journey_name.split(".")[0]
    client = client_name_message_map[client_name]
    user_journey = next(
        user_journey for user_journey in client.user_journeys
        if user_journey.name == user_journey_name)

    node_frontier = deque()

    # add the initial set of nodes to the frontier
    for dependency in user_journey.dependencies:
        node_frontier.append(node_name_message_map[dependency.target_name])
        edges_map[(client_name,
                   dependency.target_name
                  )]["classes"] = constants.HIGHLIGHTED_UJ_EDGE_CLASS

    while node_frontier:
        node = node_frontier.pop()
        for dependency in node.dependencies:
            node_frontier.append(node_name_message_map[dependency.target_name])
            edges_map[(node.name,
                       dependency.target_name
                      )]["classes"] = constants.HIGHLIGHTED_UJ_EDGE_CLASS

    return edges_map
