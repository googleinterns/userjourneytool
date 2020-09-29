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


def test_cytoscape_elements_from_node_map(
    slo_bounds,
    example_node_name_message_map,
    example_node_name_message_map_service_relative_names,
    example_node_name_message_map_endpoint_relative_names,
):
    service_relative_names = example_node_name_message_map_service_relative_names
    endpoint_relative_names = example_node_name_message_map_endpoint_relative_names

    expected_node_elements = [
        {
            "data":
                {
                    "id": service_relative_names[0],
                    "label": service_relative_names[0],
                    "ujt_id": service_relative_names[0],
                },
            "classes":
                f"{NodeType.Name(NodeType.NODETYPE_SERVICE)} {Status.Name(Status.STATUS_UNSPECIFIED)}"
        },
        {
            "data":
                {
                    "id": service_relative_names[1],
                    "label": service_relative_names[1],
                    "ujt_id": service_relative_names[1],
                },
            "classes":
                f"{NodeType.Name(NodeType.NODETYPE_SERVICE)} {Status.Name(Status.STATUS_UNSPECIFIED)}"
        },
        {
            "data":
                {
                    "id":
                        f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                    "label":
                        endpoint_relative_names[0],
                    "parent":
                        service_relative_names[0],
                    "ujt_id":
                        f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                },
            "classes":
                f"{NodeType.Name(NodeType.NODETYPE_ENDPOINT)} {Status.Name(Status.STATUS_UNSPECIFIED)}"
        },
        {
            "data":
                {
                    "id":
                        f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                    "label":
                        endpoint_relative_names[1],
                    "parent":
                        service_relative_names[0],
                    "ujt_id":
                        f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                },
            "classes":
                f"{NodeType.Name(NodeType.NODETYPE_ENDPOINT)} {Status.Name(Status.STATUS_UNSPECIFIED)}"
        },
        {
            "data":
                {
                    "id":
                        f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                    "label":
                        endpoint_relative_names[2],
                    "parent":
                        service_relative_names[1],
                    "ujt_id":
                        f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                },
            "classes":
                f"{NodeType.Name(NodeType.NODETYPE_ENDPOINT)} {Status.Name(Status.STATUS_UNSPECIFIED)}"
        },
    ]

    expected_edge_elements = [
        {
            "data":
                {
                    "source":
                        f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                    "target":
                        f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                    "id":
                        f"{service_relative_names[0]}.{endpoint_relative_names[0]}/{service_relative_names[0]}.{endpoint_relative_names[1]}",
                }
        },
        {
            "data":
                {
                    "source":
                        f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                    "target":
                        f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                    "id":
                        f"{service_relative_names[0]}.{endpoint_relative_names[0]}/{service_relative_names[1]}.{endpoint_relative_names[2]}",
                }
        },
        {
            "data":
                {
                    "source":
                        f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                    "target":
                        f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                    "id":
                        f"{service_relative_names[0]}.{endpoint_relative_names[1]}/{service_relative_names[1]}.{endpoint_relative_names[2]}",
                }
        },
    ]

    assert expected_node_elements + expected_edge_elements == ujt.converters.cytoscape_elements_from_node_map(
        example_node_name_message_map)


def test_cytoscape_elements_from_client_map(
    slo_bounds,
    example_client_name_message_map,
    example_client_name_message_map_client_relative_names,
    example_client_name_message_map_user_journey_relative_names,
    example_client_name_message_map_service_relative_names,
):
    client_relative_names = example_client_name_message_map_client_relative_names
    user_journey_relative_names = example_client_name_message_map_user_journey_relative_names
    service_relative_names = example_client_name_message_map_service_relative_names

    expected_node_elements = [
        {
            "data":
                {
                    "id": client_relative_names[0],
                    "label": client_relative_names[0],
                    "ujt_id": client_relative_names[0],
                },
            "classes": ujt.constants.CLIENT_CLASS,
        },
        {
            "data":
                {
                    "id": client_relative_names[1],
                    "label": client_relative_names[1],
                    "ujt_id": client_relative_names[1],
                },
            "classes": ujt.constants.CLIENT_CLASS,
        },
    ]

    expected_edge_elements = [
        {
            "data":
                {
                    "source":
                        client_relative_names[0],
                    "target":
                        service_relative_names[0],
                    "id":
                        f"{client_relative_names[0]}/{service_relative_names[0]}",
                    "user_journey_name":
                        f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
                }
        },
        {
            "data":
                {
                    "source":
                        client_relative_names[0],
                    "target":
                        service_relative_names[1],
                    "id":
                        f"{client_relative_names[0]}/{service_relative_names[1]}",
                    "user_journey_name":
                        f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
                }
        },
        {
            "data":
                {
                    "source":
                        client_relative_names[0],
                    "target":
                        service_relative_names[2],
                    "id":
                        f"{client_relative_names[0]}/{service_relative_names[2]}",
                    "user_journey_name":
                        f"{client_relative_names[0]}.{user_journey_relative_names[1]}",
                }
        },
        {
            "data":
                {
                    "source":
                        client_relative_names[1],
                    "target":
                        service_relative_names[3],
                    "id":
                        f"{client_relative_names[1]}/{service_relative_names[3]}",
                    "user_journey_name":
                        f"{client_relative_names[1]}.{user_journey_relative_names[2]}",
                }
        },
    ]

    assert expected_node_elements + expected_edge_elements == ujt.converters.cytoscape_elements_from_client_map(
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

    assert table.id == {"datatable-id": table_id}  # pylint: disable=no-member
    assert table.columns == expected_columns  # pylint: disable=no-member
    assert table.data == expected_data  # pylint: disable=no-member
    assert table.style_data_conditional == ujt.constants.DATATABLE_CONDITIONAL_STYLE  # pylint: disable=no-member
