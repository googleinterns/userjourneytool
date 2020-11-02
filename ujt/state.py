from collections import defaultdict, deque
from typing import TYPE_CHECKING, Any, DefaultDict, Deque, Dict, List, Set, Tuple

from graph_structures_pb2 import (
    SLI,
    Client,
    Node,
    NodeType,
    Status,
    UserJourney,
    VirtualNode,
)

from . import constants, converters, id_constants, rpc_client, utils
from .dash_app import cache

if TYPE_CHECKING:
    from graph_structures_pb2 import (
        StatusValue,  # pylint: disable=no-name-in-module  # pragma: no cover
    )


def clear_sli_cache():
    cache.delete_memoized(get_slis)


# This memoization prevents multiple UJT frontends from requesting
# the reporting server for new data within the same interval.
@cache.memoize(timeout=constants.SERVER_SLI_REFRESH_INTERVAL_SECONDS)
def get_slis() -> List[SLI]:
    """Gets a list of updated SLIs.

    Returns:
        A list of SLIs.
    """

    sli_response = rpc_client.get_slis()
    return list(
        sli_response.slis
    )  # convert to list to support memoization (via pickling)


def get_message_maps(
    force_refresh: bool = False,
) -> Tuple[Dict[str, Node], Dict[str, Client]]:
    """Gets Node and Client protobufs, computes their internal statuses, and return their maps.

    If the cache doesn't contain the message maps, this function reads the Nodes and Clients from the remote reporting server.

    Args:
        force_refresh: boolean indicating whether the UJT should request a new topology from the server

    Returns:
        A tuple of two dictionaries.
        The first dictionary contains a mapping from Node name to the actual Node protobuf message.
        The second dictionary contains a mapping from Client name to the actual Client protobuf message.
    """
    node_name_message_map = cache.get(id_constants.NODE_NAME_MESSAGE_MAP)
    client_name_message_map = cache.get(id_constants.CLIENT_NAME_MESSAGE_MAP)

    # If initial call (or cache was manually cleared) to get_message_maps, read from remote server.
    if (
        force_refresh
        or node_name_message_map is None
        or client_name_message_map is None
    ):
        node_response, client_response = (
            rpc_client.get_nodes(),
            rpc_client.get_clients(),
        )

        node_name_message_map = utils.proto_list_to_name_map(node_response.nodes)
        client_name_message_map = utils.proto_list_to_name_map(client_response.clients)

        override_status_map = get_override_status_map()
        comment_map = get_comment_map()

        for node_name in override_status_map:
            if (
                node_name in node_name_message_map
            ):  # if we had a saved value for non-virtual node
                node_name_message_map[node_name].override_status = override_status_map[
                    node_name
                ]

        for node_name in comment_map:
            if node_name in node_name_message_map:
                node_name_message_map[node_name].comment = comment_map[node_name]

        cache.set(id_constants.NODE_NAME_MESSAGE_MAP, node_name_message_map)
        cache.set(id_constants.CLIENT_NAME_MESSAGE_MAP, client_name_message_map)

    return node_name_message_map, client_name_message_map


def get_node_name_message_map() -> Dict[str, Node]:
    """Gets a dictionary mapping Node names to Node messages.

    Returns:
        A dictionary mapping Node names to Node messages.
    """

    return get_message_maps()[0]


def set_node_name_message_map(node_name_message_map):
    return cache.set(id_constants.NODE_NAME_MESSAGE_MAP, node_name_message_map)


def get_client_name_message_map() -> Dict[str, Client]:
    """Gets a dictionary mapping Client names to Client messages.

    Returns:
        A dictionary mapping Client names to Client messages.
    """
    return get_message_maps()[1]


def set_client_name_message_map(client_name_message_map):
    cache.set(id_constants.CLIENT_NAME_MESSAGE_MAP, client_name_message_map)


