# pylint: disable=redefined-outer-name

import pytest
from graph_structures_pb2 import (
    SLI,
    Client,
    Dependency,
    Node,
    NodeType,
    Status,
    UserJourney,
)

import ujt.constants


@pytest.fixture
def assert_same_elements():
    def inner_assert_same_elements(list1, list2):
        """Asserts that two lists have the same elements, regardless of order.

        We use this approach for unhashable and uncomparable types, e.g. proto messages.

        Args:
            list1: First list to assert.
            list2: Second list to assert.
        """
        # although it's slower/not strictly necessary to wrap the generator in
        # a list, pytest will give a more informative error message this way.
        assert all([element1 in list2 for element1 in list1])
        assert all([element2 in list1 for element2 in list2])

    return inner_assert_same_elements


@pytest.fixture
def slo_bounds():
    return {
        "slo_error_lower_bound": 0.1,
        "slo_warn_lower_bound": 0.2,
        "slo_warn_upper_bound": 0.8,
        "slo_error_upper_bound": 0.9,
    }


""" Example Node name message map data:
Service0 has children Endpoint0 and Endpoint1
Service1 has child Endpoint2

Endpoint0 depends on Endpoint1 and Endpoint2
Endpoint1 depends on Endpoint2
"""


@pytest.fixture
def example_node_name_message_map_service_relative_names():
    service_relative_names = ["Service0", "Service1"]
    return service_relative_names


@pytest.fixture
def example_node_name_message_map_endpoint_relative_names():
    endpoint_relative_names = ["Endpoint0", "Endpoint1", "Endpoint2"]
    return endpoint_relative_names


@pytest.fixture
def example_node_name_message_map(
    slo_bounds,
    example_node_name_message_map_service_relative_names,
    example_node_name_message_map_endpoint_relative_names,
):
    service_relative_names = example_node_name_message_map_service_relative_names
    endpoint_relative_names = example_node_name_message_map_endpoint_relative_names
    node_name_message_map = {
        service_relative_names[0]: Node(
            node_type=NodeType.NODETYPE_SERVICE,
            name=service_relative_names[0],
            child_names=[
                f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
            ],
            slis=[
                SLI(
                    node_name=service_relative_names[0],
                    sli_value=0.5,
                    **slo_bounds,
                ),
            ],
        ),
        service_relative_names[1]: Node(
            node_type=NodeType.NODETYPE_SERVICE,
            name=service_relative_names[1],
            child_names=[f"{service_relative_names[1]}.{endpoint_relative_names[2]}"],
            slis=[
                SLI(
                    node_name=service_relative_names[1],
                    sli_value=0.5,
                    **slo_bounds,
                ),
            ],
        ),
        f"{service_relative_names[0]}.{endpoint_relative_names[0]}": Node(
            node_type=NodeType.NODETYPE_ENDPOINT,
            name=f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
            parent_name=service_relative_names[0],
            dependencies=[
                Dependency(
                    target_name=f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                    source_name=f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                ),
                Dependency(
                    target_name=f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                    source_name=f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                ),
            ],
            slis=[
                SLI(
                    node_name=f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                    sli_value=0.5,
                    **slo_bounds,
                ),
            ],
        ),
        f"{service_relative_names[0]}.{endpoint_relative_names[1]}": Node(
            node_type=NodeType.NODETYPE_ENDPOINT,
            name=f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
            parent_name=service_relative_names[0],
            dependencies=[
                Dependency(
                    target_name=f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                    source_name=f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                ),
            ],
            slis=[
                SLI(
                    node_name=f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                    sli_value=0.5,
                    **slo_bounds,
                ),
            ],
        ),
        f"{service_relative_names[1]}.{endpoint_relative_names[2]}": Node(
            node_type=NodeType.NODETYPE_ENDPOINT,
            name=f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
            parent_name=service_relative_names[1],
            slis=[
                SLI(
                    node_name=f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                    sli_value=0.5,
                    **slo_bounds,
                ),
            ],
        ),
    }
    return node_name_message_map


