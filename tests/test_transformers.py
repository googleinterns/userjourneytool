# pylint: disable=redefined-outer-name

from collections import defaultdict
from unittest.mock import Mock, call, patch, sentinel

import pytest
from graph_structures_pb2 import Client, Node, NodeType, Status, VirtualNode

import ujt.constants
import ujt.transformers


@pytest.fixture
def patch_path():
    return "ujt.transformers"


def test_apply_node_classes(assert_same_elements):
    node_name = "node"
    node_name_message_map = {
        node_name:
            Node(
                name=node_name,
                status=Status.STATUS_HEALTHY,
                node_type=NodeType.NODETYPE_SERVICE,
            ),
    }
    client_name = "client"
    client_name_message_map = {
        client_name: Client(name=client_name,
                           ),
    }
    virtual_node_name = "virtual_node"
    virtual_node_name_message_map = {
        virtual_node_name:
            VirtualNode(
                name=virtual_node_name,
                status=Status.STATUS_HEALTHY,
                node_type=NodeType.NODETYPE_VIRTUAL,
            )
    }

    elements = [
        {
            "data": {
                "ujt_id": node_name,
            },
        },
        {
            "data": {
                "ujt_id": client_name,
            },
        },
        {
            "data": {
                "ujt_id": virtual_node_name,
            },
        },
    ]

    expected_elements = [
        {
            "data": {
                "ujt_id": node_name,
            },
            "classes": "NODETYPE_SERVICE STATUS_HEALTHY",
        },
        {
            "data": {
                "ujt_id": client_name,
            },
            "classes": ujt.constants.CLIENT_CLASS,
        },
        {
            "data": {
                "ujt_id": virtual_node_name,
            },
            "classes": "NODETYPE_VIRTUAL STATUS_HEALTHY",
        },
    ]

    ujt.transformers.apply_node_classes(
        elements,
        node_name_message_map,
        client_name_message_map,
        virtual_node_name_message_map)
    assert_same_elements(elements, expected_elements)


def test_apply_highlighted_edge_class_to_elements(
    patch_path,
    example_client_name_message_map_client_relative_names,
    example_client_name_message_map_user_journey_relative_names,
    example_edge_elements_from_client_map,
    example_node_elements_from_client_map,
    assert_same_elements,
):
    input_elements = example_edge_elements_from_client_map + example_node_elements_from_client_map
    client_names = example_client_name_message_map_client_relative_names
    user_journey_names = example_client_name_message_map_user_journey_relative_names
    # we don't patch utils.is_node_element since we want to assert the edge map was created correctly
    with patch(f"{patch_path}.remove_highlighted_class_from_edges") as mock_remove_highlighted_class_from_edges, \
        patch(f"{patch_path}.apply_highlighted_class_to_edges") as mock_apply_highlighted_class_from_edges:
        returned_elements = ujt.transformers.apply_highlighted_edge_class_to_elements(
            input_elements,
            user_journey_names[0])

        # assert edges map creation
        remove_highlighted_class_from_edges_call_args, _ = mock_remove_highlighted_class_from_edges.call_args
        assert len(remove_highlighted_class_from_edges_call_args) == 1

        edges_map = remove_highlighted_class_from_edges_call_args[0]
        assert len(edges_map[f"{client_names[0]}.{user_journey_names[0]}"]) == 2
        assert len(edges_map[f"{client_names[0]}.{user_journey_names[1]}"]) == 1
        assert len(edges_map[f"{client_names[1]}.{user_journey_names[2]}"]) == 1

        # following assertions don't test the output too robustly,
        # but we perform more rigorous testing in following tests
        # assert correct calls
        assert mock_remove_highlighted_class_from_edges.called
        assert mock_apply_highlighted_class_from_edges.called

        # since remove and apply highlighted class functions were mocked, they act as no-op
        # we can check if elements returned are the same
        assert_same_elements(
            returned_elements,
            example_edge_elements_from_client_map +
            example_node_elements_from_client_map)


def test_remove_highlighted_class_from_edges():
    edge_map = {"source_name": [{"classes": "some_class"}]}
    ujt.transformers.remove_highlighted_class_from_edges(edge_map)
    assert edge_map["source_name"][0]["classes"] == ""


