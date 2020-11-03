""" Temp file to generate mock data. """

import pathlib
import random
from collections import defaultdict
from typing import DefaultDict, Dict, List
import argparse

from graph_structures_pb2 import (
    SLI,
    Client,
    Dependency,
    Node,
    NodeType,
    SLIType,
    UserJourney,
)

from . import server_utils

# define the mock data in a convenient format to generate protobufs
# service and endpoint names correspond 1:1
SERVICE_ENDPOINT_NAME_MAP: Dict[str, List[str]] = {
    "APIServer": [
        "StartGame",
        "UpdateGameState",
    ],
    "WebServer": ["GetProfilePage", "GetLeaderboardPage", "BuyCurrency"],
    "GameService": [
        "GetPlayerLocation",
        "GetScore",
    ],
    "LeaderboardService": [
        "GetLeaderboard",
        "SetUserHighScore",
        "GetUserHighScore",
    ],
    "ProfileService": [
        "Authenticate",
        "GetUserInfo",
    ],
    "StoreService": ["VerifyPayment"],
    "GameDB": [
        "ReadHighScore",
        "WriteHighScore",
    ],
    "ProfileDB": [
        "ReadFriendsList",
        "WriteFriendsList",
    ],
    "ExternalAuthProvider": [],
    "ExternalPaymentProvider": [],
}
# define a dependency map from endpoint to its dependencies
# each tuple represents a dependency in the form (target_service_name, target_endpoint_name)
# note we use empty string instead of None to match the protobuf convention for "unset" fields
NODE_DEPENDENCY_MAP: DefaultDict[str, List[str]] = defaultdict(list)
NODE_DEPENDENCY_MAP.update(
    {
        "APIServer.StartGame": ["APIServer.UpdateGameState"],
        "APIServer.UpdateGameState": [
            "GameService.GetPlayerLocation",
            "GameService.GetScore",
            "LeaderboardService.SetUserHighScore",
        ],
        "WebServer.GetLeaderboardPage": ["LeaderboardService.GetLeaderboard"],
        "WebServer.GetProfilePage": [
            "ProfileService.Authenticate",
            "ProfileService.GetUserInfo",
        ],
        "WebServer.BuyCurrency": [("StoreService.VerifyPayment")],
        "LeaderboardService.GetLeaderboard": ["GameDB.ReadHighScore"],
        "LeaderboardService.SetUserHighScore": ["GameDB.WriteHighScore"],
        "LeaderboardService.GetUserHighScore": ["GameDB.ReadHighScore"],
        "ProfileService.Authenticate": ["ExternalAuthProvider"],
        "ProfileService.GetUserInfo": [
            "LeaderboardService.GetUserHighScore",
            "ProfileDB.ReadFriendsList",
        ],
        # StoreService
        "StoreService.VerifyPayment": ["ExternalPaymentProvider"],
    }
)
# client names and user journeys correspond 1:1
CLIENT_USER_JOURNEY_NAME_MAP: Dict[str, List[str]] = {
    "MobileClient": ["PlayGame"],
    "WebBrowser": [
        "ViewLeaderboard",
        "ViewProfile",
        "ConductMicrotransaction",
    ],
}
USER_JOURNEY_DEPENDENCY_MAP: Dict[str, List[str]] = {
    "MobileClient.PlayGame": ["APIServer.StartGame"],
    "WebBrowser.ViewLeaderboard": ["WebServer.GetLeaderboardPage"],
    "WebBrowser.ViewProfile": ["WebServer.GetProfilePage"],
    "WebBrowser.ConductMicrotransaction": ["WebServer.BuyCurrency"],
}
SLO_BOUNDS: Dict[str, float] = {
    "slo_error_lower_bound": 0.1,
    "slo_warn_lower_bound": 0.2,
    "slo_warn_upper_bound": 0.8,
    "slo_error_upper_bound": 0.9,
}
SLO_TARGET = 0.5
INTRA_STATUS_CHANGE_THRESHOLD = 0.03


def generate_nodes():
    """Generates mock service data used to test the UJT.

    Returns: a list of Service protobufs.
    """

    services = []
    endpoints = []
    for service_name, relative_endpoint_names in SERVICE_ENDPOINT_NAME_MAP.items():
        service = Node(node_type=NodeType.NODETYPE_SERVICE, name=service_name)

        fully_qualified_endpoint_names = [
            f"{service.name}.{relative_endpoint_name}"
            for relative_endpoint_name in relative_endpoint_names
        ]
        service.child_names.extend(fully_qualified_endpoint_names)
        service.slis.extend(
            [
                SLI(
                    node_name=service_name,
                    sli_value=random.random(),
                    slo_target=SLO_TARGET,
                    sli_type=SLIType.SLITYPE_AVAILABILITY,
                    intra_status_change_threshold=INTRA_STATUS_CHANGE_THRESHOLD,
                    **SLO_BOUNDS,
                )
            ]
        )
        services.append(service)

        for endpoint_name in fully_qualified_endpoint_names:
            endpoint = Node(
                node_type=NodeType.NODETYPE_ENDPOINT,
                name=endpoint_name,
                parent_name=service.name,
            )
            endpoint.dependencies.extend(
                [
                    Dependency(target_name=target_name, source_name=endpoint_name)
                    for target_name in NODE_DEPENDENCY_MAP[endpoint_name]
                ]
            )
            endpoint.slis.extend(
                [
                    SLI(
                        node_name=endpoint_name,
                        sli_value=random.random(),
                        slo_target=SLO_TARGET,
                        sli_type=SLIType.SLITYPE_LATENCY,
                        intra_status_change_threshold=INTRA_STATUS_CHANGE_THRESHOLD,
                        **SLO_BOUNDS,
                    )
                ]
            )
            endpoints.append(endpoint)

    return services + endpoints


def generate_clients():
    """Generates the mock client data used to test the UJT.

    Returns: A list of Client protobufs.
    """

    clients = []
    for (
        client_name,
        relative_user_journey_names,
    ) in CLIENT_USER_JOURNEY_NAME_MAP.items():
        client = Client(name=client_name)

        fully_qualified_user_journey_names = [
            f"{client.name}.{relative_user_journey_name}"
            for relative_user_journey_name in relative_user_journey_names
        ]
        for user_journey_name in fully_qualified_user_journey_names:
            user_journey = UserJourney(name=user_journey_name, client_name=client_name)
            user_journey.dependencies.extend(
                [
                    Dependency(
                        target_name=target_name,
                        source_name=user_journey_name,
                        toplevel=True,
                    )
                    for target_name in USER_JOURNEY_DEPENDENCY_MAP[user_journey_name]
                ]
            )
            client.user_journeys.extend([user_journey])

        clients.append(client)

    return clients


def save_mock_data(data_path_str: str = None):
    """ Saves the mock data used to test the UJT to disk. 
    
    Args:
        data_path_str: path to directory where mock data should be saved.

    """

    proto_type_message_map = {
        Node: generate_nodes(),
        Client: generate_clients(),
    }

    if data_path_str is None:
        data_path = pathlib.Path(__file__).parent / "data"
    else:
        data_path = pathlib.Path(data_path_str)


    for proto_type, messages in proto_type_message_map.items():
        for message in messages:
            path = data_path / server_utils.named_proto_file_name(
                message.name, proto_type
            )
            server_utils.write_proto_to_file(path, message)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-o",
        "--output-directory",
        help="Path to directory to store mock data",
    )
    args = arg_parser.parse_args()
    save_mock_data(data_path_str=args.output_directory)
