"""Implementation of Reporting Server."""

import datetime
import pathlib
import random
from concurrent import futures
from typing import List

import grpc
import server_pb2
import server_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
from graph_structures_pb2 import SLI, Client, Node

from . import generate_data, server_utils


def read_local_data():
    """ Read and return protos from values in data directory. """
    data_path = pathlib.Path(__file__).parent / "data"
    client_paths = data_path.glob("Client_*.ujtdata")
    node_paths = data_path.glob("Node_*.ujtdata")

    clients = [server_utils.read_proto_from_file(path, Client) for path in client_paths]
    nodes = [server_utils.read_proto_from_file(path, Node) for path in node_paths]

    return nodes, clients


def generate_new_random_slis(nodes, timestamp: datetime.datetime):
    slis = []
    for node in nodes:
        proto_timestamp = Timestamp()
        proto_timestamp.FromDatetime(timestamp)
        sli = SLI(
            node_name=node.name,
            sli_value=random.random(),
            timestamp=proto_timestamp,
            **generate_data.SLO_BOUNDS,
        )
        slis.append(sli)

    return slis


class ReportingServiceServicer(server_pb2_grpc.ReportingServiceServicer):
    """Provides methods that implement functionality of Reporting Service."""

    def __init__(self, nodes, clients):
        self.nodes: List[Node] = nodes
        self.clients: List[Client] = clients
        self.last_reported_timestamp: datetime.datetime = datetime.datetime.now()
        self.reporting_interval: int = 5

    def GetNodes(self, request, context):
        return server_pb2.GetNodesResponse(nodes=self.nodes)

    def GetClients(self, request, context):
        return server_pb2.GetClientsResponse(clients=self.clients)

    def GetSLIs(self, request, context):
        """Returns updated SLI values to clients.

        In this mock example, we generate new random values for SLIs dynamically.
        In a real server, this method should report real SLI values.
        """
        current_timestamp = Timestamp()
        current_timestamp.GetCurrentTime()
        # Set the start and end time to the current time if they are unset in the request
        start_dt = request.start_time.ToDatetime() if request.start_time.IsInitialized() else current_timestamp.ToDatetime()
        end_dt = request.end_time.ToDatetime() if request.end_time.IsInitialized() else current_timestamp.ToDatetime()
        
        slis_output = []
        slis_at_timestamp = []
        # In this implementation, the timestamps are inclusive since we generate new SLIs
        # However, this is not inherent to the proto semantics
        while start_dt <= end_dt:
            slis_at_timestamp = generate_new_random_slis(self.nodes, start_dt)
            slis_output += slis_at_timestamp
            start_dt += datetime.timedelta(seconds=self.reporting_interval)

        # Can we improve this logic? Doesn't seem very elegant.
        if slis_at_timestamp != []:
            this_last_reported_timestamp = slis_at_timestamp[0].timestamp.ToDatetime()
            if this_last_reported_timestamp > self.last_reported_timestamp:
                self.last_reported_timestamp = this_last_reported_timestamp
                # Update the server's internal Node state
                sli_name_map = {sli.node_name: sli for sli in slis_at_timestamp}
                for node in self.nodes:
                    del node.slis[:]
                    node.slis.extend([sli_name_map[node.name]])

        return server_pb2.GetSLIsResponse(slis=slis_output)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    nodes, clients = read_local_data()
    reporting_service_servicer = ReportingServiceServicer(nodes, clients)

    server_pb2_grpc.add_ReportingServiceServicer_to_server(
        reporting_service_servicer, server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    print("starting server!")
    serve()
