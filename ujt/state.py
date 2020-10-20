from collections import defaultdict, deque
from typing import (
    TYPE_CHECKING,
    Any,
    DefaultDict,
    Deque,
    Dict,
    List,
    Set,
    Tuple,
    cast)

from graph_structures_pb2 import (
    SLI,
    Client,
    Node,
    NodeType,
    Status,
    UserJourney,
    VirtualNode)

from . import converters, rpc_client, utils
from .dash_app import cache

if TYPE_CHECKING:
    from graph_structures_pb2 import \
        StatusValue  # pylint: disable=no-name-in-module  # pragma: no cover


def clear_sli_cache():
    cache.delete_memoized(get_slis)


# We use cache.memoize here since the UJT doesn't explicitly write
# to the list of SLIs, unlike the node or client message maps.
# This memoization prevents multiple UJT frontends from requesting the reporting server
# for new data within the same interval.
@cache.memoize()
def get_slis() -> List[SLI]:
    """ Gets a list of updated SLIs.

    Returns:
        A list of SLIs.
    """

    sli_response = rpc_client.get_slis()
    return list(
        sli_response.slis
    )  # convert to list to support memoization (via pickling)


def get_message_maps() -> Tuple[Dict[str, Node], Dict[str, Client]]:
    """ Gets Node and Client protobufs, computes their internal statuses, and return their maps.

    If the cache doesn't contain the message maps, this function reads the Nodes and Clients from the remote reporting server.

    Returns:
        A tuple of two dictionaries.
        The first dictionary contains a mapping from Node name to the actual Node protobuf message.
        The second dictionary contains a mapping from Client name to the actual Client protobuf message.
    """
    node_name_message_map = cache.get("node_name_message_map")
    client_name_message_map = cache.get("client_name_message_map")

    # If initial call (or cache was manually cleared) to get_message_maps, read from remote server.
    if node_name_message_map is None or client_name_message_map is None:
        node_response, client_response = rpc_client.get_nodes(), rpc_client.get_clients()

        node_name_message_map = utils.proto_list_to_name_map(
            node_response.nodes)
        client_name_message_map = utils.proto_list_to_name_map(
            client_response.clients)

        cache.set("node_name_message_map", node_name_message_map)
        cache.set("client_name_message_map", client_name_message_map)

    return node_name_message_map, client_name_message_map


def get_node_name_message_map() -> Dict[str, Node]:
    """ Gets a dictionary mapping Node names to Node messages.

    Returns:
        A dictionary mapping Node names to Node messages.
    """

    return get_message_maps()[0]


def set_node_name_message_map(node_name_message_map):
    return cache.set("node_name_message_map", node_name_message_map)


def get_client_name_message_map() -> Dict[str, Client]:
    """ Gets a dictionary mapping Client names to Client messages.

    Returns:
        A dictionary mapping Client names to Client messages.
    """
    return get_message_maps()[1]


def set_client_name_message_map(client_name_message_map):
    cache.set("client_name_message_map", client_name_message_map)


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
    """ Gets a dictionary mapping virtual node names to virtual node messages.

    Returns:
        A dictionary mapping virtual node names to virtual node objects.
    """
    return cache.get("virtual_node_map")


def set_virtual_node_map(virtual_node_map: Dict[str, VirtualNode]):
    """ Sets a dictionary mapping virtual node names to virtual node objects.
    
    Args:
        virutal_node_map: The new virtual node map to be saved in the cache.
    """
    cache.set("virtual_node_map", virtual_node_map)


def get_parent_virtual_node_map() -> Dict[str, str]:
    """ Gets a dictionary mapping node names to the name of their direct virtual node parent.

    The keys of the dictionary can be names of virtual and non-virtual nodes.
    The values are always virtual nodes. 
    This dictionary can be used to re-construct the chain of the virtual nodes that contain a given node. 

    Returns:
        A dictionary mapping node names to the name of their direct virtual node parent.
    """
    return cache.get("parent_virtual_node_map")


