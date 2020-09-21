import pytest
from graph_structures_pb2 import (
    SLI,
    Client,
    Dependency,
    Node,
    NodeType,
    Status,
    UserJourney,
    SLIType,
)

import ujt.converters
import dash_bootstrap_components as dbc
from unittest.mock import patch, Mock

@pytest.fixture
def patch_path():
    return "ujt.converters"


@pytest.fixture
def current_path():
    return "tests.test_converters"


def test_cytoscape_elements_from_nodes():
    service_relative_names = ["Service0", "Service1"]
    endpoint_relative_names = ["Endpoint0", "Endpoint1", "Endpoint2"]

    node_name_message_map = {
        service_relative_names[0]:
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
        service_relative_names[1]:
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
        f"{service_relative_names[0]}.{endpoint_relative_names[0]}":
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
        f"{service_relative_names[0]}.{endpoint_relative_names[1]}":
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
        f"{service_relative_names[1]}.{endpoint_relative_names[2]}":
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
    }

    expected_node_elements = [
        {
            "data":
                {
                    "id": service_relative_names[0],
                    "label": service_relative_names[0],
                },
            "classes":
                f"{NodeType.Name(NodeType.NODETYPE_SERVICE)} {Status.Name(Status.STATUS_UNSPECIFIED)}"
        },
        {
            "data":
                {
                    "id": service_relative_names[1],
                    "label": service_relative_names[1],
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
                }
        },
        {
            "data":
                {
                    "source":
                        f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                    "target":
                        f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                }
        },
        {
            "data":
                {
                    "source":
                        f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                    "target":
                        f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                }
        },
    ]

    assert expected_node_elements + expected_edge_elements == ujt.converters.cytoscape_elements_from_nodes(
        node_name_message_map)


def test_cytoscape_elements_from_clients():
    client_relative_names = ["Client0", "Client1"]
    user_journey_relative_names = ["UJ0", "UJ1", "UJ2"]
    service_relative_names = ["Service0", "Service1", "Service2", "Service3"]

    client_name_message_map = {
        client_relative_names[0]:
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
        client_relative_names[1]:
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
            )
    }

    expected_node_elements = [
        {
            "data":
                {
                    "id": client_relative_names[0],
                    "label": client_relative_names[0]
                },
            "classes": ujt.converters.CLIENT_CLASS,
        },
        {
            "data":
                {
                    "id": client_relative_names[1],
                    "label": client_relative_names[1]
                },
            "classes": ujt.converters.CLIENT_CLASS,
        },
    ]

    expected_edge_elements = [
        {
            "data":
                {
                    "source": client_relative_names[0],
                    "target": service_relative_names[0],
                }
        },
        {
            "data":
                {
                    "source": client_relative_names[0],
                    "target": service_relative_names[1],
                }
        },
        {
            "data":
                {
                    "source": client_relative_names[0],
                    "target": service_relative_names[2],
                }
        },
        {
            "data":
                {
                    "source": client_relative_names[1],
                    "target": service_relative_names[3],
                }
        },
    ]

    assert expected_node_elements + expected_edge_elements == ujt.converters.cytoscape_elements_from_clients(
        client_name_message_map)


def test_bootstrap_info_table_from_nodes(patch_path, current_path):
    node = Node(name="node", status=Status.STATUS_HEALTHY)

    # assert dbc.Row() == dbc.Row() fails -- there are probably some unique internal fields being set
    # Thus, patch these calls to return a tuple of the args and kwargs instead of a real Row or Col object.
    with patch(f"{patch_path}.dbc.Row", Mock(side_effect=lambda *args, **kwargs: (args, kwargs))), \
        patch(f"{patch_path}.dbc.Col", Mock(side_effect=lambda *args, **kwargs: (args, kwargs))), \
        patch(f"{current_path}.dbc.Row", Mock(side_effect=lambda *args, **kwargs: (args, kwargs))), \
        patch(f"{current_path}.dbc.Col", Mock(side_effect=lambda *args, **kwargs: (args, kwargs))):
        expected_table = [
            dbc.Row(
                children=[
                    dbc.Col("Node"),
                    dbc.Col("Status"),
                ],
                className="header-row"
            ),
            dbc.Row(
                children=[
                    dbc.Col(node.name),
                    dbc.Col(
                        children="HEALTHY",
                        className="STATUS_HEALTHY",
                    ),
                ],
                className="data-row"
            )
        ]
        table = ujt.converters.bootstrap_info_table_from_nodes([node])
        assert table == expected_table

def test_bootstrap_info_table_from_slis(patch_path, current_path):
    sli = SLI(
        sli_type=SLIType.SLITYPE_UNSPECIFIED,
        sli_value=.511,
        slo_error_lower_bound=.1,
        slo_warn_lower_bound=.2,
        slo_warn_upper_bound=.8,
        slo_error_upper_bound=.9,
        status=Status.STATUS_HEALTHY,
    )

    # assert dbc.Row() == dbc.Row() fails -- there are probably some unique internal fields being set
    # Thus, patch these calls to return a tuple of the args and kwargs instead of a real Row or Col object.
    with patch(f"{patch_path}.dbc.Row", Mock(side_effect=lambda *args, **kwargs: (args, kwargs))), \
        patch(f"{patch_path}.dbc.Col", Mock(side_effect=lambda *args, **kwargs: (args, kwargs))), \
        patch(f"{current_path}.dbc.Row", Mock(side_effect=lambda *args, **kwargs: (args, kwargs))), \
        patch(f"{current_path}.dbc.Col", Mock(side_effect=lambda *args, **kwargs: (args, kwargs))):
        expected_table = [
            dbc.Row(
            children=[
                dbc.Col("SLI"),
                dbc.Col("SLI Type"),
                dbc.Col("SLI Status"),
                dbc.Col("Warn Range"),
                dbc.Col("Error Range"),
            ],
            className="header-row",
        ),
            dbc.Row(
            children=[
                dbc.Col("UNSPECIFIED"),
                dbc.Col(
                    children="HEALTHY",
                    className="STATUS_HEALTHY",
                ),
                dbc.Col(.51),
                dbc.Col(
                    f"({sli.slo_warn_lower_bound}, {sli.slo_warn_upper_bound})"
                ),
                dbc.Col(
                    f"({sli.slo_error_lower_bound}, {sli.slo_error_upper_bound})"
                ),
            ],
            className="data-row",
        )
        ]
        table = ujt.converters.bootstrap_info_table_from_slis([sli])
        assert table == expected_table
