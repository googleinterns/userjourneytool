import grpc

import graph_structures_pb2
import server_pb2
import server_pb2_grpc

with grpc.insecure_channel("localhost:50051") as channel:
    stub = server_pb2_grpc.ReportingServiceStub(channel)

    node_request = server_pb2.NodeRequest()
    node_response = stub.GetNodes(node_request)
    print(node_response.nodes)

