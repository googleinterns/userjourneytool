""" Module holding transformer functions.

Transformer functions take a Dash-specific data structure or an intermediate data structure,
make a change, and return the same type of data structure.
"""

from collections import deque, defaultdict

from . import constants, state, utils, converters

from typing import Set, Dict, Any

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


def add_virtual_node(virtual_node_name, selected_node_data):
    virtual_node_map = state.get_virtual_node_map()
    parent_virtual_node_map = state.get_parent_virtual_node_map()
    node_name_message_map = state.get_node_name_message_map()

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

    state.set_virtual_node_map(virtual_node_map)
    state.set_parent_virtual_node_map(parent_virtual_node_map)


def delete_virtual_node(virtual_node_name):
    virtual_node_map = state.get_virtual_node_map()
    parent_virtual_node_map = state.get_parent_virtual_node_map()

    virtual_node = virtual_node_map[virtual_node_name]
    for child_name in virtual_node["child_names"]:
        del parent_virtual_node_map[child_name]

    del virtual_node_map[virtual_node_name]

    state.set_virtual_node_map(virtual_node_map)
    state.set_parent_virtual_node_map(parent_virtual_node_map)


def set_virtual_node_collapsed_state(virtual_node_name, collapsed):
    virtual_node_map = state.get_virtual_node_map()
    virtual_node = virtual_node_map[virtual_node_name]
    virtual_node["collapsed"] = collapsed
    state.set_virtual_node_map(virtual_node_map)



def get_highest_collapsed_virtual_node_name(node_name):
    virtual_node_map = state.get_virtual_node_map()
    parent_virtual_node_map = state.get_parent_virtual_node_map()

    current_name = node_name
    highest_collapsed_name = None

    while current_name in parent_virtual_node_map:
        if current_name in virtual_node_map and virtual_node_map[current_name]["collapsed"]:
            highest_collapsed_name = current_name
        current_name = parent_virtual_node_map[current_name]

    # need this for the highest-level (last) virtual node, which isn't registered
    # in the parent_virtual_node_map.
    if current_name in virtual_node_map and virtual_node_map[current_name]["collapsed"]:
        highest_collapsed_name = current_name

    return highest_collapsed_name

def apply_virtual_nodes_to_elements(elements):
    virtual_node_map = state.get_virtual_node_map()
    parent_virtual_node_map = state.get_parent_virtual_node_map()

    new_elements = []
    for element in elements:
        if utils.is_node_element(element):
            highest_collapsed_virtual_node_name = get_highest_collapsed_virtual_node_name(element["data"]["id"])
            if highest_collapsed_virtual_node_name is None:
                # not within collapsed node
                if element["data"]["id"] in parent_virtual_node_map and "parent" not in element["data"]:
                    element["data"]["parent"] = parent_virtual_node_map[element["data"]["id"]]
                new_elements.append(element)

        else: 
            new_source = get_highest_collapsed_virtual_node_name(element["data"]["source"])
            new_target = get_highest_collapsed_virtual_node_name(element["data"]["target"])
            if new_source is not None:
                element["data"]["source"] = new_source
            if new_target is not None:
                element["data"]["target"] = new_target
            try:
                del element["data"]["id"]
            except:
                pass
            if element["data"]["source"] != element["data"]["target"]:
                new_elements.append(element)

    for virtual_node_name in virtual_node_map:
        highest_collapsed_virtual_node_name = get_highest_collapsed_virtual_node_name(virtual_node_name)
        if highest_collapsed_virtual_node_name is None or highest_collapsed_virtual_node_name == virtual_node_name:
            # This if statement determines if the virtual node should be visible
            # first condition: entire stack of virtual nodes is expanded
            # second condition: the virtual node itself is the toplevel, collapsed node
            print("hello")
            element = {
                "data": {
                    "label": virtual_node_name,
                    "id": virtual_node_name,
                },
                "classes": constants.VIRTUAL_NODE_CLASS,
            }
            if virtual_node_name in parent_virtual_node_map:
                element["data"]["parent"] = parent_virtual_node_map[virtual_node_name]
            new_elements.append(element)
    print(new_elements)
    return new_elements
"""
def collapse_nodes(virtual_node_name, selected_node_data, elements):
    virtual_node_child_names = set()
    node_name_message_map = state.get_node_name_message_map()
    node_frontier = deque([node_name_message_map[node_data["id"]] for node_data in selected_node_data])
    
    while node_frontier:
        node = node_frontier.popleft()
        virtual_node_child_names.add(node.name)
        for child_name in node.child_names:
            node_frontier.append(node_name_message_map[child_name])

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
    }
    state.set_virtual_node_map(virtual_node_map)

    # A simpler approach to collapse/expand virtual nodes is to keep track of
    # the elements that are added/removed when a node is collapsed/expanded.
    # However, dicts are unhashable and can't be placed in sets, so we need a workaround.
    # Added:
    #   The virtual node itself
    #   Edges to the virtual node
    # Removed:
    #   The nodes within the virtual node
    #   The edges within the virutal node
    
    new_elements = [
        {
            "data": {
                "label": virtual_node_name,
                "id": virtual_node_name,
            },
            "classes": constants.VIRTUAL_NODE_CLASS
        },
    ]
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
    node_name_message_map = state.get_node_name_message_map()
    
    new_elements = []
    for element in elements:
        if utils.is_node_element(element):
            if element["data"]["id"] in node_name_message_map:
                pass
            else:
                pass
        else:
            if element["data"]["target"] != virtual_node["name"] and element["data"]["source"] != virtual_node["name"]:
                new_elements.append(element)
"""