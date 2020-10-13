import pathlib
from typing import Type

import google.protobuf.text_format as text_format
from google.protobuf.message import Message


def named_proto_file_name(name: str, proto_type: Type[Message]):
    """ Generates the default file name for messages with a name field.

    Such messages include: Services, Endpoints, Clients, UserJourneys.

    Args:
        name: A protobuf message name.
        proto_type: The type of the protobuf message

    Returns:
        A string of the default file name for the given message.
    """
    return f"{proto_type.__name__}_{name}.ujtdata"


def write_proto_to_file(path: pathlib.Path, message: Message) -> None:
    """Writes a protobuf to disk in a human-readable format.

    Args:
        path: The desired path for the file to be written.
        message: A protobuf message.
    """
    path.write_text(text_format.MessageToString(message))


def read_proto_from_file(
        path: pathlib.Path,
        proto_type: Type[Message]) -> Message:
    """Reads a protobuf message from a file.

    Args:
        path: The desired path for the file to be read.
        proto_type: The type of the protobuf message.
    """

    return text_format.Parse(path.read_text(), proto_type())
