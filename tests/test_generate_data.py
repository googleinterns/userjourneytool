from unittest.mock import Mock, call, patch, sentinel

import pytest

import ujt.generate_data
from generated import graph_structures_pb2


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
            call(mock_node.name, graph_structures_pb2.Node),
            call(mock_client.name, graph_structures_pb2.Client),
        ]
