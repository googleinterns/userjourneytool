""" Temp file to generate mock data. """

from collections import defaultdict
from typing import DefaultDict, List, Tuple

from generated import graph_structures_pb2

from . import utils

# define the mock data in a simpler format before generating protobufs
# service and endpoint names correspond 1:1
SERVICE_NAMES = [
    "APIServer",
    "WebServer",
    "GameService",
    "LeaderboardService",
    "ProfileService",
    "StoreService",
    "GameDB",
    "ProfileDB",
    "ExternalAuthProvider",
    "ExternalPaymentProvider",
]
SERVICE_ENDPOINT_NAME_MAP = {
    "APIServer": ["StartGame", "UpdateGameState"],
    "WebServer": ["ViewProfile", "ViewLeaderboard"],
    "GameService": ["GetPlayerLocation", "GetScore"],
    "LeaderboardService": [
        "GetLeaderboard", "SetUserHighScore", "GetUserHighScore"
    ],
    "ProfileService": ["Authenticate", "GetUserInfo"],
    "StoreService": ["BuyCurrency"],
    "GameDB": ["ReadHighScore", "WriteHighScore"],
    "ProfileDB": ["ReadFriendsList", "WriteFriendsList"],
    "ExternalAuthProvider": [],
    "ExternalPaymentProvider": [],
}
# define a dependency map from endpoint to its dependencies
# each tuple represents a dependency in the form (target_service_name, target_endpoint_name)
# note we use empty string instead of None to match the protobuf convention for "unset" fields
ENDPOINT_DEPENDENCY_MAP: DefaultDict[str, List[Tuple[str,
                                                     str]]] = defaultdict(list)
ENDPOINT_DEPENDENCY_MAP.update({
    # APIServer
    "StartGame": [("APIServer", "UpdateGameState")],
    "UpdateGameState": [
        ("GameService", "GetPlayerLocation"),
        ("GameService", "GetScore"),
        ("LeaderboardService", "SetUserHighScore"),
    ],
    # WebServer
    "ViewLeaderboard": [("LeaderboardService", "GetLeaderboard")],
    "ViewProfile": [
        ("ProfileService", "Authenticate"),
        ("ProfileService", "GetUserInfo"),
    ],
    "BuyCurrency": [("StoreService", "VerifyPayment")],
    # LeaderboardService
    "GetLeaderboard": [("GameDB", "ReadHighScore")],
    "SetUserHighScore": [("GameDB", "WriteHighScore")],
    "GetUserHighScore": [("GameDB", "ReadHighScore")],
    # ProfileService
    "Authenticate": [("ExternalAuthProvider", "")],
    "GetUserInfo": [("LeaderboardService", "GetUserHighScore"),
                    ("ProfileDB", "ReadFriendsList")],
    # StoreService
    "VerifyPayment": [("ExternalPaymentProvider", "")],
})
# client names and user journeys correspond 1:1
CLIENT_NAMES = ["MobileClient", "WebBrowser"]
CLIENT_USER_JOURNEY_NAME_MAP = {
    "MobileClient": ["Play a Game"],
    "WebBrowser": [
        "View Leaderboard",
        "View Profile",
        "Conduct Microtransaction",
    ],
}
USER_JOURNEY_DEPENDENCY_MAP = {
    # MobileClient
    "Play a Game": [("APIServer", "StartGame")],
    # WebClient
    "View Leaderboard": [("WebServer", "ViewLeaderboard")],
    "View Profile": [("WebServer", "ViewProfile")],
    "Conduct Microtransaction": [("WebServer", "BuyCurrency")],
}


def generate_services():
    """ Generates mock service data used to test the UJT.
    
    Returns: a list of Service protobufs.
    """

    services = [
        graph_structures_pb2.Service(name=name) for name in SERVICE_NAMES
    ]
    for service in services:
        endpoints = [
            graph_structures_pb2.Endpoint(name=name, service_name=service.name)
            for name in SERVICE_ENDPOINT_NAME_MAP[service.name]
        ]
        for endpoint in endpoints:
            dependencies = [
                graph_structures_pb2.Dependency(
                    target_service_name=target_service_name,
                    target_endpoint_name=target_endpoint_name,
                ) for (target_service_name, target_endpoint_name
                      ) in ENDPOINT_DEPENDENCY_MAP[endpoint.name]
            ]
            endpoint.dependencies.extend(dependencies)
        service.endpoints.extend(endpoints)

    return services


def generate_clients():
    """ Generates the mock client data used to test the UJT.
    
    Returns: A list of Client protobufs.
    """

    clients = [graph_structures_pb2.Client(name=name) for name in CLIENT_NAMES]
    for client in clients:
        user_journeys = [
            graph_structures_pb2.UserJourney(name=name)
            for name in CLIENT_USER_JOURNEY_NAME_MAP[client.name]
        ]
        for user_journey in user_journeys:
            dependencies = [
                graph_structures_pb2.Dependency(
                    target_service_name=target_service_name,
                    target_endpoint_name=target_endpoint_name,
                ) for (target_service_name, target_endpoint_name
                      ) in USER_JOURNEY_DEPENDENCY_MAP[user_journey.name]
            ]
            user_journey.dependencies.extend(dependencies)
        client.user_journeys.extend(user_journeys)

    return clients


def save_mock_data():
    """ Saves the mock data used to test the UJT to disk. """

    for client in generate_clients():
        utils.write_proto_to_file(client, graph_structures_pb2.Client)

    for service in generate_services():
        utils.write_proto_to_file(service, graph_structures_pb2.Service)


if __name__ == "__main__":
    save_mock_data()
