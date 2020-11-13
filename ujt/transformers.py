""" Module holding transformer functions.

Transformer functions take an input data structure, make a change, and return an output of the same type.
They are commonly used to perform operations on cytoscape graph elements.
"""

import copy
import datetime as dt
import uuid
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Tuple

from graph_structures_pb2 import SLI, NodeType, Status

from . import compute_status, constants, state, utils


def apply_node_property_classes(
    elements, node_name_message_map, client_name_message_map, virtual_node_map
):
    """Adds classes to elements based on the properties of their corresponding nodes.

    Currently, these properties include:
        if the element corresponds to a client
        the overall status of a node or virtual node
        the override status of a node or virtual node

    Args:
        elements: A list of cytoscape elements
        node_name_message_map: A dictionary mapping node names to Node protos.
        client_name_message_map: A dictionary mapping client names to Client protos.
        virtual_node_map: A dictionary mapping virtual node names to VirtualNode protos.

    Returns:
        a new list of elements with appropriate cytoscape classes.
    """
    out_elements = []

    for element in elements:
        new_element = copy.deepcopy(element)

        # edge element
        if not utils.is_node_element(new_element):
            out_elements.append(new_element)
            continue

        element_ujt_id = new_element["data"]["ujt_id"]

        # client
        if element_ujt_id in client_name_message_map:
            utils.add_class_mutable(new_element, [constants.CLIENT_CLASS])
            out_elements.append(new_element)
            continue

        # nodes
        if element_ujt_id in node_name_message_map:
            node = node_name_message_map[element_ujt_id]
        elif element_ujt_id in virtual_node_map:
            node = virtual_node_map[element_ujt_id]
        else:
            raise ValueError(
                "Cytoscape element not found in node maps -- some data is corrupt!"
            )

        class_list = [NodeType.Name(node.node_type)]
        if node.override_status != Status.STATUS_UNSPECIFIED:
            class_list += [Status.Name(node.override_status), constants.OVERRIDE_CLASS]
        else:
            class_list.append(Status.Name(node.status))

        utils.add_class_mutable(new_element, class_list)
        out_elements.append(new_element)

    return out_elements


def apply_view_classes(elements, tag_map, view_list):
    """Applies classes to elements based on the user defined tags and views.

    The stylesheet is updated upon every style update.
    Given a view composed of a tag and style name, we change
    the actual appearance of elements, by appending the style name
    to all elements tagged with the tag.

    Notice that the tag name itself is not appended to the class list.

    Args:
        elements: A list of cytoscape elements.
        tag_map: A dictionary mapping element_ujt_ids to a list of applied tags
        view_list: The list of user defined views.

    Returns:
        a list of cytoscape elements with view classes applied.
    """
    out_elements = []
    for element in elements:
        new_element = copy.deepcopy(element)
        element_ujt_id = new_element["data"]["ujt_id"]
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
                    if tag == view_tag and tag != "" and view_style_name != "":
                        class_list.append(view_style_name)
        utils.add_class_mutable(new_element, class_list)
        out_elements.append(new_element)

    return out_elements


def apply_change_over_time_classes(
    elements: List[Dict[str, Any]],
    slis: List[SLI],
    start_time: dt.datetime,
    end_time: dt.datetime,
) -> List[Dict[str, Any]]:
    """Applies classes to elements based on the change in SLIs over the time range.

    Args:
        elements: A list of cytoscape elements.
        slis: A list of SLI protos.
        start_time: The start time of the time range to compute aggregate status over.
        end_time: The end time of the time range to compute aggregate status over.
        sli_type: The SLI type of interest.

    Returns:
        A new list of elements with the change over time classes applied.
    """

    node_name_sli_map = defaultdict(list)
    for sli in slis:
        node_name_sli_map[sli.node_name].append(sli)

    out_elements = []
    for element in elements:
        new_element = copy.deepcopy(element)
        ujt_id = new_element["data"]["ujt_id"]
        if ujt_id in node_name_sli_map:
            (
                before_composite_sli,
                after_composite_sli,
            ) = generate_before_after_composite_slis(
                node_name_sli_map[ujt_id],
                start_time,
                end_time,
            )
            change_over_time_class = (
                utils.get_change_over_time_class_from_composite_slis(
                    before_composite_sli,
                    after_composite_sli,
                )
            )
            utils.add_class_mutable(new_element, [change_over_time_class])

        out_elements.append(new_element)

    return out_elements


