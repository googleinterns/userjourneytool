import pytest
from graph_structures_pb2 import (
    SLI,
    Client,
    Dependency,
    Node,
    NodeType,
    UserJourney)


@pytest.fixture
def assert_same_elements():

    def inner_assert_same_elements(list1, list2):
        """ Asserts that two lists have the same elements, regardless of order.

        We use this approach for unhashable and uncomparable types, e.g. proto messages.

        Args:
            list1: First list to assert.
            list2: Second list to assert.
        """
        assert all(element1 in list2 for element1 in list1)
        assert all(element2 in list1 for element2 in list2)

    return inner_assert_same_elements


@pytest.fixture
def slo_bounds():
    return {
        "slo_error_lower_bound": .1,
        "slo_warn_lower_bound": .2,
        "slo_warn_upper_bound": .8,
        "slo_error_upper_bound": .9,
    }


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
                        **slo_bounds,
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
                        **slo_bounds,
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
                        **slo_bounds,
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
                        **slo_bounds,
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
                        **slo_bounds,
                    ),
                ],
            ),
    }
    return node_name_message_map


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
    slo_bounds,
    example_client_name_message_map_client_relative_names,
    example_client_name_message_map_user_journey_relative_names,
    example_client_name_message_map_service_relative_names,
):
    client_relative_names = example_client_name_message_map_client_relative_names
    user_journey_relative_names = example_client_name_message_map_user_journey_relative_names
    service_relative_names = example_client_name_message_map_service_relative_names

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
    return client_name_message_map
