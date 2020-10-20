# pylint: disable=redefined-outer-name

from unittest.mock import ANY, Mock, call, patch

import pytest
from graph_structures_pb2 import SLI, Client, Dependency, Node, Status, UserJourney

import ujt.compute_status


@pytest.fixture
def patch_path():
    return "ujt.compute_status"


@pytest.mark.parametrize(
    "expected_status", [Status.STATUS_HEALTHY, Status.STATUS_WARN, Status.STATUS_ERROR]
)
def test_compute_statuses(patch_path, expected_status):
    client_name = "client"
    user_journey_name = "uj"
    node_name = "node"
    orphan_name = "orphan"
    client_name_message_map = {
        client_name: Client(
            name=client_name,
            user_journeys=[
                UserJourney(
                    name=user_journey_name,
                    client_name=client_name,
                    dependencies=[
                        Dependency(
                            source_name=f"{client_name}.{user_journey_name}",
                            target_name=node_name,
                        )
                    ],
                ),
            ],
        ),
    }
    node_name_message_map = {
        node_name: Node(name=node_name),
        orphan_name: Node(name=orphan_name),
    }

    def side_effect_update_node_name_message_map(_, node_name):
        node_name_message_map[node_name].status = expected_status
        return expected_status

    with patch(
        f"{patch_path}.compute_single_node_status",
        Mock(side_effect=side_effect_update_node_name_message_map),
    ) as mock_compute_single_node_status, patch(
        f"{patch_path}.compute_status_from_count_map",
        Mock(return_value=expected_status),
    ) as mock_compute_status_from_count_map:
        ujt.compute_status.compute_statuses(
            node_name_message_map, client_name_message_map
        )

        assert (
            client_name_message_map[client_name].user_journeys[0].status
            == expected_status
        )
        assert node_name_message_map[node_name].status == expected_status
        assert node_name_message_map[orphan_name].status == expected_status

        assert mock_compute_single_node_status.mock_calls == [
            call(ANY, node_name),
            call(ANY, orphan_name),
        ]
        assert mock_compute_status_from_count_map.mock_calls == [
            call({expected_status: 1})
        ]


def test_compute_single_node_status_already_set():
    node_name = "node"
    node_name_message_map = {
        node_name: Node(name=node_name, status=Status.STATUS_HEALTHY)
    }
    assert (
        ujt.compute_status.compute_single_node_status(node_name_message_map, node_name)
        == Status.STATUS_HEALTHY
    )
    assert node_name_message_map[node_name].status == Status.STATUS_HEALTHY


""" 
The following tests for compute_single_node_status are not very robust,
they rely on the function to automatically return the node's status if it's already set.
They also rely on compute_status_from_count_map and compute_sli_status.
Ideally, we should mock all the functions being called.
"""


@pytest.mark.parametrize(
    "expected_status", [Status.STATUS_HEALTHY, Status.STATUS_WARN, Status.STATUS_ERROR]
)
def test_compute_single_node_status_with_child(expected_status):
    parent_name = "parent"
    child_name = "child"
    node_name_message_map = {
        parent_name: Node(
            name=parent_name,
            status=Status.STATUS_UNSPECIFIED,
            child_names=[child_name],
        ),
        child_name: Node(
            name=child_name,
            status=expected_status,
            parent_name=parent_name,
        ),
    }
    assert (
        ujt.compute_status.compute_single_node_status(
            node_name_message_map, parent_name
        )
        == expected_status
    )
    assert node_name_message_map[parent_name].status == expected_status


@pytest.mark.parametrize(
    "expected_status", [Status.STATUS_HEALTHY, Status.STATUS_WARN, Status.STATUS_ERROR]
)
def test_compute_single_node_status_with_dependency(expected_status):
    source_name = "source"
    target_name = "target"
    node_name_message_map = {
        source_name: Node(
            name=source_name,
            status=Status.STATUS_UNSPECIFIED,
            dependencies=[
                Dependency(target_name=target_name, source_name=source_name),
            ],
        ),
        target_name: Node(
            name=target_name,
            status=expected_status,
        ),
    }
    assert (
        ujt.compute_status.compute_single_node_status(
            node_name_message_map, source_name
        )
        == expected_status
    )
    assert node_name_message_map[source_name].status == expected_status


@pytest.mark.parametrize(
    "sli_value, expected_status",
    [
        (0.5, Status.STATUS_HEALTHY),
        (0.15, Status.STATUS_WARN),
        (0.85, Status.STATUS_WARN),
        (0, Status.STATUS_ERROR),
        (1, Status.STATUS_ERROR),
    ],
)
def test_compute_single_node_status_with_sli(sli_value, expected_status, slo_bounds):
    node_name = "node"
    node_name_message_map = {
        node_name: Node(
            name=node_name,
            slis=[SLI(node_name=node_name, sli_value=sli_value, **slo_bounds)],
        )
    }
    assert (
        ujt.compute_status.compute_single_node_status(node_name_message_map, node_name)
        == expected_status
    )
    assert node_name_message_map[node_name].status == expected_status


@pytest.mark.parametrize(
    "count_map, expected_status",
    [
        (
            {
                Status.STATUS_HEALTHY: 1,
                Status.STATUS_WARN: 0,
                Status.STATUS_ERROR: 0,
            },
            Status.STATUS_HEALTHY,
        ),
        (
            {
                Status.STATUS_HEALTHY: 1,
                Status.STATUS_WARN: 1,
                Status.STATUS_ERROR: 0,
            },
            Status.STATUS_WARN,
        ),
        (
            {
                Status.STATUS_HEALTHY: 1,
                Status.STATUS_WARN: 1,
                Status.STATUS_ERROR: 1,
            },
            Status.STATUS_ERROR,
        ),
    ],
)
def test_compute_status_from_count_map(count_map, expected_status):
    assert (
        ujt.compute_status.compute_status_from_count_map(count_map) == expected_status
    )


@pytest.mark.parametrize(
    "sli_value, expected_status",
    [
        (0.5, Status.STATUS_HEALTHY),
        (0.15, Status.STATUS_WARN),
        (0.85, Status.STATUS_WARN),
        (0, Status.STATUS_ERROR),
        (1, Status.STATUS_ERROR),
    ],
)
def test_compute_sli_status(sli_value, expected_status, slo_bounds):
    sli = SLI(sli_value=sli_value, **slo_bounds)
    assert ujt.compute_status.compute_sli_status(sli) == expected_status
    assert sli.status == expected_status


def test_reset_node_statuses():
    node_name = "node"
    node_name_message_map = {
        node_name: Node(name=node_name, status=Status.STATUS_ERROR),
    }
    ujt.compute_status.reset_node_statuses(node_name_message_map)
    assert node_name_message_map[node_name].status == Status.STATUS_UNSPECIFIED


def test_reset_client_statuses():
    client_name = "client"
    user_journey_name = "uj"
    client_name_message_map = {
        client_name: Client(
            name=client_name,
            user_journeys=[
                UserJourney(
                    name=user_journey_name,
                    client_name=client_name,
                    status=Status.STATUS_ERROR,
                ),
            ],
        ),
    }
    ujt.compute_status.reset_client_statuses(client_name_message_map)
    assert (
        client_name_message_map[client_name].user_journeys[0].status
        == Status.STATUS_UNSPECIFIED
    )
