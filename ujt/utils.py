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


from . import constants, state


def is_client_cytoscape_node(tap_node):
    return constants.CLIENT_CLASS in tap_node["classes"].split(" ")


def relative_name(full_name):
    return full_name.split(".")[-1]


def parent_full_name(full_name):
    return full_name.rsplit(".", 1)[0]


def human_readable_enum_name(enum_value, enum_class):
    return enum_class.Name(enum_value).split("_")[-1]


def is_node_element(element):
    return not "source" in element["data"].keys()


def ctx_triggered_info(ctx):
    triggered_id, triggered_prop, triggered_value = None, None, None
    if ctx.triggered:
        triggered_id, triggered_prop = ctx.triggered[0]["prop_id"].split(".")
        triggered_value = ctx.triggered[0]["value"]
    return triggered_id, triggered_prop, triggered_value


def get_highest_collapsed_virtual_node_name(node_name):
    """ Gets the name of the highest collapsed virtual node, given a node name.

    Node name can be virtual or non virtual.
    Highest refers to furthest ancestor.
    This function doesn't feel like it should be in utils, but not sure where else to put it.
    Can refactor later.

    Args:
        node_name: a name of a virtual or non-virtual node.

    Returns:
        The name of the highest collapsed virtual node above the given node.
    """
    virtual_node_map = state.get_virtual_node_map()
    parent_virtual_node_map = state.get_parent_virtual_node_map()

    current_name = node_name
    highest_collapsed_name = None

    while current_name in parent_virtual_node_map:
        if current_name in virtual_node_map and virtual_node_map[
                current_name].collapsed:
            highest_collapsed_name = current_name
        current_name = parent_virtual_node_map[current_name]

    # need this for the highest-level (last) virtual node, which isn't registered
    # in the parent_virtual_node_map.
    if current_name in virtual_node_map and virtual_node_map[
            current_name].collapsed:
        highest_collapsed_name = current_name

    return highest_collapsed_name
