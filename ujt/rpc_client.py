""" Module providing access points for RPCs to the reporting server. 

Although we can directly expose the reporting_service_stub, seems like
a better design to provide an abstraction layer on top of it. 
These functions are 1:1 passthroughs right now, but we may need to do
some additional data processing as the application grows.
"""

import datetime as dt
from typing import TYPE_CHECKING, List, Optional

import grpc
import server_pb2
import server_pb2_grpc

if TYPE_CHECKING:
    from graph_structures_pb2 import (  # pylint: disable=no-name-in-module  # pragma: no cover
        SLITypeValue,
        StatusValue,
    )

from . import config

reporting_service_stub = None


def connect():
    global reporting_service_stub
    channel = grpc.insecure_channel(config.REPORTING_SERVER_ADDRESS)
    reporting_service_stub = server_pb2_grpc.ReportingServiceStub(channel)


def get_nodes():
    """ Reads a list of Nodes from the remote Reporting Service. """
    global reporting_service_stub
    assert reporting_service_stub
    return reporting_service_stub.GetNodes(server_pb2.GetNodesRequest())


def get_clients():
    """ Reads a list of Clients from the remote Reporting Service. """
    global reporting_service_stub
    assert reporting_service_stub
    return reporting_service_stub.GetClients(server_pb2.GetClientsRequest())


def get_slis(
    node_names: Optional[List[str]] = None,
    start_time: Optional[dt.datetime] = None,
    end_time: Optional[dt.datetime] = None,
    sli_types: Optional[List["SLITypeValue"]] = None,
):
    """ Reads a list of SLIs from the remote Reporting Service. """
    global reporting_service_stub
    assert reporting_service_stub
    get_slis_request = server_pb2.GetSLIsRequest()
    if node_names is not None:
        get_slis_request.node_names.extend(node_names)
    if start_time is not None:
        get_slis_request.start_time.FromDatetime(start_time)
    if end_time is not None:
        get_slis_request.end_time.FromDatetime(end_time)
    if sli_types is not None:
        get_slis_request.sli_types.extend(sli_types)

    return reporting_service_stub.GetSLIs(get_slis_request)