@cache.memoize()
def get_cytoscape_elements():
    node_name_message_map, client_name_message_map = get_message_maps()
    elements = converters.cytoscape_elements_from_maps(
        node_name_message_map,
        client_name_message_map,
    )
    return elements


# region virtual node
def get_virtual_node_map() -> Dict[str, VirtualNode]:
    """Gets a dictionary mapping virtual node names to virtual node messages.

    Returns:
        A dictionary mapping virtual node names to virtual node objects.
    """
    return cache.get(id_constants.VIRTUAL_NODE_MAP)


def set_virtual_node_map(virtual_node_map: Dict[str, VirtualNode]):
    """Sets a dictionary mapping virtual node names to virtual node objects.

    Args:
        virutal_node_map: The new virtual node map to be saved in the cache.
    """
    cache.set(id_constants.VIRTUAL_NODE_MAP, virtual_node_map)


def get_parent_virtual_node_map() -> Dict[str, str]:
    """Gets a dictionary mapping node names to the name of their direct virtual node parent.

    The keys of the dictionary can be names of virtual and non-virtual nodes.
    The values are always virtual nodes.
    This dictionary can be used to re-construct the chain of the virtual nodes that contain a given node.

    Returns:
        A dictionary mapping node names to the name of their direct virtual node parent.
    """
    return cache.get(id_constants.PARENT_VIRTUAL_NODE_MAP)


def set_parent_virtual_node_map(parent_virtual_node_map: Dict[str, str]):
    """Sets a dictionary mapping node names to the name of their direct virtual node parent.

    Args:
        parent_virutal_node_map: The new parent virtual node map to be saved in the cache.
    """
    cache.set(id_constants.PARENT_VIRTUAL_NODE_MAP, parent_virtual_node_map)


def add_virtual_node(
    virtual_node_name: str,
    selected_node_data: List[Dict[str, Any]],
):
    """Adds a virtual node.

    Updates the virtual node map with the newly created virtual node object.
    Updates the entries in the parent virtual node map corresponding to the virtual node's children,
    to point to the new virtual node.

    The interface could be refactored to take node_names instead of selected_node_data to be cleaner.
    However, this function is currently only called in the callback to update the elements of the cytoscape graph.
    It would be an extraneous transformation that doesn't offer any additional convenience or benefit, currently.

    Args:
        virutal_node_name: The name of the virtual node to create.
        selected_node_data: A list of node data dictionaries to include in the virtual node.

    """
    virtual_node_map = get_virtual_node_map()
    parent_virtual_node_map = get_parent_virtual_node_map()
    node_name_message_map = get_node_name_message_map()

    virtual_node_child_names: Set[str] = set()
    # use this queue to do BFS to flatten non-virtual nodes
    node_frontier: Deque[Node] = deque()
    for node_data in selected_node_data:
        if node_data["ujt_id"] in virtual_node_map:  # nested virtual node
            virtual_node_child_names.add(node_data["ujt_id"])
            parent_virtual_node_map[node_data["ujt_id"]] = virtual_node_name
        else:
            node_frontier.append(node_name_message_map[node_data["ujt_id"]])

    while node_frontier:
        node = node_frontier.popleft()
        virtual_node_child_names.add(node.name)
        parent_virtual_node_map[node.name] = virtual_node_name
        for child_name in node.child_names:
            node_frontier.append(node_name_message_map[child_name])

    virtual_node = VirtualNode(
        name=virtual_node_name,
        child_names=virtual_node_child_names,
        collapsed=True,
        node_type=NodeType.NODETYPE_VIRTUAL,
    )
    virtual_node_map[virtual_node_name] = virtual_node

    set_virtual_node_map(virtual_node_map)
    set_parent_virtual_node_map(parent_virtual_node_map)


