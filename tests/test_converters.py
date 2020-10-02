import pytest
from graph_structures_pb2 import (
    SLI,
    Client,
    Dependency,
    Node,
    NodeType,
    SLIType,
    Status,
    UserJourney)

import ujt.constants
import ujt.converters

# TODO: write individual test cases for cytoscape_element_from_node, client, dependency
# They are currently exercised through test_cytoscape_elements_from_node_map and
# test_cytoscape_elements_from_client map, but should be tested on their own as well.


def test_cytoscape_elements_from_node_map(
    example_node_name_message_map,
    example_node_elements_from_node_map,
    example_edge_elements_from_node_map,
):
    assert example_node_elements_from_node_map + example_edge_elements_from_node_map == ujt.converters.cytoscape_elements_from_node_map(
        example_node_name_message_map)


def test_cytoscape_elements_from_client_map(
    example_client_name_message_map,
    example_node_elements_from_client_map,
    example_edge_elements_from_client_map,
):
    assert example_node_elements_from_client_map + example_edge_elements_from_client_map == ujt.converters.cytoscape_elements_from_client_map(
        example_client_name_message_map)


def test_datatable_from_nodes():
    node = Node(name="node", status=Status.STATUS_HEALTHY)
    table_id = "test-table"

    expected_columns = [
        {
            "name": "Node",
            "id": "Node"
        },
        {
            "name": "Status",
            "id": "Status"
        },
    ]
    expected_data = [{
        "Node": node.name,
        "Status": "HEALTHY",
    }]

    table = ujt.converters.datatable_from_nodes(
        [node],
        use_relative_names=False,
        table_id=table_id,
    )

    assert table.id == table_id  # pylint: disable=no-member
    assert table.columns == expected_columns  # pylint: disable=no-member
    assert table.data == expected_data  # pylint: disable=no-member
    assert table.style_data_conditional == ujt.constants.DATATABLE_CONDITIONAL_STYLE  # pylint: disable=no-member


def test_datatable_from_slis():
    sli = SLI(
        sli_type=SLIType.SLITYPE_UNSPECIFIED,
        sli_value=.511,
        slo_error_lower_bound=.1,
        slo_warn_lower_bound=.2,
        slo_warn_upper_bound=.8,
        slo_error_upper_bound=.9,
        status=Status.STATUS_HEALTHY,
    )
    table_id = "test-table"

    expected_columns = [
        {
            "name": "Type",
            "id": "Type"
        },
        {
            "name": "Status",
            "id": "Status"
        },
        {
            "name": "Value",
            "id": "Value"
        },
        {
            "name": "Warn Range",
            "id": "Warn Range"
        },
        {
            "name": "Error Range",
            "id": "Error Range"
        },
    ]
    expected_data = [
        {
            "Type": "UNSPECIFIED",
            "Status": "HEALTHY",
            "Value": .51,
            "Warn Range": "(0.2, 0.8)",
            "Error Range": "(0.1, 0.9)",
        }
    ]

    table = ujt.converters.datatable_from_slis([sli], table_id=table_id)

    assert table.id == table_id  # pylint: disable=no-member
    assert table.columns == expected_columns  # pylint: disable=no-member
    assert table.data == expected_data  # pylint: disable=no-member
    assert table.style_data_conditional == ujt.constants.DATATABLE_CONDITIONAL_STYLE  # pylint: disable=no-member


def test_datatable_from_client():
    client = Client(
        name="client",
        user_journeys=[
            UserJourney(
                name="client.uj",
                status=Status.STATUS_HEALTHY,
            ),
        ],
    )
    table_id = "test-table"

    expected_columns = [
        {
            "name": "User Journey",
            "id": "User Journey"
        },
        {
            "name": "Status",
            "id": "Status"
        },
    ]
    expected_data = [
        {
            "User Journey": "uj",
            "Status": "HEALTHY",
            "id": client.user_journeys[0].name,
        }
    ]

    table = ujt.converters.datatable_from_client(
        client,
        table_id=table_id,
    )

    assert table.id == {table_id: table_id}  # pylint: disable=no-member
    assert table.columns == expected_columns  # pylint: disable=no-member
    assert table.data == expected_data  # pylint: disable=no-member
    assert table.style_data_conditional == ujt.constants.DATATABLE_CONDITIONAL_STYLE  # pylint: disable=no-member
