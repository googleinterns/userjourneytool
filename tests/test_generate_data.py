from unittest.mock import Mock, call, patch, sentinel

import pytest

import ujt.generate_data
from generated.graph_structures_pb2 import (SLI, Client, Dependency, Node,
                                            NodeType, UserJourney)


@pytest.fixture
def patch_path():
    return "ujt.generate_data"


def test_save_mock_data(patch_path):
    mock_node, mock_client = Mock(), Mock()
    with patch(f"{patch_path}.generate_nodes", Mock(return_value=[mock_node])), \
        patch(f"{patch_path}.generate_clients", Mock(return_value=[mock_client])), \
        patch(f"{patch_path}.utils.named_proto_file_name", Mock(return_value=sentinel.named_proto_file_name)) as mock_named_proto_file_name, \
        patch(f"{patch_path}.utils.write_proto_to_file", Mock()) as mock_write_proto_to_file:
        ujt.generate_data.save_mock_data()

        assert mock_write_proto_to_file.mock_calls == [
            call(sentinel.named_proto_file_name, mock_node),
            call(sentinel.named_proto_file_name, mock_client),
        ]

        assert mock_named_proto_file_name.mock_calls == [
            call(mock_node.name, Node),
            call(mock_client.name, Client),
        ]


def test_generate_nodes_functional(patch_path):
    service_relative_names = ["Service0", "Service1"]
    endpoint_relative_names = ["Endpoint0", "Endpoint1", "Endpoint2"]

    test_service_endpoint_name_map = {
        service_relative_names[0]: [
            endpoint_relative_names[0], endpoint_relative_names[1]
        ],
        service_relative_names[1]: [endpoint_relative_names[2]],
    }
    test_node_dependency_map = {
        f"{service_relative_names[0]}.{endpoint_relative_names[0]}": [
            f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
            f"{service_relative_names[1]}.{endpoint_relative_names[2]}"
        ],
        f"{service_relative_names[0]}.{endpoint_relative_names[1]}": [
            f"{service_relative_names[1]}.{endpoint_relative_names[2]}"
        ],
        f"{service_relative_names[1]}.{endpoint_relative_names[2]}": [],
    }
    expected_nodes = [
        Node(
            node_type=NodeType.NODETYPE_SERVICE,
            name=service_relative_names[0],
            child_names=[
                f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                f"{service_relative_names[0]}.{endpoint_relative_names[1]}"
            ],
            slis=[
                SLI(
                    node_name=service_relative_names[0],
                    sli_value=.5,
                    **ujt.generate_data.SLO_BOUNDS,
                ),
            ],
        ),
        Node(
            node_type=NodeType.NODETYPE_SERVICE,
            name=service_relative_names[1],
            child_names=[
                f"{service_relative_names[1]}.{endpoint_relative_names[2]}"
            ],
            slis=[
                SLI(
                    node_name=service_relative_names[1],
                    sli_value=.5,
                    **ujt.generate_data.SLO_BOUNDS,
                ),
            ],
        ),
        Node(
            node_type=NodeType.NODETYPE_ENDPOINT,
            name=f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
            parent_name=service_relative_names[0],
            dependencies=[
                Dependency(
                    target_name=
                    f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                    source_name=
                    f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                ),
                Dependency(
                    target_name=
                    f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                    source_name=
                    f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                ),
            ],
            slis=[
                SLI(
                    node_name=
                    f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                    sli_value=.5,
                    **ujt.generate_data.SLO_BOUNDS,
                ),
            ],
        ),
        Node(
            node_type=NodeType.NODETYPE_ENDPOINT,
            name=f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
            parent_name=service_relative_names[0],
            dependencies=[
                Dependency(
                    target_name=
                    f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                    source_name=
                    f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                ),
            ],
            slis=[
                SLI(
                    node_name=
                    f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                    sli_value=.5,
                    **ujt.generate_data.SLO_BOUNDS,
                ),
            ],
        ),
        Node(
            node_type=NodeType.NODETYPE_ENDPOINT,
            name=f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
            parent_name=service_relative_names[1],
            slis=[
                SLI(
                    node_name=
                    f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                    sli_value=.5,
                    **ujt.generate_data.SLO_BOUNDS,
                ),
            ],
        ),
    ]
    with patch(f"{patch_path}.SERVICE_ENDPOINT_NAME_MAP", test_service_endpoint_name_map), \
        patch(f"{patch_path}.NODE_DEPENDENCY_MAP", test_node_dependency_map), \
        patch(f"{patch_path}.random.random", Mock(return_value=.5)):
        nodes = ujt.generate_data.generate_nodes()
        # not the most elegant way to check list equality ignoring order,
        # but can't hash or sort Nodes. This should be fine for small test cases.
        assert all([expected_node in nodes for expected_node in expected_nodes])
        assert all([actual_node in expected_nodes for actual_node in nodes])


