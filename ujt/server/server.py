"""Implementation of Reporting Server."""

from concurrent import futures

import grpc

import google.protobuf.text_format as text_format

import graph_structures_pb2
import server_pb2
import server_pb2_grpc

import glob
import pathlib

from . import server_utils

def read_local_data():
    """ Read and return protos from values in data directory. """
    data_path = pathlib.Path(__file__).parent / "data"
    client_paths = data_path.glob("Client_*.ujtdata")
    node_paths = data_path.glob("Node_*.ujtdata")

    clients = [server_utils.read_proto_from_file(path, graph_structures_pb2.Client) for path in client_paths]
    nodes = [server_utils.read_proto_from_file(path, graph_structures_pb2.Node) for path in node_paths]

    return nodes, clients

class ReportingServiceServicer(server_pb2_grpc.ReportingServiceServicer):
    """Provides methods that implement functionality of Reporting Service Server."""

    def __init__(self, nodes, clients):
        self.nodes = nodes
        self.clients = clients

    def GetNodes(self, request, context):
        response = server_pb2.NodeResponse(nodes=self.nodes)
        return response


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    nodes, clients = read_local_data()
    reporting_service_servicer = ReportingServiceServicer(nodes, clients)
        
    server_pb2_grpc.add_ReportingServiceServicer_to_server(reporting_service_servicer, server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    print("starting server!")
    serve()