def generate_before_after_composite_slis(
    slis: List[SLI], start_time: dt.datetime, end_time: dt.datetime
) -> Tuple[Optional[SLI], Optional[SLI]]:
    """Generates two composite SLIs from the slis in each half of the specified time range.

    The composite SLI's value is the average of the individual SLI values in the appropriate range.

    Args:
        slis: A list of SLIs within the tine range
        start_time: The start of the time range
        end_time: The end of the time range

    Returns:
        A tuple of two composite SLIs. It will never return (None, None)
    """
    if slis == []:
        raise ValueError

    mid_time = start_time + (end_time - start_time) / 2
    slis_before, slis_after = [], []
    for sli in slis:
        if sli.timestamp.ToDatetime() < mid_time:
            slis_before.append(sli)
        else:
            slis_after.append(sli)

    # Compute the average value before and after min_time, and note the appropriate class
    composite_slis: List[Optional[SLI]] = [None, None]
    for idx, sli_sublist in enumerate([slis_before, slis_after]):
        if sli_sublist != []:
            composite_sli = SLI()
            # copy the slo bound/target values from the input,
            # these should be constant across all slis in the input list
            composite_sli.CopyFrom(sli_sublist[0])
            # compute the average value, this can be more sophisticated
            composite_sli.sli_value = sum([sli.sli_value for sli in sli_sublist]) / len(
                sli_sublist
            )
            compute_status.compute_sli_status(composite_sli)

            composite_slis[idx] = composite_sli

    return (composite_slis[0], composite_slis[1])  # explicitly return as a tuple


def apply_highlighted_edge_class_to_elements(elements, user_journey_name):
    """Applies the highlighted edge class to elements based on the selected user journey.

    Args:
        elements: a list of cytoscape elements
        user_journey_name: the user journey to highlight

    Returns:
        a list of cytoscape elements with the highlighted class on the appropriate edges
    """

    edges_map = defaultdict(list)  # map from edge source to edge elements
    nodes_list = []
    for element in elements:
        new_element = copy.deepcopy(element)
        if utils.is_node_element(new_element):
            nodes_list.append(new_element)
        else:
            if "user_journey_name" in new_element["data"].keys():
                # treat the user journey name as the edge source
                edges_map[new_element["data"]["user_journey_name"]].append(new_element)
            else:
                edges_map[new_element["data"]["source"]].append(new_element)

    # do a bfs traversal and highlight the appropriate edges
    node_frontier_names = deque([user_journey_name])
    while node_frontier_names:
        source_name = node_frontier_names.popleft()
        for edge in edges_map[source_name]:
            utils.add_class_mutable(edge, [constants.HIGHLIGHTED_UJ_EDGE_CLASS])
            node_frontier_names.append(edge["data"]["target"])

    out_elements = nodes_list
    for edges in edges_map.values():
        out_elements += edges

    return out_elements


def apply_virtual_nodes_to_elements(elements):
    """Applies the virtual node transformation to elements.

    This is done in two steps:
        1. modifying the existing elements by:
            a. removing the elements that should be hidden by a collapsed virtual node
            b. adding the parent property to elements that are in an expanded virtual node
            c. modifying edges to connect collapsed virtual nodes
        2. adding in the expanded or top-level virtual nodes that should be visible

    Args:
        elements: a list of cytoscape elements
    """
    virtual_node_map = state.get_virtual_node_map()
    parent_virtual_node_map = state.get_parent_virtual_node_map()

    out_elements = []
    # 1. modify existing elements
    for element in elements:
        new_element = copy.deepcopy(element)

        if utils.is_node_element(new_element):
            highest_collapsed_virtual_node_name = (
                utils.get_highest_collapsed_virtual_node_name(
                    new_element["data"]["ujt_id"],
                    virtual_node_map,
                    parent_virtual_node_map,
                )
            )
            # this condition checks if the node should be visible
            if highest_collapsed_virtual_node_name is None:
                # this condition checks if the current node is not within
                # a compound node, but should be contained within a virutal node.
                if (
                    new_element["data"]["ujt_id"] in parent_virtual_node_map
                    and "parent" not in new_element["data"]
                ):
                    new_element["data"]["parent"] = parent_virtual_node_map[
                        new_element["data"]["ujt_id"]
                    ]
                out_elements.append(new_element)

        else:
            new_source = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["source"], virtual_node_map, parent_virtual_node_map
            )
            new_target = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["target"], virtual_node_map, parent_virtual_node_map
            )

            if new_source is not None:
                new_element["data"]["source"] = new_source
            if new_target is not None:
                new_element["data"]["target"] = new_target

            new_element["data"][
                "id"
            ] = f"{new_element['data']['source']}/{new_element['data']['target']}"

            # avoid adding:
            #   edges between nodes within the same virtual nodes
            #   duplicate edges
            if (
                new_element["data"]["source"] != new_element["data"]["target"]
                and new_element not in out_elements
            ):
                out_elements.append(new_element)

    # 2. add visible virtual nodes
    for virtual_node_name in virtual_node_map:
        highest_collapsed_virtual_node_name = (
            utils.get_highest_collapsed_virtual_node_name(
                virtual_node_name, virtual_node_map, parent_virtual_node_map
            )
        )
        if (
            highest_collapsed_virtual_node_name is None
            or highest_collapsed_virtual_node_name == virtual_node_name
        ):
            # This condition determines if the virtual node should be visible
            # first condition: entire stack of virtual nodes is expanded
            # second condition: the virtual node itself is the toplevel, collapsed node
            new_element = {
                "data": {
                    "label": virtual_node_name,
                    "id": virtual_node_name,
                    "ujt_id": virtual_node_name,
                },
                "classes": "",
            }
            if virtual_node_name in parent_virtual_node_map:
                new_element["data"]["parent"] = parent_virtual_node_map[
                    virtual_node_name
                ]
            out_elements.append(new_element)

    return out_elements


