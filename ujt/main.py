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
""" Temporary main class for prototyping purposes.

Currently used for testing protobuf read and write functionality.
"""

import pathlib
from typing import Any

import google.protobuf.text_format as text_format

from generated import graph_structures_pb2


def write_proto_to_file(message: graph_structures_pb2.Service) -> None:
    """Writes a protobuf to disk in a human-readable format.

    Args:
        message: A protobuf message with a name field.

    Raises:
        ValueError: The provided message's name field was empty.
        AttributeError: The provided message does not contain a name field.
    """

    if not message.name:
        raise ValueError

    with open(
            pathlib.Path(__file__).parent.parent / "data" / message.name,
            "w+") as f:
        f.write(text_format.MessageToString(message))


def read_proto_from_file(path: str,
                         proto_type: Any = graph_structures_pb2.Service) -> Any:
    """Reads a protobuf message from a file.

    Args:
        path: The path to the file within the data directory.

    Raises:
        FileNotFoundError: The path was invalid.
    """

    with open(pathlib.Path(__file__).parent.parent / "data" / path, "r") as f:
        proto_text: str = f.read()
        return text_format.Parse(proto_text, proto_type())


if __name__ == "__main__":
    pass
