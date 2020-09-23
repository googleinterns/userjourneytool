""" Module holding transformer functions.

Transformer functions take a Dash-specific data structure or an intermediate data structure,
make a change, and return the same type of data structure.
"""

from collections import deque, defaultdict

from . import constants, state, utils, converters


def apply_highlighted_edge_class_to_elements(elements, user_journey_name):
    edges_map = defaultdict(list)
    nodes_list = []

    for element in elements:
        if utils.is_node_element(element):
            nodes_list.append(element)
        else:
            # the edge originates from a client, but we want to know 
            # which user journey it is associated with
            if "user_journey_name" in element["data"].keys():
                edges_map[element["data"]["user_journey_name"]].append(element)
            else:
                edges_map[element["data"]["source"]].append(element)

    updated_edges_map = remove_highlighted_class_from_edges(edges_map)

    if user_journey_name:
        updated_edges_map = apply_highlighted_class_to_edges(
            updated_edges_map,
            user_journey_name)

    # Usually, we avoid multiple for clauses in a list comprehension,
    # but this is the canonical way to flattern lists in Python.
    flattened_edges = [edge for edge_list in edges_map.values() for edge in edge_list]

    return flattened_edges + nodes_list


def remove_highlighted_class_from_edges(edges_map):
    """ Removes the highlighted edge class to edges within a specific user journey.

    Args:
        edges_map: A dictionary mapping edge sources to a list of cytoscape elements describing edges originating from the source

    Returns:
        An updated dictionary mapping edge sources to a list of edge cytoscape elements, with the highlighted class removed.
    """

    for edge_list in edges_map.values():
        for edge in edge_list:
            edge["classes"] = ""
    return edges_map


def apply_highlighted_class_to_edges(edges_map, user_journey_name):
    """ Applies the highlighted edge class to edges within a specific user journey.

    Traverses the edges map (gneerated from the elements array) instead of the underlying
    protobufs, in order to easily support virtual nodes.

    Args:
        edges_map: A dictionary mapping edge sources to a list of cytoscape elements describing edges originating from the source
        user_journey_name: The fully qualified user journey name to highlight.

    Returns:
        An updated dictionary mapping edge sources to a list of edge cytoscape elements, with the new highlighted class applied.
    """
    node_frontier_names = deque([user_journey_name])
    while node_frontier_names:
        source_name = node_frontier_names.popleft()
        for edge in edges_map[source_name]:
            edge["classes"] = constants.HIGHLIGHTED_UJ_EDGE_CLASS
            node_frontier_names.append(edge["data"]["target"])

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

    virtual_node_dependency_names = virtual_node_dependency_names.difference(virtual_node_child_names)

    virtual_node_map = state.get_virtual_node_map()
    # This should probably be a proto. We keep it as a dict for now.
    # Should virtual nodes be separate from the Node proto?
    # On one hand, a virtual node can be thought of as a "view" over the graph. 
    # We don't modify the underlying graph structures, only the elements
    # used by Cytoscape to render the graph.
    # On the other hand, we need to do the same status computation with virtual
    # as we do with normal nodes.

    # Also, modifying the set of existing elements is O(V+E), the same as regenerating the graph elements. 
    # Is it cleaner to regenerate the graph elements from scratch?
    # By directly modifying the elements, we can preserve other (stateful) changes made to the elements,
    # such as highlighting a path through the graph.  
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
            if element["data"]["source"] in virtual_node_child_names:
                element["data"]["source"] = virtual_node_name

            if element["data"]["target"] in virtual_node_child_names:
                element["data"]["target"] = virtual_node_name

            # Can't reuse the id of an existing node, delete it so cytoscape gives a new one
            # We avoid making a new element dictionary in order to preserve other properties that 
            # may be in the element, such as classes.
            del element["data"]["id"]
            if element["data"]["source"] != element["data"]["target"]:
                new_elements.append(element)

    return new_elements

def expand_nodes(selected_node_data, elements, active_user_journey_name):
    virtual_node_map = state.get_virtual_node_map()
    for node_data in selected_node_data:
        if node_data["id"] not in virtual_node_map.keys():
            continue

        virtual_node = virtual_node_map[node_data["id"]]


def expand_node(elements, virtual_node):
    pass
    """
    node_name_message_map = state.get_node_name_message_map()
    node_map_subset = {name:node for name, node in node_name_message_map if name in virtual_node["child_names"]}
    elements.append(converters.cytoscape_elements_from_nodes(node_map_subset))
    """
    # add back the nodes
    # reconnect edges ... how to preserve highlighting style?
