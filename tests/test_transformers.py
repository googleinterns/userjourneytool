# pylint: disable=redefined-outer-name

from unittest.mock import Mock, patch

import pytest
from graph_structures_pb2 import Client, Node, NodeType, Status, VirtualNode

import ujt.constants
import ujt.transformers


@pytest.fixture
def patch_path():
    return "ujt.transformers"


def test_apply_node_property_classes(assert_same_elements):
    node_name = "node"
    node_name_message_map = {
        node_name: Node(
            name=node_name,
            status=Status.STATUS_HEALTHY,
            node_type=NodeType.NODETYPE_SERVICE,
        ),
    }
    client_name = "client"
    client_name_message_map = {
        client_name: Client(
            name=client_name,
        ),
    }
    virtual_node_name = "virtual_node"
    virtual_node_name_message_map = {
        virtual_node_name: VirtualNode(
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
            "classes": "",
        },
        {
            "data": {
                "ujt_id": client_name,
            },
            "classes": "",
        },
        {
            "data": {
                "ujt_id": virtual_node_name,
            },
            "classes": "",
        },
    ]

    expected_elements = [
        {
            "data": {
                "ujt_id": node_name,
            },
            "classes": " NODETYPE_SERVICE STATUS_HEALTHY",
        },
        {
            "data": {
                "ujt_id": client_name,
            },
            "classes": f" {ujt.constants.CLIENT_CLASS}",
        },
        {
            "data": {
                "ujt_id": virtual_node_name,
            },
            "classes": " NODETYPE_VIRTUAL STATUS_HEALTHY",
        },
    ]

    returned_elements = ujt.transformers.apply_node_property_classes(
        elements,
        node_name_message_map,
        client_name_message_map,
        virtual_node_name_message_map,
    )
    assert_same_elements(returned_elements, expected_elements)


def test_apply_highlighted_edge_class_to_elements():
    # Node0 connects to Node1 which connects to Node2 (UJ0)
    # Node0 connects to Node3 (UJ1)
    node_names = ["Node0", "Node1", "Node2", "Node3"]
    user_journey_names = ["UJ0", "UJ1"]
    elements = [
        {
            "data": {
                "source": node_names[0],
                "target": node_names[1],
                "user_journey_name": user_journey_names[0],
            },
            "classes": "",
        },
        {
            "data": {
                "source": node_names[1],
                "target": node_names[2],
            },
            "classes": "",
        },
        {
            "data": {
                "source": node_names[0],
                "target": node_names[3],
                "user_journey_name": user_journey_names[1],
            },
            "classes": "",
        },
    ]
    new_elements = ujt.transformers.apply_highlighted_edge_class_to_elements(
        elements, user_journey_names[0]
    )
    for e in new_elements:
        if (
            e["data"]["source"] == node_names[0]
            and e["data"]["target"] == node_names[3]
        ):
            assert ujt.constants.HIGHLIGHTED_UJ_EDGE_CLASS not in e["classes"]
        else:
            assert ujt.constants.HIGHLIGHTED_UJ_EDGE_CLASS in e["classes"]


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
            "classes": "",
        },
        {
            "data": {
                "ujt_id": node_names[1],
                "parent": node_names[0],
            },
            "classes": "",
        },
        {
            "data": {
                "ujt_id": node_names[2],
            },
            "classes": "",
        },
    ]
    edge_elements = [
        {
            "data": {
                "source": node_names[0],
                "target": node_names[2],
            },
            "classes": "",
        },
        {
            "data": {
                "source": node_names[1],
                "target": node_names[2],
            },
            "classes": "",
        },
    ]
    virtual_node_map = {
        # apply_virtual_nodes_to_edges doesn't actually access the value inside
        # the map, only the key. However, utils.get_highest_collapsed_virtual_node_name does.
        virtual_node_names[0]: VirtualNode(name=virtual_node_names[0], collapsed=True),
        virtual_node_names[1]: VirtualNode(name=virtual_node_names[1], collapsed=False),
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
            },
            "classes": "",
        },
        {
            "data": {
                "source": virtual_node_names[0],
                "target": node_names[2],
                "id": f"{virtual_node_names[0]}/{node_names[2]}",
            },
            "classes": "",
        },
        {
            "data": {
                "label": virtual_node_names[0],
                "id": virtual_node_names[0],
                "ujt_id": virtual_node_names[0],
            },
            "classes": "",
        },
        {
            "data": {
                "label": virtual_node_names[1],
                "id": virtual_node_names[1],
                "ujt_id": virtual_node_names[1],
            },
            "classes": "",
        },
    ]

    with patch(
        f"{patch_path}.state.get_virtual_node_map", Mock(return_value=virtual_node_map)
    ), patch(
        f"{patch_path}.state.get_parent_virtual_node_map",
        Mock(return_value=parent_virtual_node_map),
    ):
        returned_elements = ujt.transformers.apply_virtual_nodes_to_elements(
            node_elements + edge_elements
        )
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
            "data": {
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
            "data": {
                "id": f"{node_names[1]}#uuid",
                "parent": f"{node_names[0]}#uuid",
            },
        },
        {
            "data": {
                "id": f"{node_names[0]}.{node_names[1]}#uuid",
                "source": f"{node_names[0]}#uuid",
                "target": f"{node_names[1]}#uuid",
            },
        },
    ]
    with patch(f"{patch_path}.uuid.uuid4", Mock(return_value="uuid")):
        returned_elements = ujt.transformers.apply_uuid_to_elements(
            node_elements + edge_elements
        )
        assert_same_elements(returned_elements, expected_elements)


def test_sort_nodes_by_parent_relationship():
    node_names = ["Node0", "Node1", "Node2", "Node3", "Node4"]
    # Node0 contains Node1 and Node2
    # Node1 contains Node3
    # Node2 contains Node4
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
        {
            "data": {
                "id": node_names[2],
                "parent": node_names[0],
            },
        },
        {
            "data": {
                "id": node_names[3],
                "parent": node_names[1],
            },
        },
        {
            "data": {
                "id": node_names[4],
                "parent": node_names[2],
            },
        },
    ]
    # We declare the input in topological order so it's easier to understand
    # Reverse so it's in reverse topological order
    reversed_node_elements = node_elements[::-1]

    edge_elements = [
        {
            "data": {
                "source": node_names[0],
                "target": node_names[1],
                "id": f"{node_names[0]}/{node_names[1]}",
            },
        },
    ]

    returned_elements = ujt.transformers.sort_nodes_by_parent_relationship(
        reversed_node_elements + edge_elements
    )

    expected_elements = [
        {
            "data": {
                "source": f"{node_names[0]}",
                "target": f"{node_names[1]}",
                "id": f"{node_names[0]}/{node_names[1]}",
            }
        },
        {"data": {"id": f"{node_names[0]}"}},
        {"data": {"id": f"{node_names[1]}", "parent": f"{node_names[0]}"}},
        {"data": {"id": f"{node_names[2]}", "parent": f"{node_names[0]}"}},
        {"data": {"id": f"{node_names[3]}", "parent": f"{node_names[1]}"}},
        {"data": {"id": f"{node_names[4]}", "parent": f"{node_names[2]}"}},
    ]

    assert returned_elements == expected_elements