def set_parent_virtual_node_map(parent_virtual_node_map: Dict[str, str]):
    """ Sets a dictionary mapping node names to the name of their direct virtual node parent.
    
    Args:
        parent_virutal_node_map: The new parent virtual node map to be saved in the cache.
    """
    cache.set("parent_virtual_node_map", parent_virtual_node_map)


def add_virtual_node(
    virtual_node_name: str,
    selected_node_data: List[Dict[str,
                                  Any]],
):
    """ Adds a virtual node.

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
    """ Deletes a virtual node.

    Updates the virtual node map to remove the corresponding virtual node object.
    Updates the entries in the parent virtual node map corresponding to the virtual node's children,
    to no longer point to the new virtual node.

    Args:
        virutal_node_name: The name of the virtual node to delete.
    """
    virtual_node_map = get_virtual_node_map()
    parent_virtual_node_map = get_parent_virtual_node_map()

    virtual_node = virtual_node_map[virtual_node_name]
    # child_names property is convenient but not strictly necessary.
    for child_name in virtual_node.child_names:
        del parent_virtual_node_map[child_name]

    del virtual_node_map[virtual_node_name]

    set_virtual_node_map(virtual_node_map)
    set_parent_virtual_node_map(parent_virtual_node_map)


def set_virtual_node_collapsed_state(virtual_node_name: str, collapsed: bool):
    """ Sets the collapsed state of a virtual node.

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


def set_comment(
    name: str,
    comment: str,
    node_name_message_map: Dict[str,
                                Node] = None,
    client_name_message_map: Dict[str,
                                  Client] = None,
    virtual_node_map: Dict[str,
                           VirtualNode] = None,
):
    """ Sets the node comment in the appropriate node map.

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
        get_virtual_node_map
    ]
    setters = [
        set_node_name_message_map,
        set_client_name_message_map,
        set_virtual_node_map
    ]

    for idx, proto_map in enumerate(maps):
        if proto_map is None:
            proto_map = getters[idx]()  # type: ignore
            save_changes = True
        if name in proto_map:  # type: ignore
            proto_map[name].comment = comment  # type: ignore
            if save_changes:
                setters[idx](proto_map)

    comment_map = cache.get("comment_map")
    if comment == "":
        try:
            del comment_map[name]
        except KeyError:  # the node didn't have a comment before
            pass
    else:
        comment_map[name] = comment
    cache.set("comment_map", comment_map)


def set_node_override_status(
    node_name: str,
    override_status: "StatusValue",
    node_name_message_map: Dict[str,
                                Node] = None,
    virtual_node_map: Dict[str,
                           VirtualNode] = None,
):
    """ Sets the node override status in the appropriate node map.

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
                node_name].override_status = override_status  # type: ignore
            if save_changes:
                setters[idx](proto_map)

    override_status_map = cache.get("override_status_map")
    if override_status == Status.STATUS_UNSPECIFIED:
        try:
            del override_status_map[node_name]
        except KeyError:  # the node didn't have a comment before
            pass
    else:
        override_status_map[node_name] = override_status
    cache.set("override_status_map", override_status_map)


#@cache.memoize()  # this is commented out for consistent testing
def get_node_to_user_journey_map() -> Dict[str, List[UserJourney]]:
    # map the node name to user journey names that pass through the node
    # should this be in state? it's memoized but doesn't really affect state
    # however, it's kind of similar to the other maps we expose in state.py,
    # only this one is dynamically generated once...
    node_name_message_map, client_name_message_map = get_message_maps()
    output_map: DefaultDict[
        str,
        List[UserJourney]] = defaultdict(
            list
        )  # we would prefer to use a set here, but protobufs are not hashable
    for client in client_name_message_map.values():
        for user_journey in client.user_journeys:
            node_frontier = deque(
                [
                    dependency.target_name
                    for dependency in user_journey.dependencies
                ])

            while node_frontier:
                current_node_name = node_frontier.popleft()
                if user_journey not in output_map[
                        current_node_name]:  # since we don't use a set, we check if it exists in the list already
                    output_map[current_node_name].append(user_journey)

                # add all the node's parents
                parent_name = node_name_message_map[
                    current_node_name].parent_name
                while parent_name != "":
                    if user_journey not in output_map[parent_name]:
                        output_map[parent_name].append(user_journey)
                    parent_name = node_name_message_map[parent_name].parent_name

                for dependency in node_name_message_map[
                        current_node_name].dependencies:
                    node_frontier.append(dependency.target_name)

    return output_map


