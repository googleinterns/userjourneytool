""" Module providing access points for RPCs to the reporting server. 

Although we can directly expose the reporting_service_stub, seems like
a better design to provide an abstraction layer on top of it. 
These functions are 1:1 passthroughs right now, but we may need to do
some additional data processing as the application grows.
"""

from typing import TYPE_CHECKING, Type

import grpc
import server_pb2
import server_pb2_grpc

if TYPE_CHECKING:
    from graph_structures_pb2 import \
        StatusValue  # pylint: disable=no-name-in-module  # pragma: no cover

# Let's hardcode this for now... later can move into cfg file. Doesn't really fit in constants file
# Not sure how to provide it as a cmd line argument from ujt module.
channel = grpc.insecure_channel("localhost:50051")
reporting_service_stub = server_pb2_grpc.ReportingServiceStub(channel)


def get_nodes():
    """ Reads a list of Nodes from the remote Reporting Service. """
    return reporting_service_stub.GetNodes(server_pb2.GetNodesRequest())


def get_clients():
    """ Reads a list of Clients from the remote Reporting Service. """
    return reporting_service_stub.GetClients(server_pb2.GetClientsRequest())


def get_slis():
    """ Reads a list of SLIs from the remote Reporting Service. """
    return reporting_service_stub.GetSLIs(server_pb2.GetSLIsRequest())


def set_comment(node_name: str, comment: str):
    """ Requests the reporting server to update the comment for a given node.
    
    Args:
        node_name: The name of the node to update.
        comment: The comment to give to the node.
    """
    reporting_service_stub.SetComment(
        server_pb2.SetCommentRequest(node_name=node_name,
                                     comment=comment))


def set_override_status(node_name: str, override_status: "StatusValue"):
    """ Requests the reporting server to update the override status for a given node.
    
    Args:
        node_name: The name of the node to update.
        override_status: The new status to give to the node.
    """
    reporting_service_stub.SetOverrideStatus(
        server_pb2.SetOverrideStatusRequest(
            node_name=node_name,
            override_status=override_status))
