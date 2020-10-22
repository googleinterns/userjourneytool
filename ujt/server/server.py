"""Implementation of Reporting Server."""

import datetime as dt
import pathlib
import random
from concurrent import futures
from typing import TYPE_CHECKING, Dict, List

import grpc
import server_pb2
import server_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
from graph_structures_pb2 import SLI, Client, Node, SLIType

from . import generate_data, server_utils

if TYPE_CHECKING:
    from graph_structures_pb2 import (
        SLITypeValue,  # pylint: disable=no-name-in-module  # pragma: no cover
    )


def read_local_data():
    """ Read and return protos from values in data directory. """
    data_path = pathlib.Path(__file__).parent / "data"
    client_paths = data_path.glob("Client_*.ujtdata")
    node_paths = data_path.glob("Node_*.ujtdata")

    clients = [server_utils.read_proto_from_file(path, Client) for path in client_paths]
    nodes = [server_utils.read_proto_from_file(path, Node) for path in node_paths]

    client_map = {client.name: client for client in clients}
    node_map = {node.name: node for node in nodes}

    return node_map, client_map


def node_contains_sli_type(node: Node, sli_type: "SLITypeValue"):
    for sli in node.slis:
        if sli.sli_type == sli_type:
            return True
    return False


def generate_new_random_slis(
    node_map: Dict[str, Node],
    node_names: List[str],
    timestamp: dt.datetime,
    sli_types: List["SLITypeValue"],
):
    slis = []
    for node_name in node_names:
        for sli_type in sli_types:
            if node_contains_sli_type(node_map[node_name], sli_type):
                sli = SLI(
                    node_name=node_name,
                    sli_value=random.random(),
                    slo_target=generate_data.SLO_TARGET,
                    sli_type=sli_type,
                    **generate_data.SLO_BOUNDS,  # type: ignore
                )
                sli.timestamp.FromDatetime(timestamp)

                slis.append(sli)

    return slis


class ReportingServiceServicer(server_pb2_grpc.ReportingServiceServicer):
    """Provides methods that implement functionality of Reporting Service."""

    def __init__(self, node_map, client_map):
        self.node_map: Dict[str, Node] = node_map
        self.client_map: Dict[str, Client] = client_map
        self.last_reported_timestamp: dt.datetime = dt.datetime.now()
        self.reporting_interval: int = 5

    def GetNodes(self, request, context):
        return server_pb2.GetNodesResponse(nodes=self.node_map.values())

    def GetClients(self, request, context):
        return server_pb2.GetClientsResponse(clients=self.client_map.values())

    def GetSLIs(self, request, context):
        """Returns updated SLI values to clients.

        In this mock example, we generate new random values for SLIs dynamically.
        In a real server, this method should report real SLI values.
        """
        current_timestamp = Timestamp()
        current_timestamp.GetCurrentTime()
        # Set the start and end time to the current time if they are unset in the request
        start_dt = (
            request.start_time.ToDatetime()
            if request.start_time.IsInitialized()
            else current_timestamp.ToDatetime()
        )
        end_dt = (
            request.end_time.ToDatetime()
            if request.end_time.IsInitialized()
            else current_timestamp.ToDatetime()
        )

        if end_dt > start_dt:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "End time must not be later than start time!",
            )

        requested_node_names = (
            request.node_names if request.node_names != [] else self.node_map.keys()
        )

        requested_sli_types = (
            request.sli_types
            if request.sli_types != []
            # get all SLI types if sli_types was empty in request message
            else [
                value_descriptor.number
                for value_descriptor in SLIType.DESCRIPTOR.values
            ]
        )

        slis_output = []
        slis_at_timestamp = []
        # In this implementation, the timestamps are inclusive since we generate new SLIs
        # However, this is not inherent to the proto semantics
        while start_dt <= end_dt:
            slis_at_timestamp = generate_new_random_slis(
                self.node_map, requested_node_names, start_dt, requested_sli_types
            )
            slis_output += slis_at_timestamp
            start_dt += dt.timedelta(seconds=self.reporting_interval)

        # Can we improve this logic? Doesn't seem very elegant.
        this_last_reported_timestamp = slis_at_timestamp[0].timestamp.ToDatetime()
        if this_last_reported_timestamp > self.last_reported_timestamp:
            self.last_reported_timestamp = this_last_reported_timestamp
            # Update the server's internal Node state
            sli_name_map = {sli.node_name: sli for sli in slis_at_timestamp}
            for node_name, node in self.node_map:
                del node.slis[:]
                node.slis.extend([sli_name_map[node.name]])

        return server_pb2.GetSLIsResponse(slis=slis_output)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    node_map, client_map = read_local_data()
    reporting_service_servicer = ReportingServiceServicer(node_map, client_map)

    server_pb2_grpc.add_ReportingServiceServicer_to_server(
        reporting_service_servicer, server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("starting server!")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
