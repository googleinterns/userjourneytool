# pylint: disable=redefined-outer-name

from unittest.mock import Mock, call, patch, sentinel

import pytest
from graph_structures_pb2 import NodeType, VirtualNode

import ujt.state


@pytest.fixture
def patch_path():
    return "ujt.state"


def test_clear_sli_cache(patch_path):
    with patch(f"{patch_path}.cache.delete_memoized") as mock_delete_memoized:
        ujt.state.clear_sli_cache()
        assert mock_delete_memoized.mock_calls == [call(ujt.state.get_slis)]


def test_get_slis(patch_path):
    with patch(f"{patch_path}.rpc_client.get_slis") as mock_rpc_client_get_slis, patch(
        f"{patch_path}.list"
    ) as mock_list:

        returned_slis = ujt.state.get_slis()

        assert mock_rpc_client_get_slis.mock_calls == [call()]
        assert mock_list.mock_calls == [
            call(mock_rpc_client_get_slis.return_value.slis)
        ]
        assert mock_list.return_value == returned_slis


def test_get_message_maps_no_cache(patch_path):
    with patch(
        f"{patch_path}.cache.get", Mock(return_value=None)
    ) as mock_cache_get, patch(f"{patch_path}.cache.set") as mock_cache_set, patch(
        f"{patch_path}.rpc_client.get_nodes"
    ) as mock_rpc_client_get_nodes, patch(
        f"{patch_path}.rpc_client.get_clients"
    ) as mock_rpc_client_get_clients, patch(
        f"{patch_path}.utils.proto_list_to_name_map",
        Mock(side_effect=[sentinel.node_map, sentinel.client_map]),
    ) as mock_proto_list_to_name_map:

        assert (sentinel.node_map, sentinel.client_map) == ujt.state.get_message_maps()

        assert mock_cache_get.mock_calls == [
            call("node_name_message_map"),
            call("client_name_message_map"),
        ]
        assert mock_rpc_client_get_nodes.mock_calls == [call()]
        assert mock_rpc_client_get_clients.mock_calls == [call()]
        assert mock_proto_list_to_name_map.mock_calls == [
            call(mock_rpc_client_get_nodes.return_value.nodes),
            call(mock_rpc_client_get_clients.return_value.clients),
        ]
        assert mock_cache_set.mock_calls == [
            call("node_name_message_map", sentinel.node_map),
            call("client_name_message_map", sentinel.client_map),
        ]


def test_get_message_maps_with_cached(patch_path):
    with patch(
        f"{patch_path}.cache.get",
        Mock(side_effect=[sentinel.node_map, sentinel.client_map]),
    ) as mock_cache_get:
        assert (sentinel.node_map, sentinel.client_map) == ujt.state.get_message_maps()


def test_get_node_name_message_map(patch_path):
    with patch(
        f"{patch_path}.get_message_maps",
        Mock(return_value=(sentinel.node_map, sentinel.client_map)),
    ):
        assert ujt.state.get_node_name_message_map() == sentinel.node_map


def test_set_node_name_message_map(patch_path):
    with patch(f"{patch_path}.cache.set") as mock_cache_set:
        ujt.state.set_node_name_message_map(sentinel.node_map)
        assert mock_cache_set.mock_calls == [
            call("node_name_message_map", sentinel.node_map)
        ]


def test_get_client_name_message_map(patch_path):
    with patch(
        f"{patch_path}.get_message_maps",
        Mock(return_value=(sentinel.node_map, sentinel.client_map)),
    ):
        assert ujt.state.get_client_name_message_map() == sentinel.client_map


def test_set_client_name_message_map(patch_path):
    with patch(f"{patch_path}.cache.set") as mock_cache_set:
        ujt.state.set_client_name_message_map(sentinel.client_map)
        assert mock_cache_set.mock_calls == [
            call("client_name_message_map", sentinel.client_map)
        ]


def test_get_virtual_node_map(patch_path):
    with patch(f"{patch_path}.cache.get") as mock_cache_get:
        assert ujt.state.get_virtual_node_map() == mock_cache_get.return_value


def test_set_virtual_node_map(patch_path):
    with patch(f"{patch_path}.cache.set") as mock_cache_set:
        ujt.state.set_virtual_node_map(sentinel.virtual_node_map)
        assert mock_cache_set.mock_calls == [
            call("virtual_node_map", sentinel.virtual_node_map)
        ]


def test_get_parent_virtual_node_map(patch_path):
    with patch(f"{patch_path}.cache.get") as mock_cache_get:
        assert ujt.state.get_parent_virtual_node_map() == mock_cache_get.return_value


def test_set_parent_virtual_node_map(patch_path):
    with patch(f"{patch_path}.cache.set") as mock_cache_set:
        ujt.state.set_parent_virtual_node_map(sentinel.parent_virtual_node_map)
        assert mock_cache_set.mock_calls == [
            call("parent_virtual_node_map", sentinel.parent_virtual_node_map)
        ]