# Maybe we can think about making the following functions the result of
# a higher order function or decorator.
# See https://stackoverflow.com/questions/13184281/python-dynamic-function-creation-with-custom-names


#region tag list
def get_tag_list() -> List[str]:
    """ Return the list of tags.

    We use a list since the order matters when using pattern matching callbacks to remove tags.

    Returns:
        A list containing the created tags.
    """
    return cache.get("tag_list")


def set_tag_list(tag_list):
    return cache.set("tag_list", tag_list)


def create_tag(new_tag):
    tag_list = get_tag_list()
    if " " in new_tag:  # where should validation be done? in the callback or here?
        raise ValueError("Tags cannot contain spaces!")
    tag_list.append(new_tag)
    set_tag_list(tag_list)


def delete_tag(tag_index):
    tag_list = get_tag_list()
    del tag_list[tag_index]
    # TODO: delete this tag from the tag map
    set_tag_list(tag_list)


def update_tag(tag_index, new_tag):
    tag_list = get_tag_list()
    tag_list[tag_index] = new_tag
    set_tag_list(tag_list)


#endregion


#region tag map
def get_tag_map() -> Dict[str, List[str]]:
    """ Returns the map associating ujt_ids and applied tags.
    
    The tag map associates names of nodes/virtual nodes/clients with a list of the tags that they contain.
    Maybe we should break this map up into separate maps for nodes, virtual nodes, and clients, but their names should be unique,
    so I leave it as one map for now.
    We use lists as the value type of the dictionary since we need an ordering to use the pattern matching callbacks to add/remove tags. 
    Moreover, this ensures a consistent ordering of applied tags in the UI.

    Returns:
        A dictionary associating ujt_ids and their applied tags.
    """
    return cache.get("tag_map")


def set_tag_map(tag_map):
    return cache.set("tag_map", tag_map)


def add_tag_to_element(ujt_id, tag):
    """ Adds a tag to an element.

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


def update_applied_tag(ujt_id, tag_idx, tag):
    tag_map = get_tag_map()
    tag_map[ujt_id][tag_idx] = tag
    set_tag_map(tag_map)


#endregion


#region style map
def get_style_map() -> Dict[str, Dict[str, str]]:
    """ Return the map of styles.

    The style map associates the name of a style with the value of the "style" field in the cytoscape stylesheet.
    """

    return cache.get("style_map")


def set_style_map(style_map):
    return cache.set("style_map", style_map)


def update_style(style_name: str, style_dict: Dict[str, str]):
    style_map = get_style_map()
    style_map[style_name] = style_dict
    set_style_map(style_map)


def delete_style(style_name: str):
    style_map = get_style_map()
    del style_map[style_name]
    set_style_map(style_map)


#endregion


#region view list
def get_view_list():
    """ Returns the list of created views, which associate a tag and a style.

    This structure is a list since the ordering matters in the UI when displaying views.
    
    Returns:
        A list of all created views.
    """
    return cache.get("view_list")


def set_view_list(view_list):
    return cache.set("view_list", view_list)


def create_view(tag, style):
    view_list = get_view_list()
    view_list.append([tag, style])
    set_view_list(view_list)


def update_view(view_idx, tag, style):
    view_list = get_view_list()
    view_list[view_idx] = [tag, style]
    set_view_list(view_list)


def delete_view(view_idx):
    view_list = get_view_list()
    del view_list[view_idx]
    set_view_list(view_list)


#endregion