def apply_uuid_to_elements(elements, uuid_to_apply=None):
    """Append a new UUID to the id of each cytoscape element

    This is used as a workaround to update the source/target of edges, and the parent/child relatioship of nodes.
    In Cytoscape.js, these relationships are immutable, and a move() function has to
    be called on the element to update the aforementioned properties.
    However, Dash Cytoscape doesn't expose this functionality.
    See https://github.com/plotly/dash-cytoscape/issues/106.
    By providing a new ID, we can avoid this restriction.

    Args:
        elements: a list of Cytoscape elements
        uuid_to_apply: a UUID to append. Defaults to None.
            If None is provided, this function generates a new UUID.

    Returns:
        A list of Cytoscape elements with an UUID appended to their ID fields.
    """
    if uuid_to_apply is None:
        uuid_to_apply = uuid.uuid4()

    out_elements = []

    # the properties of the element that need to have a UUID
    # appended
    UUID_KEYS = ["id", "source", "target", "parent"]
    for element in elements:
        new_element = copy.deepcopy(element)
        for key in UUID_KEYS:
            if key in new_element["data"]:
                new_element["data"][key] += f"#{uuid_to_apply}"
        out_elements.append(new_element)

    return out_elements


def apply_slis_to_node_map(sli_list, node_map):
    """Updates the nodes in the node map with the slis from the sli list.

    Args:
        sli_list: A list of SLIs to add to the nodes
        node_map: A dict mapping node names to nodes

    Returns:
        a dict mapping node names to nodes, with updated SLIs
    """

    out_node_map = copy.deepcopy(node_map)

    for sli in sli_list:
        node = out_node_map[sli.node_name]
        # find the index of the node's SLI with the same SLI type as the SLI from sli_list

        new_node_slis = []

        for node_sli in node.slis:
            if node_sli.sli_type == sli.sli_type:
                new_node_slis.append(sli)
            else:
                new_node_slis.append(node_sli)

        del node.slis[:]
        node.slis.extend(new_node_slis)

    return out_node_map


def sort_nodes_by_parent_relationship(elements):
    """Returns a list of elements where node parents always appear before node children.

    This method essentially performs a topological sort on the trees
    formed from parent-child relationships between nodes.

    For context, see https://github.com/plotly/dash-cytoscape/issues/112
    and https://github.com/googleinterns/userjourneytool/issues/63

    Args:
        elements: a list of cytoscape elements.

    Returns:
        a list of cytoscape where node parents always appear before node children.
    """

    edges = []
    node_id_element_map = {}
    for element in elements:
        new_element = copy.deepcopy(element)
        if utils.is_node_element(new_element):
            node_id_element_map[element["data"]["id"]] = new_element
        else:
            edges.append(new_element)

    parent_child_map = defaultdict(list)
    bfs_queue = deque()

    lexicographically_sorted_edges = sorted(edges, key=lambda edge: edge["data"]["id"])
    # initially sort the nodes to ensure a consistent traversal order, for a consistent layout
    lexicographically_sorted_nodes = sorted(
        node_id_element_map.values(), key=lambda node: node["data"]["id"]
    )

    # build a tree from parents to children (parent_child_map)
    # (reversing the edge direction of cytoscape format)
    for node in lexicographically_sorted_nodes:
        node_id = node["data"]["id"]
        if "parent" in node["data"]:
            parent_id = node["data"]["parent"]
            parent_child_map[parent_id].append(node_id)
        else:
            bfs_queue.append(node_id)

    topologically_sorted_nodes = []
    visited_node_ids = set()
    while bfs_queue:
        node_id = bfs_queue.popleft()
        if node_id in visited_node_ids:
            raise ValueError("Circular parent/child relationship detected!")
        else:
            visited_node_ids.add(node_id)
        bfs_queue.extend(parent_child_map[node_id])
        topologically_sorted_nodes.append(node_id_element_map[node_id])

    return lexicographically_sorted_edges + topologically_sorted_nodes