def delete_virtual_node(virtual_node_name: str):
    """Deletes a virtual node.

    Updates the virtual node map to remove the corresponding virtual node object.
    Updates the entries in the parent virtual node map corresponding to the virtual node's children,
    to no longer point to the new virtual node.

    Args:
        virutal_node_name: The name of the virtual node to delete.
    """
    virtual_node_map = get_virtual_node_map()
    parent_virtual_node_map = get_parent_virtual_node_map()
    override_status_map = get_override_status_map()
    comment_map = get_comment_map()

    virtual_node = virtual_node_map[virtual_node_name]
    # child_names property is convenient but not strictly necessary.
    for child_name in virtual_node.child_names:
        del parent_virtual_node_map[child_name]

    del virtual_node_map[virtual_node_name]

    if virtual_node_name in override_status_map:
        del override_status_map[virtual_node_name]

    if virtual_node_name in comment_map:
        del comment_map[virtual_node_name]

    set_virtual_node_map(virtual_node_map)
    set_parent_virtual_node_map(parent_virtual_node_map)
    set_override_status_map(override_status_map)
    set_comment_map(comment_map)


def set_virtual_node_collapsed_state(virtual_node_name: str, collapsed: bool):
    """Sets the collapsed state of a virtual node.

    Updates the corresponding virtual node object within the virtual node map.

    Args:
        virutal_node_name: The name of the virtual node to update.
        collapsed: The new collapsed state
    """
    virtual_node_map = get_virtual_node_map()
    virtual_node = virtual_node_map[virtual_node_name]
    virtual_node.collapsed = collapsed
    set_virtual_node_map(virtual_node_map)


# endregion


def get_comment_map() -> Dict[str, str]:
    """Gets a dictionary mapping node names to their comment.

    Returns:
        The mapping between node names and their comment.
    """
    return cache.get(id_constants.COMMENT_MAP)


def set_comment_map(comment_map: Dict[str, str]):
    """Sets a dictionary mapping node names to their comment.

    Args:
        override_status_map: a dictionary mapping node names to their comment.
    """
    cache.set(id_constants.COMMENT_MAP, comment_map)


def set_comment(
    name: str,
    comment: str,
    node_name_message_map: Dict[str, Node] = None,
    client_name_message_map: Dict[str, Client] = None,
    virtual_node_map: Dict[str, VirtualNode] = None,
):
    """Sets the node comment in the appropriate node map.

    Addiionally adds the override status to an internal map.
    This internal map is combined with the graph topology when the topology is read from the reporting server.

    Args:
        name: The name of the node or client to modify.
        comment: The comment to write to the node or client
        node_name_message_map: A dictionary mapping node names to Nodes. Used when we want to modify the state of an existing map without reading from cache.
        client_name_message_map: A dictionary mapping client names to Clients. Used when we want to modify the state of an existing map without reading from cache.
        virtual_node_map: A dictionary mapping virtual node names to VirtualNodes. Used when we want to modify the state of an existing map without reading from cache.
    """

    save_changes = False

    maps = [node_name_message_map, client_name_message_map, virtual_node_map]
    getters = [
        get_node_name_message_map,
        get_client_name_message_map,
        get_virtual_node_map,
    ]
    setters = [
        set_node_name_message_map,
        set_client_name_message_map,
        set_virtual_node_map,
    ]

    for idx, proto_map in enumerate(maps):
        if proto_map is None:
            proto_map = getters[idx]()  # type: ignore
            save_changes = True
        if name in proto_map:  # type: ignore
            proto_map[name].comment = comment  # type: ignore
            if save_changes:
                setters[idx](proto_map)

    comment_map = get_comment_map()
    if comment == "":
        try:
            del comment_map[name]
        except KeyError:  # the node didn't have a comment before
            pass
    else:
        comment_map[name] = comment
    set_comment_map(comment_map)


def get_override_status_map() -> Dict[str, "StatusValue"]:
    """Gets a dictionary mapping node names to their override status.

    Returns:
        The mapping between node names and their override status.
    """
    return cache.get(id_constants.OVERRIDE_STATUS_MAP)


