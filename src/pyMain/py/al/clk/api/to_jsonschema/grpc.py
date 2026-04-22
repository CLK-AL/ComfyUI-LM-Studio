"""gRPC → JSON Schema canonical form.

Pipeline (the "grpc2jsonschema2comfyui" pattern):
  1. Compile .proto with `protoc --descriptor_set_out=out.desc`
  2. Parse the FileDescriptorSet (google.protobuf.descriptor_pb2)
  3. For each service × method, emit one OperationSchema with
     input_schema / output_schema generated from the message types.
  4. `binding.py` turns that into ComfyUI INPUT_TYPES / RETURN_TYPES.

Status: scaffold. The protobuf → JSON Schema mapping is well-trodden
(see protoc-gen-jsonschema, buf.build/json-schema). We'll import
`google.protobuf` when the first gRPC test lands.
"""
from __future__ import annotations

from typing import Mapping

from . import Canonical


def convert(descriptor_set: bytes | Mapping) -> Canonical:
    raise NotImplementedError(
        "gRPC → JSON Schema converter is not yet implemented. "
        "Compile proto with `protoc --descriptor_set_out=...`, load the "
        "FileDescriptorSet, and emit OperationSchema entries."
    )
