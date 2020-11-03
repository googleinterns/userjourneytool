"""Implementation of Reporting Server."""

import datetime as dt
import pathlib
import random
from concurrent import futures
from typing import TYPE_CHECKING, Dict
import argparse

import grpc
import server_pb2
import server_pb2_grpc
from graph_structures_pb2 import SLI, Client, Node, SLIType

from . import generate_data, server_utils

if TYPE_CHECKING:
    from graph_structures_pb2 import (
        SLITypeValue,  # pylint: disable=no-name-in-module  # pragma: no cover
    )


def read_local_data(data_path_str: str = None):
    """ Read and return protos from values in data directory. """
    if data_path_str is None:
        data_path = pathlib.Path(__file__).parent / "data"
    else:
        data_path = pathlib.Path(data_path_str)
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


def generate_interval_slis(
    node_name: str,
    start_time: dt.datetime,
    end_time: dt.datetime,
    sli_type: "SLITypeValue",
    reporting_interval: dt.timedelta,
    random_mode: bool = True,
    start_value: float = None,
    end_value: float = None,
):
    """Generate SLIs for a given node and SLI type within a given interval.

    Uses random generation or linear interpolation for SLI value generation.
    In this implementation, the timestamps are deemed inclusive since we generate new SLIs.
    However, this is not inherently required by the proto request semantics.

    Args:
        node_name: the name of the node to generate SLIs for
        start_time: the start time of the interval
        end_time: the end time of the interval
        sli_type: the type of SLI to generate
        reporting_interval: the interval between successive SLIs

        random_mode: flag to use random value generation
        start_value: starting value for linear interpolation of SLI values
        end_value: end value for linear interpolation of SLI values
    """
    slis = []
    current_time = start_time

    if not random_mode:
        if start_value is None or end_value is None:
            raise ValueError

        time_range_seconds = (end_time - start_time).total_seconds()
        increment = (
            (end_value - start_value)
            * reporting_interval.total_seconds()
            / time_range_seconds
        )
        current_value = start_value

    while current_time <= end_time:
        if random_mode:
            sli_value = random.random()
        else:
            sli_value = current_value
            current_value += increment
        sli = SLI(
            node_name=node_name,
            sli_value=sli_value,
            slo_target=generate_data.SLO_TARGET,
            sli_type=sli_type,
            intra_status_change_threshold=generate_data.INTRA_STATUS_CHANGE_THRESHOLD,
            **generate_data.SLO_BOUNDS,  # type: ignore
        )
        sli.timestamp.FromDatetime(current_time)
        slis.append(sli)
        current_time += reporting_interval

    return slis


class ReportingServiceServicer(server_pb2_grpc.ReportingServiceServicer):
    """Provides methods that implement functionality of Reporting Service."""

    def __init__(self, node_map, client_map):
        self.node_map: Dict[str, Node] = node_map
        self.client_map: Dict[str, Client] = client_map
        self.last_reported_timestamp: dt.datetime = dt.datetime.now()
        self.reporting_interval: dt.timedelta = dt.timedelta(seconds=5)
        self.start_end_values = [
            (0, 0.05),  # ERROR IMPROVING
            (0.05, 0.15),  # ERROR to WARN
            (0.125, 0.175),  # WARN IMPROVING
            (0.15, 0.25),  # WARN to HEALTHY
            (0.3, 0.4),  # HEALTHY IMPROVING
            (0.6, 0.7),  # HEALTHY WORSENING
            (0.75, 0.85),  # HEALTHY to WARN,
            (0.825, 0.875),  # WARN WORSENING
            (0.85, 0.95),  # WARN to ERROR
            (0.95, 1),  # ERROR WORSENING
        ]
        self.start_end_idx = 0

    def GetNodes(self, request, context):
        return server_pb2.GetNodesResponse(nodes=self.node_map.values())

    def GetClients(self, request, context):
        return server_pb2.GetClientsResponse(clients=self.client_map.values())

    def GetSLIs(self, request, context):
        """Returns updated SLI values to clients.

        In this mock example, we generate new values for SLIs dynamically.
        In a real server, this method should report real SLI values.
        """

        current_timestamp = dt.datetime.now()

        # Set the start and end time to the current time if they are unset in the request
        start_dt = (
            request.start_time.ToDatetime()
            if request.start_time.IsInitialized()
            else current_timestamp
        )
        end_dt = (
            request.end_time.ToDatetime()
            if request.end_time.IsInitialized()
            else current_timestamp
        )

        if end_dt < start_dt:
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

        # if an instant was requested, use random values
        # otherwise, use linear interpolation to test change over time feature
        random_mode = start_dt == end_dt

        output_slis = []
        for node_name in requested_node_names:
            for sli_type in requested_sli_types:
                if node_contains_sli_type(self.node_map[node_name], sli_type):
                    node_slis = generate_interval_slis(
                        node_name,
                        start_dt,
                        end_dt,
                        sli_type,
                        self.reporting_interval,
                        random_mode=random_mode,
                        start_value=self.start_end_values[self.start_end_idx][0],
                        end_value=self.start_end_values[self.start_end_idx][1],
                    )

                    if node_slis == []:
                        continue

                    output_slis += node_slis

                    # update the server's internal store of the nodes
                    this_last_reported_timestamp = node_slis[-1].timestamp.ToDatetime()
                    if this_last_reported_timestamp > self.last_reported_timestamp:
                        self.last_reported_timestamp = this_last_reported_timestamp
                        for sli in self.node_map[node_name].slis:
                            if sli.sli_type == node_slis[-1].sli_type:
                                sli.CopyFrom(node_slis[-1])

        if not random_mode:
            # cycle through a new case
            self.start_end_idx = (self.start_end_idx + 1) % len(self.start_end_values)

        return server_pb2.GetSLIsResponse(slis=output_slis)


def serve(port: str = None, data_path_str: str = None):
    if port is None:
        port = "50052"

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    node_map, client_map = read_local_data(data_path_str)
    reporting_service_servicer = ReportingServiceServicer(node_map, client_map)

    server_pb2_grpc.add_ReportingServiceServicer_to_server(
        reporting_service_servicer, server
    )
    server.add_insecure_port(f"[::]:{port}")
    
    server.start()
    print("starting server!")
    server.wait_for_termination()


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-d",
        "--data-path",
        help="Path to directory to read mock data from",
    )
    arg_parser.add_argument(
        "-p",
        "--port",
        help="Port to run server on",
    )
    args = arg_parser.parse_args()
    serve(port=args.port, data_path_str=args.data_path)