@pytest.fixture
def example_node_elements_from_node_map(
    example_node_name_message_map_service_relative_names,
    example_node_name_message_map_endpoint_relative_names,
):
    service_relative_names = example_node_name_message_map_service_relative_names
    endpoint_relative_names = example_node_name_message_map_endpoint_relative_names

    expected_node_elements = [
        {
            "data": {
                "id": service_relative_names[0],
                "label": service_relative_names[0],
                "ujt_id": service_relative_names[0],
            },
        },
        {
            "data": {
                "id": service_relative_names[1],
                "label": service_relative_names[1],
                "ujt_id": service_relative_names[1],
            },
        },
        {
            "data": {
                "id": f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                "label": endpoint_relative_names[0],
                "parent": service_relative_names[0],
                "ujt_id": f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
            },
        },
        {
            "data": {
                "id": f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                "label": endpoint_relative_names[1],
                "parent": service_relative_names[0],
                "ujt_id": f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
            },
        },
        {
            "data": {
                "id": f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                "label": endpoint_relative_names[2],
                "parent": service_relative_names[1],
                "ujt_id": f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
            },
        },
    ]
    return expected_node_elements


@pytest.fixture
def example_edge_elements_from_node_map(
    example_node_name_message_map_service_relative_names,
    example_node_name_message_map_endpoint_relative_names,
):
    service_relative_names = example_node_name_message_map_service_relative_names
    endpoint_relative_names = example_node_name_message_map_endpoint_relative_names

    expected_edge_elements = [
        {
            "data": {
                "source": f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                "target": f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                "id": f"{service_relative_names[0]}.{endpoint_relative_names[0]}/{service_relative_names[0]}.{endpoint_relative_names[1]}",
                "ujt_id": f"{service_relative_names[0]}.{endpoint_relative_names[0]}/{service_relative_names[0]}.{endpoint_relative_names[1]}",
            }
        },
        {
            "data": {
                "source": f"{service_relative_names[0]}.{endpoint_relative_names[0]}",
                "target": f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                "id": f"{service_relative_names[0]}.{endpoint_relative_names[0]}/{service_relative_names[1]}.{endpoint_relative_names[2]}",
                "ujt_id": f"{service_relative_names[0]}.{endpoint_relative_names[0]}/{service_relative_names[1]}.{endpoint_relative_names[2]}",
            }
        },
        {
            "data": {
                "source": f"{service_relative_names[0]}.{endpoint_relative_names[1]}",
                "target": f"{service_relative_names[1]}.{endpoint_relative_names[2]}",
                "id": f"{service_relative_names[0]}.{endpoint_relative_names[1]}/{service_relative_names[1]}.{endpoint_relative_names[2]}",
                "ujt_id": f"{service_relative_names[0]}.{endpoint_relative_names[1]}/{service_relative_names[1]}.{endpoint_relative_names[2]}",
            }
        },
    ]
    return expected_edge_elements


""" Example client name message map data:
Client0 has UserJourneys UJ0 and UJ1
Client1 has UserJourneys UJ2

UJ0 depends on Service0 and Service1
UJ1 depends on Service2
UJ2 depends on Service3

"""


@pytest.fixture
def example_client_name_message_map_client_relative_names():
    client_relative_names = ["Client0", "Client1"]
    return client_relative_names


@pytest.fixture
def example_client_name_message_map_user_journey_relative_names():
    user_journey_relative_names = ["UJ0", "UJ1", "UJ2"]
    return user_journey_relative_names


@pytest.fixture
def example_client_name_message_map_service_relative_names():
    service_relative_names = ["Service0", "Service1", "Service2", "Service3"]
    return service_relative_names


