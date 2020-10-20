"""Implementation of Reporting Server."""

import pathlib
import random
from concurrent import futures
from typing import List

import grpc
import server_pb2
import server_pb2_grpc
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


def generate_new_random_slis(nodes):
    slis = []
    for node in nodes:
        sli = SLI(
            node_name=node.name,
            sli_value=random.random(),
            **generate_data.SLO_BOUNDS,
        )
        slis.append(sli)

    return slis


class ReportingServiceServicer(server_pb2_grpc.ReportingServiceServicer):
    """Provides methods that implement functionality of Reporting Service."""

    def __init__(self, nodes, clients):
        self.nodes: List[Node] = nodes
        self.clients: List[Client] = clients

    def GetNodes(self, request, context):
        return server_pb2.GetNodesResponse(nodes=self.nodes)

    def GetClients(self, request, context):
        return server_pb2.GetClientsResponse(clients=self.clients)

    def GetSLIs(self, request, context):
        """Returns updated SLI values to clients.

        In this mock example, we generate new random values for SLIs dynamically.
        In a real server, this method should report real SLI values.
        """

        slis = generate_new_random_slis(self.nodes)
        # Update the server's internal Node state
        sli_name_map = {sli.node_name: sli for sli in slis}
        for node in self.nodes:
            # not sure why node.slis[:] = [sli_name_map[node.name]] doesn't work
            # it seems to be supported in the official documentation.
            # https://developers.google.com/protocol-buffers/docs/reference/python-generated#embedded_message
            # TODO: investigate proto repeated field assignmnt

            del node.slis[:]
            node.slis.extend([sli_name_map[node.name]])
        return server_pb2.GetSLIsResponse(slis=slis)


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
