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
    test_service_endpoint_name_map = {
        "Service1": ["Endpoint1", "Endpoint2"],
        "Service2": ["Endpoint3"],
    }
    test_node_dependency_map = {
        "Service1.Endpoint1": ["Service1.Endpoint2", "Service2.Endpoint3"],
        "Service1.Endpoint2": ["Service2.Endpoint3"],
        "Service2.Endpoint3": [],
    }
    expected_nodes = [
        Node(node_type=NodeType.NODETYPE_SERVICE,
             name="Service1",
             child_names=["Service1.Endpoint1", "Service1.Endpoint2"],
             slis=[
                 SLI(node_name="Service1",
                     sli_value=.5,
                     **ujt.generate_data.SLO_BOUNDS)
             ]),
        Node(node_type=NodeType.NODETYPE_SERVICE,
             name="Service2",
             child_names=["Service2.Endpoint3"],
             slis=[
                 SLI(node_name="Service2",
                     sli_value=.5,
                     **ujt.generate_data.SLO_BOUNDS)
             ]),
        Node(node_type=NodeType.NODETYPE_ENDPOINT,
             name="Service1.Endpoint1",
             parent_name="Service1",
             dependencies=[
                 Dependency(
                     target_name="Service1.Endpoint2",
                     source_name="Service1.Endpoint1",
                 ),
                 Dependency(target_name="Service2.Endpoint3",
                            source_name="Service1.Endpoint1")
             ],
             slis=[
                 SLI(node_name="Service1.Endpoint1",
                     sli_value=.5,
                     **ujt.generate_data.SLO_BOUNDS)
             ]),
        Node(node_type=NodeType.NODETYPE_ENDPOINT,
             name="Service1.Endpoint2",
             parent_name="Service1",
             dependencies=[
                 Dependency(
                     target_name="Service2.Endpoint3",
                     source_name="Service1.Endpoint2",
                 ),
             ],
             slis=[
                 SLI(node_name="Service1.Endpoint2",
                     sli_value=.5,
                     **ujt.generate_data.SLO_BOUNDS)
             ]),
        Node(node_type=NodeType.NODETYPE_ENDPOINT,
             name="Service2.Endpoint3",
             parent_name="Service2",
             slis=[
                 SLI(node_name="Service2.Endpoint3",
                     sli_value=.5,
                     **ujt.generate_data.SLO_BOUNDS)
             ]),
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
    test_client_user_journey_name_map = {
        "Client1": ["UJ1", "UJ2"],
        "Client2": ["UJ3"],
    }
    test_user_journey_dependency_map = {
        "Client1.UJ1": ["Service1", "Service2"],
        "Client1.UJ2": ["Service3"],
        "Client2.UJ3": ["Service4"],
    }
    expected_clients = [
        Client(
            name="Client1",
            user_journeys=[
                UserJourney(
                    name="Client1.UJ1",
                    client_name="Client1",
                    dependencies=[
                        Dependency(
                            target_name="Service1",
                            source_name="Client1.UJ1",
                            toplevel=True,
                        ),
                        Dependency(
                            target_name="Service2",
                            source_name="Client1.UJ1",
                            toplevel=True,
                        ),
                    ],
                ),
                UserJourney(
                    name="Client1.UJ2",
                    client_name="Client1",
                    dependencies=[
                        Dependency(
                            target_name="Service3",
                            source_name="Client1.UJ2",
                            toplevel=True,
                        ),
                    ],
                ),
            ],
        ),
        Client(
            name="Client2",
            user_journeys=[
                UserJourney(
                    name="Client2.UJ3",
                    client_name="Client2",
                    dependencies=[
                        Dependency(
                            target_name="Service4",
                            source_name="Client2.UJ3",
                            toplevel=True,
                        ),
                    ],
                ),
            ],
        )
    ]
    with patch(f"{patch_path}.CLIENT_USER_JOURNEY_NAME_MAP", test_client_user_journey_name_map), \
        patch(f"{patch_path}.USER_JOURNEY_DEPENDENCY_MAP", test_user_journey_dependency_map):
        clients = ujt.generate_data.generate_clients()
        # not the most elegant way to check list equality ignoring order,
        # but can't hash or sort Nodes. This should be fine for small test cases.
        print(clients)
        print("--")
        print(expected_clients)
        assert all([
            expected_client in clients for expected_client in expected_clients
        ])
        assert all(
            [actual_client in expected_clients for actual_client in clients])
