from unittest.mock import MagicMock, Mock, call, patch, sentinel

import pytest
from graph_structures_pb2 import Node

import ujt.server.server_utils


@pytest.fixture
def patch_path():
    return "ujt.server.server_utils"


def test_named_proto_file_name():
    mock_proto_type = MagicMock(__name__=sentinel.type)
    assert (
        ujt.server.server_utils.named_proto_file_name(sentinel.name, mock_proto_type)
        == "sentinel.type_sentinel.name.ujtdata"
    )


def test_write_proto_to_file(patch_path):
    mock_path = Mock()

    with patch(f"{patch_path}.text_format.MessageToString") as mock_message_to_string:
        ujt.server.server_utils.write_proto_to_file(mock_path, sentinel.message)

        mock_message_to_string.assert_called_once_with(sentinel.message)
        mock_path.write_text.assert_called_once_with(
            mock_message_to_string.return_value
        )


def test_read_proto_from_file(patch_path):
    mock_path = Mock()
    mock_proto_type = Mock()

    with patch(
        f"{patch_path}.text_format.Parse", Mock(return_value=sentinel.result)
    ) as mock_parse:
        ujt.server.server_utils.read_proto_from_file(mock_path, mock_proto_type)

        assert mock_path.read_text.mock_calls == [call()]
        mock_parse.assert_called_once_with(
            mock_path.read_text.return_value, mock_proto_type.return_value
        )


def test_read_write_functional(patch_path, tmp_path):
    node = Node()
    node.name = "name"
    node.comment = "comment"

    ujt.server.server_utils.write_proto_to_file(
        tmp_path / ujt.server.server_utils.named_proto_file_name(node.name, Node),
        node,
    )
    service_from_file = ujt.server.server_utils.read_proto_from_file(
        tmp_path / ujt.server.server_utils.named_proto_file_name(node.name, Node),
        Node,
    )

    assert service_from_file == node