@pytest.fixture
def example_client_name_message_map(
    example_client_name_message_map_client_relative_names,
    example_client_name_message_map_user_journey_relative_names,
    example_client_name_message_map_service_relative_names,
):
    client_relative_names = example_client_name_message_map_client_relative_names
    user_journey_relative_names = (
        example_client_name_message_map_user_journey_relative_names
    )
    service_relative_names = example_client_name_message_map_service_relative_names

    client_name_message_map = {
        client_relative_names[0]: Client(
            name=client_relative_names[0],
            user_journeys=[
                UserJourney(
                    name=f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
                    client_name=client_relative_names[0],
                    dependencies=[
                        Dependency(
                            target_name=service_relative_names[0],
                            source_name=f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
                            toplevel=True,
                        ),
                        Dependency(
                            target_name=service_relative_names[1],
                            source_name=f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
                            toplevel=True,
                        ),
                    ],
                ),
                UserJourney(
                    name=f"{client_relative_names[0]}.{user_journey_relative_names[1]}",
                    client_name=client_relative_names[0],
                    dependencies=[
                        Dependency(
                            target_name=service_relative_names[2],
                            source_name=f"{client_relative_names[0]}.{user_journey_relative_names[1]}",
                            toplevel=True,
                        ),
                    ],
                ),
            ],
        ),
        client_relative_names[1]: Client(
            name=client_relative_names[1],
            user_journeys=[
                UserJourney(
                    name=f"{client_relative_names[1]}.{user_journey_relative_names[2]}",
                    client_name=client_relative_names[1],
                    dependencies=[
                        Dependency(
                            target_name=service_relative_names[3],
                            source_name=f"{client_relative_names[1]}.{user_journey_relative_names[2]}",
                            toplevel=True,
                        ),
                    ],
                ),
            ],
        ),
    }
    return client_name_message_map


@pytest.fixture
def example_node_elements_from_client_map(
    example_client_name_message_map_client_relative_names,
):
    client_relative_names = example_client_name_message_map_client_relative_names
    expected_node_elements = [
        {
            "data": {
                "id": client_relative_names[0],
                "label": client_relative_names[0],
                "ujt_id": client_relative_names[0],
            },
        },
        {
            "data": {
                "id": client_relative_names[1],
                "label": client_relative_names[1],
                "ujt_id": client_relative_names[1],
            },
        },
    ]
    return expected_node_elements


@pytest.fixture
def example_edge_elements_from_client_map(
    example_client_name_message_map_client_relative_names,
    example_client_name_message_map_user_journey_relative_names,
    example_client_name_message_map_service_relative_names,
):
    client_relative_names = example_client_name_message_map_client_relative_names
    user_journey_relative_names = (
        example_client_name_message_map_user_journey_relative_names
    )
    service_relative_names = example_client_name_message_map_service_relative_names

    expected_edge_elements = [
        {
            "data": {
                "source": client_relative_names[0],
                "target": service_relative_names[0],
                "id": f"{client_relative_names[0]}/{service_relative_names[0]}",
                "ujt_id": f"{client_relative_names[0]}/{service_relative_names[0]}",
                "user_journey_name": f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
            }
        },
        {
            "data": {
                "source": client_relative_names[0],
                "target": service_relative_names[1],
                "id": f"{client_relative_names[0]}/{service_relative_names[1]}",
                "ujt_id": f"{client_relative_names[0]}/{service_relative_names[1]}",
                "user_journey_name": f"{client_relative_names[0]}.{user_journey_relative_names[0]}",
            }
        },
        {
            "data": {
                "source": client_relative_names[0],
                "target": service_relative_names[2],
                "id": f"{client_relative_names[0]}/{service_relative_names[2]}",
                "ujt_id": f"{client_relative_names[0]}/{service_relative_names[2]}",
                "user_journey_name": f"{client_relative_names[0]}.{user_journey_relative_names[1]}",
            }
        },
        {
            "data": {
                "source": client_relative_names[1],
                "target": service_relative_names[3],
                "id": f"{client_relative_names[1]}/{service_relative_names[3]}",
                "ujt_id": f"{client_relative_names[1]}/{service_relative_names[3]}",
                "user_journey_name": f"{client_relative_names[1]}.{user_journey_relative_names[2]}",
            }
        },
    ]
    return expected_edge_elements