def set_override_status_map(override_status_map: Dict[str, "StatusValue"]):
    """Sets a dictionary mapping node names to their override status.

    Args:
        override_status_map: a dictionary mapping node names to their override status.
    """
    cache.set(id_constants.OVERRIDE_STATUS_MAP, override_status_map)


def set_node_override_status(
    node_name: str,
    override_status: "StatusValue",
    node_name_message_map: Dict[str, Node] = None,
    virtual_node_map: Dict[str, VirtualNode] = None,
):
    """Sets the node override status in the appropriate node map.

    Addiionally adds the override status to an internal map.
    This internal map is combined with the graph topology when the topology is read from the reporting server.

    Notice that this function doesn't read and write from the cache if maps were provided in the arguments.
    The maps should be provided when the caller is in the middle of a modification (a "transaction") of the message maps.
    For instance,
        node_name_message_map = state.get_node_name_message_map()
        modify_map(node_name_message_map)
        set_node_override_status(node_name, override_status, node_name_message_map, virtual_node_map)
        state.set_node_name_message_map(node_name_message_map)

    Args:
        node_name: The name of the node to modify.
        override_status: The override status to write to the node
        node_name_message_map: A dictionary mapping node names to Nodes. Used when we want to modify the state of an existing map without reading from cache.
        virtual_node_map: A dictionary mapping virtual node names to VirtualNodes. Used when we want to modify the state of an existing map without reading from cache.
    """
    save_changes = False

    maps = [node_name_message_map, virtual_node_map]
    getters = [get_node_name_message_map, get_virtual_node_map]
    setters = [set_node_name_message_map, set_virtual_node_map]

    for idx, proto_map in enumerate(maps):
        if proto_map is None:
            maps[idx] = getters[idx]()  # type: ignore
            save_changes = True
        if node_name in proto_map:  # type: ignore
            proto_map[  # type: ignore
                node_name
            ].override_status = override_status  # type: ignore
            if save_changes:
                setters[idx](proto_map)

    override_status_map = get_override_status_map()
    if override_status == Status.STATUS_UNSPECIFIED:
        try:
            del override_status_map[node_name]
        except KeyError:  # the node didn't have a comment before
            pass
    else:
        override_status_map[node_name] = override_status
    set_override_status_map(override_status_map)


@cache.memoize()
def get_node_to_user_journey_map() -> Dict[str, List[UserJourney]]:
    """Generates a map from node name to user journey that pass through the node.

    We place this function in module state, but it doesn't really produce/modify state.
    It is, however, conceptually similar to the other maps that are exposed in this module.
    This one is just dynamically generated once.

    Returns:
        a dictionary associating node names and user journeys that pass through the node.
    """
    node_name_message_map, client_name_message_map = get_message_maps()

    user_journey_map: Dict[str, UserJourney] = {}
    node_name_user_journey_name_map: DefaultDict[str, Set[str]] = defaultdict(set)

    for client in client_name_message_map.values():
        for user_journey in client.user_journeys:
            user_journey_map[user_journey.name] = user_journey

            # perform a BFS through the user journey
            node_frontier = deque(
                [dependency.target_name for dependency in user_journey.dependencies]
            )
            while node_frontier:
                current_node_name = node_frontier.popleft()
                node_name_user_journey_name_map[current_node_name].add(
                    user_journey.name
                )

                # add all the node's parents
                parent_name = node_name_message_map[current_node_name].parent_name
                while parent_name != "":
                    node_name_user_journey_name_map[parent_name].add(user_journey.name)
                    parent_name = node_name_message_map[parent_name].parent_name

                for dependency in node_name_message_map[current_node_name].dependencies:
                    node_frontier.append(dependency.target_name)

    node_name_user_journey_map: Dict[str, List[UserJourney]] = {}
    for node_name, user_journey_names in node_name_user_journey_name_map.items():
        node_name_user_journey_map[node_name] = [
            user_journey_map[user_journey_name]
            for user_journey_name in user_journey_names
        ]

    return node_name_user_journey_map


