from unittest.mock import Mock, call, patch, sentinel

import pytest

import ujt.generate_data
from generated import graph_structures_pb2


@pytest.fixture
def patch_path():
    return "ujt.generate_data"


def test_save_mock_data(patch_path):
    with patch(f"{patch_path}.generate_clients", Mock(return_value=[sentinel.client])), \
        patch(f"{patch_path}.generate_services", Mock(return_value=[sentinel.service])), \
        patch(f"{patch_path}.utils.write_proto_to_file", Mock()) as mock_write_proto_to_file:
        ujt.generate_data.save_mock_data()

        assert mock_write_proto_to_file.mock_calls == [
            call(sentinel.client, graph_structures_pb2.Client),
            call(sentinel.service, graph_structures_pb2.Service),
        ]