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
from typing import Type

import google.protobuf.text_format as text_format
from google.protobuf.message import Message


def file_name(name: str, proto_type: Type[Message]):
    return f"{proto_type.__name__}_{name}"


def write_proto_to_file(message: Message, proto_type: Type[Message]) -> None:
    """Writes a protobuf to disk in a human-readable format.

    Args:
        message: A protobuf message with a name field.
        proto_type: The type of the protobuf message.

    Raises:
        ValueError: The provided message's name field was empty.
        AttributeError: The provided message does not contain a name field.
    """

    if not message.name:  # type: ignore
        raise ValueError

    with open(
            pathlib.Path(__file__).parent.parent / "data" /
            file_name(message.name, proto_type), "w+") as f:  # type: ignore
        f.write(text_format.MessageToString(message))


def read_proto_from_file(name: str, proto_type: Type[Message]) -> Message:
    """Reads a protobuf message from a file.

    Args:
        name: The name field of the protobuf to be read.
        proto_type: The type of the protobuf message.

    Raises:
        FileNotFoundError: The path was invalid.
    """

    with open(
            pathlib.Path(__file__).parent.parent / "data" /
            file_name(name, proto_type), "r") as f:
        proto_text: str = f.read()
        return text_format.Parse(proto_text, proto_type())
