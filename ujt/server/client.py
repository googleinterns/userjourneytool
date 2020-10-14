import graph_structures_pb2
import grpc
import server_pb2
import server_pb2_grpc

with grpc.insecure_channel("localhost:50051") as channel:  # pragma: no cover
    stub = server_pb2_grpc.ReportingServiceStub(channel)

    node_request = server_pb2.GetNodesRequest()
    node_response = stub.GetNodes(node_request)
    print(node_response.nodes)

    sli_request = server_pb2.GetSLIsRequest()
    # sli_response = stub.get_slis(sli_request)
    sli_response = stub.GetSLIs(sli_request)
    print(sli_response.slis)
