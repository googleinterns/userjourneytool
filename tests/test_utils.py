""" Tests for the main module. """

from unittest.mock import MagicMock, Mock, mock_open, patch, sentinel

import pytest
from graph_structures_pb2 import Node, NodeType, Status

import ujt.converters
import ujt.utils


def test_is_client_cytoscape_node():
    non_client_node = {
        "classes": f"{NodeType.NODETYPE_SERVICE} {Status.STATUS_HEALTHY}"
    }
    assert not ujt.utils.is_client_cytoscape_node(non_client_node)

    client_node = {"classes": ujt.constants.CLIENT_CLASS}
    assert ujt.utils.is_client_cytoscape_node(client_node)


def test_relative_name():
    system_name, service_name, endpoint_name = "System", "Service", "Endpoint"
    assert (
        ujt.utils.relative_name(f"{system_name}.{service_name}.{endpoint_name}")
        == endpoint_name
    )

    assert ujt.utils.relative_name(system_name) == system_name


def test_human_readable_enum_name():
    assert (
        ujt.utils.human_readable_enum_name(Status.STATUS_HEALTHY, Status) == "HEALTHY"
    )
