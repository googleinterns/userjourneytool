""" Module holding transformer functions.

Transformer functions take an input data structure, make a change, and return an output of the same type.
They are commonly used to perform operations on cytoscape graph elements.
"""

import uuid
from collections import defaultdict, deque
from typing import Any, Dict, Set

from graph_structures_pb2 import NodeType, Status

from . import constants, converters, state, utils


def apply_node_classes(
        elements,
        node_name_message_map,
        client_name_message_map,
        virtual_node_map):
    for element in elements:
        if not utils.is_node_element(element):
            continue

        element_ujt_id = element["data"]["ujt_id"]

        # Should we refactor this into three separate functions -- one for each type of node?
        # Seems like overkill, but would allow us to separate the logic, at the cost of
        # performing iterations over the element list.

        if element_ujt_id in client_name_message_map:
            element["classes"] = constants.CLIENT_CLASS
            continue

        if element_ujt_id in node_name_message_map:
            node = node_name_message_map[element_ujt_id]
        elif element_ujt_id in virtual_node_map:
            node = virtual_node_map[element_ujt_id]
        else:
            raise ValueError

        class_list = [NodeType.Name(node.node_type)]
        if node.override_status != Status.STATUS_UNSPECIFIED:
            class_list += [
                Status.Name(node.override_status),
                constants.OVERRIDE_CLASS
            ]
        else:
            class_list.append(Status.Name(node.status))

        element["classes"] = " ".join(class_list)

    # no return since we directly mutated elements


def apply_views(elements, tag_map, view_list):
    for element in elements:
        element_ujt_id = element["data"]["ujt_id"]
        class_list = []
        if element_ujt_id in tag_map:
            tags = tag_map[element_ujt_id]
            # The following is an O(len(tags) * len(view_list)) operation.
            # Should be okay if these are small lists. We're limited to using lists over dicts or sets
            # since we need to keep a consistent order in the UI.
            # Of course, we could do some preprocessing here to convert them to intermediate dicts.
            # Let's make that optimization later if this turns out to be excessively slow.
            for tag in tags:
                for view_tag, view_style_name in view_list:
                    if tag == view_tag and tag != "":
                        class_list.append(view_style_name)
        element["classes"] += f" {' '.join(class_list)}"


def apply_highlighted_edge_class_to_elements(elements, user_journey_name):
    # we may want to refactor the edge map creation for testability.
    # No other function currently requires us to map edge source to edge element.
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

    # notice that remove/apply highlighted class mutate the edges map
    remove_highlighted_class_from_edges(edges_map)

    if user_journey_name:
        apply_highlighted_class_to_edges(edges_map, user_journey_name)

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
    """

    for edge_list in edges_map.values():
        for edge in edge_list:
            # in the future, if we apply other classes to edges, need to change this to only remove highlighted class.
            edge["classes"] = ""


def apply_highlighted_class_to_edges(edges_map, user_journey_name):
    """ Applies the highlighted edge class to edges within a specific user journey.

    Traverses the edges map (gneerated from the elements array) instead of the underlying
    protobufs, in order to easily support virtual nodes.

    Args:
        edges_map: A dictionary mapping edge sources to a list of cytoscape elements describing edges originating from the source
        user_journey_name: The fully qualified user journey name to highlight.
    """
    node_frontier_names = deque([user_journey_name])
    while node_frontier_names:
        source_name = node_frontier_names.popleft()
        for edge in edges_map[source_name]:
            edge["classes"] = constants.HIGHLIGHTED_UJ_EDGE_CLASS
            node_frontier_names.append(edge["data"]["target"])


def apply_virtual_nodes_to_elements(elements):
    virtual_node_map = state.get_virtual_node_map()
    parent_virtual_node_map = state.get_parent_virtual_node_map()

    new_elements = []
    for element in elements:
        if utils.is_node_element(element):
            highest_collapsed_virtual_node_name = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["ujt_id"],
                virtual_node_map,
                parent_virtual_node_map)
            if highest_collapsed_virtual_node_name is None:
                # not within collapsed node
                if element["data"][
                        "ujt_id"] in parent_virtual_node_map and "parent" not in element[
                            "data"]:
                    element["data"]["parent"] = parent_virtual_node_map[
                        element["data"]["ujt_id"]]
                new_elements.append(element)

        else:
            new_source = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["source"],
                virtual_node_map,
                parent_virtual_node_map)
            new_target = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["target"],
                virtual_node_map,
                parent_virtual_node_map)

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
            virtual_node_name,
            virtual_node_map,
            parent_virtual_node_map)
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


def apply_uuid_to_elements(elements, this_uuid=None):
    """ Append a new UUID to the id of each cytoscape element

    This is used as a workaround to update the source/target of edges, and the parent/child relatioship of nodes.
    In Cytoscape.js, these relationships are immutable, and a move() function has to 
    be called on the element to update the aforementioned properties.
    However, Dash Cytoscape doesn't expose this functionality.
    See https://github.com/plotly/dash-cytoscape/issues/106.
    By providing a new ID, we can avoid this restriction.

    Args:
        elements: a list of Cytoscape elements
        uuid: a UUID to append. Defaults to None. If None is provided, this function generates a new UUID.

    Returns:
        A list of Cytoscape elements with an UUID appended to their ID fields. 
    """
    if this_uuid is None:
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
        # this following is a more elegant solution, but not sure why assignment doesn't work.
        # it seems to be supported in the documentation. This appears to be related to 
        # a similar issue in server.py.

        existing_matching_sli_type_idx = next((idx for idx, node_sli in enumerate(node.slis) if sli.sli_type == node_sli.sli_type), None)
        if existing_matching_sli_type_idx is None:  # we need "is None" condition to support idx = 0 case, this is generally good practice
            node.slis.append(sli)
        else:
            node.slis[existing_matching_sli_type_idx] = sli
        """

    return node_map
