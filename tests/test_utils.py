""" Tests for the main module. """

from unittest.mock import MagicMock, Mock, mock_open, patch, sentinel

import pytest

import ujt.utils
from generated import graph_structures_pb2


@pytest.fixture
def patch_path():
    return "ujt.utils"


def test_named_proto_file_name():
    mock_proto_type = MagicMock(__name__=sentinel.type)
    assert ujt.utils.named_proto_file_name(
        sentinel.name, mock_proto_type) == "sentinel.type_sentinel.name"


def test_write_proto_to_file(patch_path):
    mock_path = MagicMock()
    mock_path.return_value.parent.parent.__truediv__.return_value.__truediv__.return_value = sentinel.path

    with patch(f"{patch_path}.open", mock_open()) as mock_open_func, \
        patch(f"{patch_path}.text_format.MessageToString") as mock_message_to_string, \
        patch(f"{patch_path}.pathlib.Path", mock_path):

        ujt.utils.write_proto_to_file(sentinel.name, sentinel.message)

        mock_message_to_string.assert_called_once_with(sentinel.message)
        mock_open_func.assert_called_once_with(sentinel.path, "w+")
        mock_open_func().write.assert_called_once_with(
            mock_message_to_string.return_value)


def test_read_proto_from_file(patch_path):
    mock_path = MagicMock()
    mock_path.return_value.parent.parent.__truediv__.return_value.__truediv__.return_value = sentinel.path

    mock_proto_instance = Mock()
    mock_proto_type = MagicMock(__name__=sentinel.type,
                                return_value=mock_proto_instance)

    with patch(f"{patch_path}.open", mock_open()) as mock_open_func, \
        patch(f"{patch_path}.text_format.Parse", Mock(return_value=sentinel.result)) as mock_parse, \
        patch(f"{patch_path}.pathlib.Path", mock_path):

        mock_open_func.return_value.read.return_value = sentinel.proto_text

        result = ujt.utils.read_proto_from_file(sentinel.name, mock_proto_type)

        mock_open_func().read.assert_called_once()
        mock_parse.assert_called_once_with(sentinel.proto_text,
                                           mock_proto_instance)
        assert result == sentinel.result


def test_read_write_functional(patch_path, tmp_path):
    node = graph_structures_pb2.Node()
    node.name = "name"
    node.comment = "comment"

    mock_path = MagicMock()
    mock_path.return_value.parent.parent.__truediv__.return_value = tmp_path

    with patch(f"{patch_path}.pathlib.Path", mock_path):
        ujt.utils.write_proto_to_file("sentinel.file_name", node)
        service_from_file = ujt.utils.read_proto_from_file(
            "sentinel.file_name",
            graph_structures_pb2.Node,
        )

    assert service_from_file == node
