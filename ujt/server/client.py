""" Client to directly access server endpoints. 
Not part of the UJT -- only used to test the server without 
having to run or setup the UJT to call the server.
"""

import datetime as dt

import grpc
import server_pb2
import server_pb2_grpc
import graph_structures_pb2

with grpc.insecure_channel("localhost:50051") as channel:  # pragma: no cover
    stub = server_pb2_grpc.ReportingServiceStub(channel)

    node_request = server_pb2.GetNodesRequest()
    node_response = stub.GetNodes(node_request)
    print(len(node_response.nodes))

    sli_request = server_pb2.GetSLIsRequest()
    # sli_response = stub.get_slis(sli_request)
    sli_response = stub.GetSLIs(sli_request)
    print(len(sli_response.slis))
    # print(sli_response.slis)

    print("---")

    start_time = dt.datetime.now() - dt.timedelta(hours=1)
    end_time = start_time + dt.timedelta(seconds=10)
    sli_request.start_time.FromDatetime(start_time)
    sli_request.end_time.FromDatetime(end_time)

    sli_response = stub.GetSLIs(sli_request)
    print(len(sli_response.slis))
    #print(sli_response.slis)

    sli_request.node_names.extend(["ProfileDB.WriteFriendsList"])
    sli_response = stub.GetSLIs(sli_request)
    print(len(sli_response.slis))
    #print(sli_response.slis)

    sli_request.sli_types.extend([graph_structures_pb2.SLIType.SLITYPE_UNSPECIFIED])
    sli_response = stub.GetSLIs(sli_request)
    print(len(sli_response.slis))