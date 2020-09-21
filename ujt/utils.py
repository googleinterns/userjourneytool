# Copyright 2020 Chuan Chen

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Module providing utility functions.

Currently used for protobuf read and write functionality.
"""

import pathlib
from typing import List, Type

import google.protobuf.text_format as text_format
import graph_structures_pb2
from google.protobuf.message import Message

from . import converters, constants


def named_proto_file_name(name: str, proto_type: Type[Message]):
    """ Generates the default file name for messages with a name field.

    Such messages include: Services, Endpoints, Clients, UserJourneys.

    Args:
        name: A protobuf message name.
        proto_type: The type of the protobuf message

    Returns:
        A string of the default file name for the given message.
    """
    return f"{proto_type.__name__}_{name}"


def write_proto_to_file(file_name: str, message: Message) -> None:
    """Writes a protobuf to disk in a human-readable format.

    Args:
        file_name: The desired file name for the file to be written.
        message: A protobuf message.
    """

    with open(pathlib.Path(__file__).parent.parent / "data" / file_name,
              "w+") as f:
        f.write(text_format.MessageToString(message))


def read_proto_from_file(file_name: str, proto_type: Type[Message]) -> Message:
    """Reads a protobuf message from a file.

    Args:
        file_name: The desired file name for the file to be read.
        proto_type: The type of the protobuf message.

    Raises:
        FileNotFoundError: The path was invalid.
    """

    with open(pathlib.Path(__file__).parent.parent / "data" / file_name,
              "r") as f:
        proto_text: str = f.read()
        return text_format.Parse(proto_text, proto_type())


def is_client_cytoscape_node(tap_node):
    return constants.CLIENT_CLASS in tap_node["classes"].split(" ")


def relative_name(full_name):
    return full_name.split(".")[-1]


def human_readable_enum_name(enum_value, enum_class):
    return enum_class.Name(enum_value).split("_")[-1]
