# Copyright 2020 Chuan Chen

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Module providing various utility functions.

Can be refactored into multiple files if necessary.
"""

import json
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from graph_structures_pb2 import SLI, Status

from . import constants


def is_client_cytoscape_node(tap_node: Dict[str, Any]) -> bool:
    return constants.CLIENT_CLASS in tap_node["classes"].split(" ")


def relative_name(full_name: str) -> str:
    return full_name.split(".")[-1]


def parent_full_name(full_name) -> str:
    return full_name.rsplit(".", 1)[0]


def human_readable_enum_name(enum_value, enum_class) -> str:
    return enum_class.Name(enum_value).split("_")[-1]


def is_node_element(element) -> bool:
    return not "source" in element["data"].keys()


def ctx_triggered_info(ctx) -> Tuple[Optional[str], Optional[str], Optional[Any]]:
    triggered_id, triggered_prop, triggered_value = None, None, None
    if ctx.triggered:
        triggered_id, triggered_prop = ctx.triggered[0]["prop_id"].split(".")
        triggered_value = ctx.triggered[0]["value"]
    return triggered_id, triggered_prop, triggered_value


def get_highest_collapsed_virtual_node_name(
    node_name,
    virtual_node_map,
    parent_virtual_node_map,
):
    """Gets the name of the highest collapsed virtual node, given a node name.

    Node name can be virtual or non virtual.
    Highest refers to furthest ancestor.
    This function doesn't feel like it should be in utils, but not sure where else to put it.
    Can refactor later.

    Args:
        node_name: A name of a virtual or non-virtual node.
        virtual_node_map: A dict mapping virtual node names to virtual node protos.
        parent_virtual_node_map: A parent mapping node names (virtual or non-virtual) to the name of their virtual parent.

    Returns:
        The name of the highest collapsed virtual node above the given node.
    """
    current_name = node_name
    highest_collapsed_name = None

    while current_name in parent_virtual_node_map:
        if (
            current_name in virtual_node_map
            and virtual_node_map[current_name].collapsed
        ):
            highest_collapsed_name = current_name
        current_name = parent_virtual_node_map[current_name]

    # need this for the highest-level (last) virtual node, which isn't registered
    # in the parent_virtual_node_map.
    if current_name in virtual_node_map and virtual_node_map[current_name].collapsed:
        highest_collapsed_name = current_name

    return highest_collapsed_name


def proto_list_to_name_map(proto_list):
    return {proto.name: proto for proto in proto_list}


def get_existing_uuid(elements):
    return elements[0]["data"]["id"].rsplit("#", 1)[1]


def get_all_node_names_within_virtual_node(
    virtual_node_name, node_name_message_map, virtual_node_map
):
    node_names = set()
    node_frontier = deque(virtual_node_map[virtual_node_name].child_names)

    while node_frontier:
        current_node_name = node_frontier.popleft()
        if current_node_name in node_name_message_map:
            node_names.add(current_node_name)
        if current_node_name in virtual_node_map:
            for child_name in virtual_node_map[current_node_name].child_names:
                node_frontier.append(child_name)

    return node_names


def string_to_dict(stringified_dict):
    return json.loads(stringified_dict)


def dict_to_str(input_dict, indent=4):
    return json.dumps(input_dict, indent=indent)


def get_latest_tapped_element(
    tap_node: Optional[Dict[str, Any]], tap_edge: Optional[Dict[str, Any]]
):
    if tap_node is None:
        return tap_edge

    if tap_edge is None:
        return tap_node

    return tap_node if tap_node["timeStamp"] > tap_edge["timeStamp"] else tap_edge


def get_change_over_time_class_from_composite_slis(
    before_composite_sli: Optional[SLI], after_composite_sli: Optional[SLI]
) -> str:
    """Returns the appropriate coloring/gradient based on the composite SLIs.

    We denote parts of a full styling class as a subclass.
    These include STATUS_HEALTHY, IMPROVED, etc.
    We join the subclasses together with underscore as a delimiter to create a full class name,
    that has an assoiated style.

    Args:
        before_composite_sli: A composite SLI holding the average value of the SLIs over the former half of a time interval.
        after_composite_sli: A composite SLI holding the average value of the SLIs over the latter half of a time interval.

    Returns:
        A class name to be added to the element.
    """

    before_subclass, after_subclass = (
        constants.NO_DATA_SUBCLASS,
        constants.NO_DATA_SUBCLASS,
    )
    if before_composite_sli is not None:
        before_subclass = Status.Name(before_composite_sli.status)
    if after_composite_sli is not None:
        after_subclass = Status.Name(after_composite_sli.status)

    if before_subclass == after_subclass != constants.NO_DATA_SUBCLASS:
        # Extra asserts here to make mypy happy
        assert before_composite_sli is not None
        assert after_composite_sli is not None

        # slo_target and threshold should be the
        # same for both the before and after sli
        slo_target = before_composite_sli.slo_target
        intra_status_change_threshold = (
            before_composite_sli.intra_status_change_threshold
        )
        if (
            abs(before_composite_sli.sli_value - after_composite_sli.sli_value)
            > intra_status_change_threshold
        ):
            if abs(slo_target - before_composite_sli.sli_value) < abs(
                slo_target - after_composite_sli.sli_value
            ):
                after_subclass += f"_{constants.WORSENED_SUBCLASS}"
            else:
                after_subclass += f"_{constants.IMPROVED_SUBCLASS}"

    return f"{before_subclass}_{after_subclass}"


def add_class_mutable(element: Dict[str, Any], class_names: List[str]):
    """Adds a class to a cytoscape element.

    This function mutates the input element.
    As such, it should be called only on a copy of the original element
    when used in a transformer.

    Args:
        element: a cytoscape element
        class_names: a list of class names to add to add
    """
    class_name_str = " ".join(class_names)
    element["classes"] += f" {class_name_str}"
