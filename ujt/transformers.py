""" Module holding transformer functions.

Transformer functions take a Dash-specific data structure or an intermediate data structure,
make a change, and return the same type of data structure.
"""

import uuid
from collections import defaultdict, deque
from typing import Any, Dict, Set

from graph_structures_pb2 import NodeType, Status

from . import constants, converters, state, utils


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
    flattened_edges = [
        edge for edge_list in edges_map.values() for edge in edge_list
    ]

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


def apply_virtual_nodes_to_elements(elements):
    virtual_node_map = state.get_virtual_node_map()
    parent_virtual_node_map = state.get_parent_virtual_node_map()

    new_elements = []
    for element in elements:
        if utils.is_node_element(element):
            highest_collapsed_virtual_node_name = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["ujt_id"])
            if highest_collapsed_virtual_node_name is None:
                # not within collapsed node
                if element["data"][
                        "id"] in parent_virtual_node_map and "parent" not in element[
                            "data"]:
                    element["data"]["parent"] = parent_virtual_node_map[
                        element["data"]["ujt_id"]]
                new_elements.append(element)

        else:
            new_source = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["source"])
            new_target = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["target"])

            if new_source is not None:
                element["data"]["source"] = new_source
            if new_target is not None:
                element["data"]["target"] = new_target

            element["data"][
                "id"] = f"{element['data']['source']}/{element['data']['target']}"

            if element["data"]["source"] != element["data"]["target"]:
                new_elements.append(element)

    for virtual_node_name in virtual_node_map:
        highest_collapsed_virtual_node_name = utils.get_highest_collapsed_virtual_node_name(
            virtual_node_name)
        if highest_collapsed_virtual_node_name is None or highest_collapsed_virtual_node_name == virtual_node_name:
            # This if statement determines if the virtual node should be visible
            # first condition: entire stack of virtual nodes is expanded
            # second condition: the virtual node itself is the toplevel, collapsed node
            virtual_node = virtual_node_map[virtual_node_name]
            element = {
                "data":
                    {
                        "label": virtual_node_name,
                        "id": virtual_node_name,
                        "ujt_id": virtual_node_name,
                    },
                "classes":
                    " ".join(
                        [
                            NodeType.Name(NodeType.NODETYPE_VIRTUAL),
                            Status.Name(virtual_node.status),
                        ]),
            }
            if virtual_node_name in parent_virtual_node_map:
                element["data"]["parent"] = parent_virtual_node_map[
                    virtual_node_name]
            new_elements.append(element)

    return new_elements


def apply_uuid(elements):
    """ Append a new UUID to the id of each cytoscape element

    This is used as a workaround to update the source/target of edges, and the parent/child relatioship of nodes.
    In Cytoscape.js, these relationships are immutable, and a move() function has to 
    be called on the element to update the aforementioned properties.
    However, Dash Cytoscape doesn't expose this functionality.
    See https://github.com/plotly/dash-cytoscape/issues/106.
    By providing a new ID, we can avoid this restriction.

    Args:
        elements: a list of Cytoscape elements

    Returns:
        A list of Cytoscape elements with an UUID appended to their ID fields. 
    """
    this_uuid = uuid.uuid4()
    for e in elements:
        e["data"]["id"] += f"#{this_uuid}"
        if "source" in e["data"].keys():
            e["data"]["source"] += f"#{this_uuid}"
        if "target" in e["data"].keys():
            e["data"]["target"] += f"#{this_uuid}"
        if "parent" in e["data"].keys():
            e["data"]["parent"] += f"#{this_uuid}"

    return elements


def apply_slis_to_node_map(sli_list, node_map):
    for sli in sli_list:
        node = node_map[sli.node_name]
        # find the index of the node's SLI with the same SLI type as the SLI from sli_list

        new_node_slis = []

        for node_sli in node.slis:
            if node_sli.sli_type == sli.sli_type:
                new_node_slis.append(sli)
            else:
                new_node_slis.append(node_sli)

        del node.slis[:]
        node.slis.extend(new_node_slis)
        """
        # this is a more elegant solution, but not sure why assignment doesn't work
        existing_matching_sli_type_idx = next((idx for idx, node_sli in enumerate(node.slis) if sli.sli_type == node_sli.sli_type), None)
        if existing_matching_sli_type_idx is None:  # we need "is None" condition to support idx = 0 case, this is generally good practice
            node.slis.append(sli)
        else:
            node.slis[existing_matching_sli_type_idx] = sli
        """

    return node_map
