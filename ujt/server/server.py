"""Implementation of Reporting Server."""

from concurrent import futures

import grpc

import graph_structures_pb2
import server_pb2
import server_pb2_grpc


class ReportingServiceServicer(server_pb2_grpc.ReportingServiceServicer):
    """Provides methods that implement functionality of Reporting Service Server."""

    def __init__(self):
        pass

    def GetNodes(self, request, context):
        node = graph_structures_pb2.Node(name="ServerNode")
        response = server_pb2.NodeResponse(nodes=[node])
        return response


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    reporting_service_servicer = ReportingServiceServicer()
    server_pb2_grpc.add_ReportingServiceServicer_to_server(reporting_service_servicer, server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    print("starting server!")
    serve()