def test_add_virtual_node(
    patch_path,
    example_node_name_message_map,
    example_node_name_message_map_service_relative_names,
    example_node_name_message_map_endpoint_relative_names,
    assert_same_elements,
):
    service_relative_names = example_node_name_message_map_service_relative_names
    endpoint_relative_names = example_node_name_message_map_endpoint_relative_names

    virtual_node_name = "sentinel.virtual_node_name"
    selected_node_data = [
        {
            "ujt_id": service_relative_names[0],
        }
    ]

    with patch(f"{patch_path}.get_virtual_node_map", Mock(return_value={})), patch(
        f"{patch_path}.get_parent_virtual_node_map", Mock(return_value={})
    ), patch(
        f"{patch_path}.get_node_name_message_map",
        Mock(return_value=example_node_name_message_map),
    ), patch(
        f"{patch_path}.set_virtual_node_map"
    ) as mock_set_virtual_node_map, patch(
        f"{patch_path}.set_parent_virtual_node_map"
    ) as mock_set_parent_virtual_node_map:

        ujt.state.add_virtual_node(virtual_node_name, selected_node_data)

        set_virtual_node_map_args, _ = mock_set_virtual_node_map.call_args
        assert len(set_virtual_node_map_args) == 1  # only one non-kw arg

        new_virtual_node_map = set_virtual_node_map_args[0]
        assert len(new_virtual_node_map) == 1  # only one item in dict

        virtual_node = new_virtual_node_map[virtual_node_name]
        assert virtual_node.name == virtual_node_name
        expected_virtual_node_child_names = [
            service_relative_names[0],
            f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
            f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
        ]
        assert_same_elements(
            virtual_node.child_names, expected_virtual_node_child_names
        )
        assert virtual_node.collapsed
        assert virtual_node.node_type == NodeType.NODETYPE_VIRTUAL

        # ---

        set_parent_virtual_node_map_args, _ = mock_set_parent_virtual_node_map.call_args
        assert len(set_parent_virtual_node_map_args) == 1

        new_parent_virtual_node_map = set_parent_virtual_node_map_args[0]
        assert len(new_parent_virtual_node_map) == 3
        for (
            name
        ) in (
            expected_virtual_node_child_names
        ):  # careful! virtual node itself isn't added to parent map
            assert name in new_parent_virtual_node_map
            assert new_parent_virtual_node_map[name] == virtual_node_name


def test_delete_virtual_node(patch_path):
    child_names = ["child0", "child1", "child2"]
    virtual_node_name = "virtual_node"
    virtual_node_map = {
        virtual_node_name: VirtualNode(
            name=virtual_node_name,
            child_names=child_names,
        ),
    }
    parent_virtual_node_map = {
        child_name: virtual_node_name for child_name in child_names
    }

    with patch(
        f"{patch_path}.get_virtual_node_map", Mock(return_value=virtual_node_map)
    ), patch(
        f"{patch_path}.get_parent_virtual_node_map",
        Mock(return_value=parent_virtual_node_map),
    ), patch(
        f"{patch_path}.set_virtual_node_map"
    ) as mock_set_virtual_node_map, patch(
        f"{patch_path}.set_parent_virtual_node_map"
    ) as mock_set_parent_virtual_node_map:

        ujt.state.delete_virtual_node(virtual_node_name)

        set_virtual_node_map_args, _ = mock_set_virtual_node_map.call_args
        assert len(set_virtual_node_map_args) == 1

        new_virtual_node_map = set_virtual_node_map_args[0]
        assert len(new_virtual_node_map) == 0

        # ---

        set_parent_virtual_node_map_args, _ = mock_set_parent_virtual_node_map.call_args
        assert len(set_parent_virtual_node_map_args) == 1

        new_parent_virtual_node_map = set_parent_virtual_node_map_args[0]
        assert len(new_parent_virtual_node_map) == 0


def test_set_virtual_node_collapsed_state(patch_path):
    virtual_node_name = "virtual_node"
    virtual_node_map = {
        virtual_node_name: VirtualNode(
            name=virtual_node_name,
            collapsed=True,
        ),
    }
    with patch(
        f"{patch_path}.get_virtual_node_map", Mock(return_value=virtual_node_map)
    ), patch(f"{patch_path}.set_virtual_node_map") as mock_set_virtual_node_map:
        ujt.state.set_virtual_node_collapsed_state(virtual_node_name, collapsed=False)

        set_virtual_node_map_args, _ = mock_set_virtual_node_map.call_args
        assert len(set_virtual_node_map_args) == 1

        new_virtual_node_map = set_virtual_node_map_args[0]
        assert len(new_virtual_node_map) == 1

        assert new_virtual_node_map[virtual_node_name].collapsed == False
