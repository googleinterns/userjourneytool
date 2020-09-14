""" Tests for the main module. """

import tempfile
from unittest.mock import MagicMock, Mock, mock_open, patch, sentinel

import pytest

import ujt.main
from generated import graph_structures_pb2


@pytest.fixture
def patch_path():
    return "ujt.main"


def test_write_proto_to_file(patch_path):
    mock_path = MagicMock()
    mock_path.return_value.parent.parent.__truediv__.return_value.__truediv__.return_value = sentinel.path
    with patch(f"{patch_path}.open", mock_open()) as mock_open_func, \
        patch(f"{patch_path}.text_format.MessageToString") as mock_message_to_string, \
        patch(f"{patch_path}.pathlib.Path", mock_path):

        ujt.main.write_proto_to_file(sentinel.message)

        mock_message_to_string.assert_called_once_with(sentinel.message)
        mock_open_func.assert_called_once_with(sentinel.path, "w+")
        mock_open_func().write.assert_called_once_with(
            mock_message_to_string.return_value)


def test_read_proto_from_file(patch_path):
    mock_path = MagicMock()
    mock_path.return_value.parent.parent.__truediv__.return_value.__truediv__.return_value = sentinel.path

    mock_proto_instance = Mock()
    mock_proto_type = Mock(return_value=mock_proto_instance)

    with patch(f"{patch_path}.open", mock_open()) as mock_open_func, \
        patch(f"{patch_path}.text_format.Parse", Mock(return_value=sentinel.result)) as mock_parse, \
        patch(f"{patch_path}.pathlib.Path", mock_path):

        mock_open_func.return_value.read.return_value = sentinel.proto_text

        result = ujt.main.read_proto_from_file(sentinel.path, mock_proto_type)

        mock_open_func().read.assert_called_once()
        mock_parse.assert_called_once_with(sentinel.proto_text,
                                           mock_proto_instance)
        assert result == sentinel.result


def test_read_write_functional(patch_path, tmp_path):
    my_service = graph_structures_pb2.Service()
    filename = "temp"
    my_service.name = filename
    my_service.comment = "comment"

    mock_path = MagicMock(name="mockname")
    mock_path.return_value.parent.parent.__truediv__.return_value = tmp_path

    with patch(f"{patch_path}.pathlib.Path", mock_path):
        ujt.main.write_proto_to_file(my_service)
        service_from_file = ujt.main.read_proto_from_file(
            filename, graph_structures_pb2.Service)

    assert service_from_file == my_service
