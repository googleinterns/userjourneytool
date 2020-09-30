""" Module providing access points for RPCs to the reporting server. 

Although we can directly expose the reporting_service_stub, seems like
a better design to provide an abstraction layer on top of it. 
These functions are 1:1 passthroughs right now, but we may need to do
some additional data processing as the application grows.
"""

import grpc
import server_pb2
import server_pb2_grpc

# Let's hardcode this for now... later can move into cfg file. Doesn't really fit in constants file
# Not sure how to provide it as a cmd line argument from ujt module.
channel = grpc.insecure_channel("localhost:50051")
reporting_service_stub = server_pb2_grpc.ReportingServiceStub(channel)


def get_nodes():
    """ Reads a list of Nodes from the remote Reporting Service. """
    return reporting_service_stub.GetNodes(server_pb2.NodeRequest())


def get_clients():
    """ Reads a list of Clients from the remote Reporting Service. """
    return reporting_service_stub.GetClients(server_pb2.ClientRequest())


def get_slis():
    """ Reads a list of SLIs from the remote Reporting Service. """
    return reporting_service_stub.GetSLIs(server_pb2.SLIRequest())