# Maybe we can think about making the following functions the result of
# a higher order function or decorator.
# See https://stackoverflow.com/questions/13184281/python-dynamic-function-creation-with-custom-names


# region tag list
def get_tag_list() -> List[str]:
    """Return the list of tags.

    We use a list since the order matters when using pattern matching callbacks to remove tags.

    Returns:
        A list containing the created tags.
    """
    return cache.get(id_constants.TAG_LIST)


def set_tag_list(tag_list):
    return cache.set(id_constants.TAG_LIST, tag_list)


def create_tag(new_tag):
    tag_list = get_tag_list()
    tag_list.append(new_tag)
    set_tag_list(tag_list)


def delete_tag(tag_index):
    tag_list = get_tag_list()

    tag_value = tag_list[tag_index]
    tag_map = get_tag_map()
    for ujt_id in tag_map:
        tag_map[ujt_id] = [tag for tag in tag_map[ujt_id] if tag != tag_value]
    set_tag_map(tag_map)

    del tag_list[tag_index]
    set_tag_list(tag_list)


def update_tag(tag_index, new_tag):
    tag_list = get_tag_list()
    tag_list[tag_index] = new_tag
    set_tag_list(tag_list)


# endregion


# region tag map
def get_tag_map() -> Dict[str, List[str]]:
    """Returns the map associating ujt_ids and applied tags.

    The tag map associates names of nodes/virtual nodes/clients with a list of the tags that they contain.
    Maybe we should break this map up into separate maps for nodes, virtual nodes, and clients, but their names should be unique,
    so I leave it as one map for now.
    We use lists as the value type of the dictionary since we need an ordering to use the pattern matching callbacks to add/remove tags.
    Moreover, this ensures a consistent ordering of applied tags in the UI.

    Returns:
        A dictionary associating ujt_ids and their applied tags.
    """
    return cache.get(id_constants.TAG_MAP)


def set_tag_map(tag_map):
    return cache.set(id_constants.TAG_MAP, tag_map)


def add_tag_to_element(ujt_id, tag):
    """Adds a tag to an element.

    We generally use "add" or "applies" to refer to this operation,
    (as opposed to create).
    This function is generally called with tag == "", when adding a new apply tag UI row.

    Args:
        ujt_id: the UJT specific id of the element (see converters.py)
        tag: the tag to apply
    """
    tag_map = get_tag_map()
    tag_map[ujt_id].append(tag)
    set_tag_map(tag_map)


def remove_tag_from_element(ujt_id, tag_idx):
    tag_map = get_tag_map()
    del tag_map[ujt_id][tag_idx]
    set_tag_map(tag_map)


def remove_tag_from_element_by_value(ujt_id, tag_to_remove):
    tag_map = get_tag_map()
    tag_map[ujt_id] = [tag for tag in tag_map[ujt_id] if tag != tag_to_remove]
    set_tag_map(tag_map)


def update_applied_tag(ujt_id, tag_idx, tag):
    tag_map = get_tag_map()
    tag_map[ujt_id][tag_idx] = tag
    set_tag_map(tag_map)


# endregion


# region style map
def get_style_map() -> Dict[str, Dict[str, str]]:
    """Return the map of styles.

    The style map associates the name of a style with the value of the "style" field in the cytoscape stylesheet.
    """

    return cache.get(id_constants.STYLE_MAP)


def set_style_map(style_map):
    return cache.set(id_constants.STYLE_MAP, style_map)


def update_style(style_name: str, style_dict: Dict[str, str]):
    style_map = get_style_map()

    if " " in style_name:  # where should validation be done? in the callback or here?
        raise ValueError("Styles cannot contain spaces!")

    style_map[style_name] = style_dict
    set_style_map(style_map)


def delete_style(style_name: str):
    style_map = get_style_map()
    del style_map[style_name]
    set_style_map(style_map)


# endregion