def test_generate_clients_functional(patch_path):
    client_relative_names = ["Client0", "Client1"]
    user_journey_relative_names = ["UJ0", "UJ1", "UJ2"]
    service_relative_names = ["Service0", "Service1", "Service2", "Service3"]

    test_client_user_journey_name_map = {
        client_relative_names[0]: [
            user_journey_relative_names[0], user_journey_relative_names[1]
        ],
        client_relative_names[1]: [user_journey_relative_names[2]],
    }
    test_user_journey_dependency_map = {
        f"{client_relative_names[0]}.{user_journey_relative_names[0]}": [
            service_relative_names[0], service_relative_names[1]
        ],
        f"{client_relative_names[0]}.{user_journey_relative_names[1]}": [
            service_relative_names[2]
        ],
        f"{client_relative_names[1]}.{user_journey_relative_names[2]}": [
            service_relative_names[3]
        ],
    }
    expected_clients = [
        Client(
            name=client_relative_names[0],
            user_journeys=[
                UserJourney(
                    name=
                    f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
                    client_name=client_relative_names[0],
                    dependencies=[
                        Dependency(
                            target_name=service_relative_names[0],
                            source_name=
                            f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
                            toplevel=True,
                        ),
                        Dependency(
                            target_name=service_relative_names[1],
                            source_name=
                            f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
                            toplevel=True,
                        ),
                    ],
                ),
                UserJourney(
                    name=
                    f"{client_relative_names[0]}.{user_journey_relative_names[1]}",
                    client_name=client_relative_names[0],
                    dependencies=[
                        Dependency(
                            target_name=service_relative_names[2],
                            source_name=
                            f"{client_relative_names[0]}.{user_journey_relative_names[1]}",
                            toplevel=True,
                        ),
                    ],
                ),
            ],
        ),
        Client(
            name=client_relative_names[1],
            user_journeys=[
                UserJourney(
                    name=
                    f"{client_relative_names[1]}.{user_journey_relative_names[2]}",
                    client_name=client_relative_names[1],
                    dependencies=[
                        Dependency(
                            target_name=service_relative_names[3],
                            source_name=
                            f"{client_relative_names[1]}.{user_journey_relative_names[2]}",
                            toplevel=True,
                        ),
                    ],
                ),
            ],
        ),
    ]
    with patch(f"{patch_path}.CLIENT_USER_JOURNEY_NAME_MAP", test_client_user_journey_name_map), \
        patch(f"{patch_path}.USER_JOURNEY_DEPENDENCY_MAP", test_user_journey_dependency_map):
        clients = ujt.generate_data.generate_clients()
        # not the most elegant way to check list equality ignoring order,
        # but can't hash or sort Nodes. This should be fine for small test cases.
        assert all([
            expected_client in clients for expected_client in expected_clients
        ])
        assert all(
            [actual_client in expected_clients for actual_client in clients])
