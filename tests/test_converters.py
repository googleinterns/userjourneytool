import pytest

import ujt.converters
from generated.graph_structures_pb2 import (SLI, Client, Dependency, Node,
                                            NodeType, UserJourney)


@pytest.fixture
def patch_path():
    return "ujt.converters"


def test_cytoscape_elements_from_nodes():
    node_name_message_map = {
        "Service1":
            Node(node_type=NodeType.NODETYPE_SERVICE,
                 name="Service1",
                 child_names=["Service1.Endpoint1", "Service1.Endpoint2"],
                 slis=[
                     SLI(node_name="Service1",
                         sli_value=.5,
                         **ujt.generate_data.SLO_BOUNDS)
                 ]),
        "Service2":
            Node(node_type=NodeType.NODETYPE_SERVICE,
                 name="Service2",
                 child_names=["Service2.Endpoint3"],
                 slis=[
                     SLI(node_name="Service2",
                         sli_value=.5,
                         **ujt.generate_data.SLO_BOUNDS)
                 ]),
        "Service1.Endpoint1":
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
        "Service1.Endpoint2":
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
        "Service2.Endpoint3":
            Node(node_type=NodeType.NODETYPE_ENDPOINT,
                 name="Service2.Endpoint3",
                 parent_name="Service2",
                 slis=[
                     SLI(node_name="Service2.Endpoint3",
                         sli_value=.5,
                         **ujt.generate_data.SLO_BOUNDS)
                 ]),
    }

    expected_node_elements = [
        {
            "data": {
                "id": "Service1",
                "label": "Service1"
            },
            "classes": "NODETYPE_SERVICE STATUS_UNSPECIFIED"
        },
        {
            "data": {
                "id": "Service2",
                "label": "Service2"
            },
            "classes": "NODETYPE_SERVICE STATUS_UNSPECIFIED"
        },
        {
            "data": {
                "id": "Service1.Endpoint1",
                "label": "Endpoint1",
                "parent": "Service1",
            },
            "classes": "NODETYPE_ENDPOINT STATUS_UNSPECIFIED"
        },
        {
            "data": {
                "id": "Service1.Endpoint2",
                "label": "Endpoint2",
                "parent": "Service1",
            },
            "classes": "NODETYPE_ENDPOINT STATUS_UNSPECIFIED"
        },
        {
            "data": {
                "id": "Service2.Endpoint3",
                "label": "Endpoint3",
                "parent": "Service2",
            },
            "classes": "NODETYPE_ENDPOINT STATUS_UNSPECIFIED"
        },
    ]

    expected_edge_elements = [
        {
            "data": {
                "source": "Service1.Endpoint1",
                "target": "Service1.Endpoint2",
            }
        },
        {
            "data": {
                "source": "Service1.Endpoint1",
                "target": "Service2.Endpoint3",
            }
        },
        {
            "data": {
                "source": "Service1.Endpoint2",
                "target": "Service2.Endpoint3",
            }
        },
    ]

    assert expected_node_elements + expected_edge_elements == ujt.converters.cytoscape_elements_from_nodes(
        node_name_message_map)


def test_cytoscape_elements_from_clients():
    client_name_message_map = {
        "Client1":
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
        "Client2":
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
    }

    expected_node_elements = [
        {
            "data": {
                "id": "Client1",
                "label": "Client1"
            },
            "classes": "client"
        },
        {
            "data": {
                "id": "Client2",
                "label": "Client2"
            },
            "classes": "client"
        },
    ]

    expected_edge_elements = [
        {
            "data": {
                "source": "Client1",
                "target": "Service1",
            }
        },
        {
            "data": {
                "source": "Client1",
                "target": "Service2",
            }
        },
        {
            "data": {
                "source": "Client1",
                "target": "Service3",
            }
        },
        {
            "data": {
                "source": "Client2",
                "target": "Service4",
            }
        },
    ]

    assert expected_node_elements + expected_edge_elements == ujt.converters.cytoscape_elements_from_clients(
        client_name_message_map)
