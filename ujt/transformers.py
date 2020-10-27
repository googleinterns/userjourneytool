""" Module holding transformer functions.

Transformer functions take an input data structure, make a change, and return an output of the same type.
They are commonly used to perform operations on cytoscape graph elements.
"""

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

    """
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
            class_list += [Status.Name(node.override_status), constants.OVERRIDE_CLASS]
        else:
            class_list.append(Status.Name(node.status))

        element["classes"] = " ".join(class_list)

    # no return since we directly mutated elements


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
    """
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
                    if tag == view_tag and tag != "" and view_style_name != "":
                        class_list.append(view_style_name)
        element["classes"] += f" {' '.join(class_list)}"


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

    output_elements = []
    for element in elements:
        ujt_id = element["data"]["ujt_id"]
        if ujt_id not in node_name_sli_map:
            output_elements.append(element.copy())
        else:
            element_copy = element.copy()
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
            element_copy["classes"] += f" {change_over_time_class}"
            output_elements.append(element_copy)

    return output_elements


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
    # We may want to refactor the edge map creation for testability.
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
    flattened_edges = [edge for edge_list in edges_map.values() for edge in edge_list]

    return flattened_edges + nodes_list


def remove_highlighted_class_from_edges(edges_map):
    """Removes the highlighted edge class to edges within a specific user journey.

    Args:
        edges_map: A dictionary mapping edge sources to a list of cytoscape elements describing edges originating from the source
    """

    for edge_list in edges_map.values():
        for edge in edge_list:
            # in the future, if we apply other classes to edges, need to change this to only remove highlighted class.
            edge["classes"] = ""


def apply_highlighted_class_to_edges(edges_map, user_journey_name):
    """Applies the highlighted edge class to edges within a specific user journey.

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
            highest_collapsed_virtual_node_name = (
                utils.get_highest_collapsed_virtual_node_name(
                    element["data"]["ujt_id"], virtual_node_map, parent_virtual_node_map
                )
            )
            if highest_collapsed_virtual_node_name is None:
                # not within collapsed node
                if (
                    element["data"]["ujt_id"] in parent_virtual_node_map
                    and "parent" not in element["data"]
                ):
                    element["data"]["parent"] = parent_virtual_node_map[
                        element["data"]["ujt_id"]
                    ]
                new_elements.append(element)

        else:
            new_source = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["source"], virtual_node_map, parent_virtual_node_map
            )
            new_target = utils.get_highest_collapsed_virtual_node_name(
                element["data"]["target"], virtual_node_map, parent_virtual_node_map
            )

            if new_source is not None:
                element["data"]["source"] = new_source
            if new_target is not None:
                element["data"]["target"] = new_target

            element["data"][
                "id"
            ] = f"{element['data']['source']}/{element['data']['target']}"

            if (
                element["data"]["source"] != element["data"]["target"]
                and element not in new_elements
            ):
                new_elements.append(element)

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
            # This if statement determines if the virtual node should be visible
            # first condition: entire stack of virtual nodes is expanded
            # second condition: the virtual node itself is the toplevel, collapsed node
            element = {
                "data": {
                    "label": virtual_node_name,
                    "id": virtual_node_name,
                    "ujt_id": virtual_node_name,
                },
            }
            if virtual_node_name in parent_virtual_node_map:
                element["data"]["parent"] = parent_virtual_node_map[virtual_node_name]
            new_elements.append(element)

    return new_elements


def apply_uuid_to_elements(elements, this_uuid=None):
    """Append a new UUID to the id of each cytoscape element

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

    return node_map


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
        if utils.is_node_element(element):
            node_id_element_map[element["data"]["id"]] = element
        else:
            edges.append(element)

    parent_child_map = defaultdict(list)
    bfs_queue = deque()
    # build a tree from parents to children
    # (reversing the edge direction of cytoscape format)
    for node in node_id_element_map.values():
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

    return edges + topologically_sorted_nodes
