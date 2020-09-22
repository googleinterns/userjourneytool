""" Module holding transformer functions.

Transformer functions take a Dash-specific data structure or an intermediate data structure,
make a change, and return the same type of data structure.
"""

from collections import deque

from . import constants, state, utils


def apply_highlighted_edge_class_to_elements(elements, user_journey_name):
    edges_map = {}
    nodes_list = []

    for element in elements:
        if utils.is_node_element(element):
            nodes_list.append(element)
        else:
            edges_map[(element["data"]["source"],
                       element["data"]["target"])] = element

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
        node = node_frontier.popleft()
        for dependency in node.dependencies:
            node_frontier.append(node_name_message_map[dependency.target_name])
            edges_map[(node.name,
                       dependency.target_name
                      )]["classes"] = constants.HIGHLIGHTED_UJ_EDGE_CLASS

    return edges_map


def collapse_nodes(virtual_node_name, selected_node_data, elements):
    virtual_node_child_names, virtual_node_dependency_names = set(), set()
    node_name_message_map = state.get_node_name_message_map()
    node_frontier = deque([node_name_message_map[node_data["id"]] for node_data in selected_node_data])
    
    while node_frontier:
        node = node_frontier.popleft()
        virtual_node_child_names.add(node.name)
        for dependency in node.dependencies:
            virtual_node_dependency_names.add(dependency.target_name)
        for child_name in node.child_names:
            node_frontier.append(node_name_message_map[child_name])

    print(virtual_node_child_names)

    virtual_node_dependency_names = virtual_node_dependency_names.difference(virtual_node_child_names)

    virtual_node_map = state.get_virtual_node_map()
    # can this be a special Node proto?
    # at the minimum, this should be a new proto. We keep it as a dict for now.
    virtual_node_map[virtual_node_name] = {
        "name": virtual_node_name,
        "child_names": virtual_node_child_names,
        "dependency_names": virtual_node_dependency_names,
    }
    state.set_virtual_node_map(virtual_node_map)

    new_elements = [{
        "data": {
            "label": virtual_node_name,
            "id": virtual_node_name,
        },
        "classes": constants.VIRTUAL_NODE_CLASS
    }]
    for element in elements:
        if utils.is_node_element(element):
            if element["data"]["id"] not in virtual_node_child_names:
                new_elements.append(element)
        else:
            source_name, target_name = element["data"]["source"], element["data"]["target"]
            if source_name in virtual_node_child_names and target_name in virtual_node_child_names:
                continue

            new_elements.append({
                "data": {
                    "source": virtual_node_name if source_name in virtual_node_child_names else source_name,
                    "target": virtual_node_name if target_name in virtual_node_child_names else target_name,
                }
            })
    
    return new_elements