def test_apply_highlighted_edge_class_to_edges():
    source_names = ["source0", "source1", "source2", "source3"]
    edge_map = defaultdict(
        list,
        {
            source_names[source_idx]: [
                {
                    "data": {
                        "target": source_names[source_idx + 1],
                    },
                    "classes": "",
                }
            ]
            for source_idx in range(len(source_names) - 1)
        })
    ujt.transformers.apply_highlighted_class_to_edges(edge_map, source_names[0])
    flattened_edges = [
        edge for edge_list in edge_map.values() for edge in edge_list
    ]
    assert all(
        ujt.constants.HIGHLIGHTED_UJ_EDGE_CLASS == edge["classes"]
        for edge in flattened_edges)


def test_apply_virtual_nodes_to_elements(patch_path, assert_same_elements):
    # Node0 and Node1 are in collapsed VirtualNode0
    # Node1 is a child of Node0
    # Node2 in collapsed VirtualNode1
    # Node0 has an edge to Node2
    # Node1 has an edge to Node2
    node_names = ["Node0", "Node1", "Node2"]
    virtual_node_names = ["VirtualNode0", "VirtualNode1"]
    node_elements = [
        {
            "data": {
                "ujt_id": node_names[0],
            },
        },
        {
            "data": {
                "ujt_id": node_names[1],
                "parent": node_names[0],
            },
        },
        {
            "data": {
                "ujt_id": node_names[2],
            },
        },
    ]
    edge_elements = [
        {
            "data": {
                "source": node_names[0],
                "target": node_names[2],
            },
        },
        {
            "data": {
                "source": node_names[1],
                "target": node_names[2],
            },
        },
    ]
    virtual_node_map = {
        # apply_virtual_nodes_to_edges doesn't actually access the value inside
        # the map, only the key. However, utils.get_highest_collapsed_virtual_node_name does.
        virtual_node_names[0]:
            VirtualNode(name=virtual_node_names[0],
                        collapsed=True),
        virtual_node_names[1]:
            VirtualNode(name=virtual_node_names[1],
                        collapsed=False),
    }
    parent_virtual_node_map = {
        node_names[0]: virtual_node_names[0],
        node_names[1]: virtual_node_names[0],
        node_names[2]: virtual_node_names[1],
    }

    expected_elements = [
        {
            "data": {
                "ujt_id": node_names[2],
                "parent": virtual_node_names[1],
            }
        },
        {
            "data":
                {
                    "source": virtual_node_names[0],
                    "target": node_names[2],
                    "id": f"{virtual_node_names[0]}/{node_names[2]}",
                },
        },
        {
            "data":
                {
                    "label": virtual_node_names[0],
                    "id": virtual_node_names[0],
                    "ujt_id": virtual_node_names[0],
                },
            "classes": "NODETYPE_VIRTUAL STATUS_UNSPECIFIED",
        },
        {
            "data":
                {
                    "label": virtual_node_names[1],
                    "id": virtual_node_names[1],
                    "ujt_id": virtual_node_names[1],
                },
            "classes": "NODETYPE_VIRTUAL STATUS_UNSPECIFIED",
        },
    ]

    with patch(f"{patch_path}.state.get_virtual_node_map", Mock(return_value=virtual_node_map)),\
        patch(f"{patch_path}.state.get_parent_virtual_node_map", Mock(return_value=parent_virtual_node_map)):
        returned_elements = ujt.transformers.apply_virtual_nodes_to_elements(
            node_elements + edge_elements)

        assert_same_elements(returned_elements, expected_elements)


def test_apply_uuid_to_elements(patch_path, assert_same_elements):
    node_names = ["Node0", "Node1"]
    node_elements = [
        {
            "data": {
                "id": node_names[0],
            },
        },
        {
            "data": {
                "id": node_names[1],
                "parent": node_names[0],
            },
        },
    ]
    edge_elements = [
        {
            "data":
                {
                    "id": f"{node_names[0]}.{node_names[1]}",
                    "source": node_names[0],
                    "target": node_names[1],
                },
        },
    ]
    expected_elements = [
        {
            "data": {
                "id": f"{node_names[0]}#uuid",
            },
        },
        {
            "data":
                {
                    "id": f"{node_names[1]}#uuid",
                    "parent": f"{node_names[0]}#uuid",
                },
        },
        {
            "data":
                {
                    "id": f"{node_names[0]}.{node_names[1]}#uuid",
                    "source": f"{node_names[0]}#uuid",
                    "target": f"{node_names[1]}#uuid",
                },
        },
    ]
    with patch(f"{patch_path}.uuid.uuid4", Mock(return_value="uuid")):
        returned_elements = ujt.transformers.apply_uuid_to_elements(
            node_elements + edge_elements)
        assert_same_elements(returned_elements, expected_elements)
