import grpc
import server_pb2
import server_pb2_grpc

channel = grpc.insecure_channel("localhost:50051")  # hardcode this for now...
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
