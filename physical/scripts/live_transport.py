"""Lossless, bounded local TCP framing for the Windows-to-WSL bridge."""
import json
import struct
import numpy as np

HEADER = struct.Struct("<4sII")
TYPES = {"|u1", "<u2", "<u4", "<f4", "<f8"}


def read_exact(stream, count):
    parts = []
    while count:
        part = stream.recv(count)
        if not part:
            raise EOFError("Sensor connection closed")
        parts.append(part)
        count -= len(part)
    return b"".join(parts)


def send(stream, metadata, arrays=None):
    metadata = dict(metadata)
    chunks = []
    buffers = []
    offset = 0
    for name, value in (arrays or {}).items():
        value = np.ascontiguousarray(value)
        if value.dtype.str not in TYPES:
            raise ValueError("Unsupported transport dtype")
        blob = value.tobytes()
        buffers.append(dict(name=name, dtype=value.dtype.str, shape=list(value.shape),
                            offset=offset, bytes=len(blob)))
        chunks.append(blob)
        offset += len(blob)
    metadata["buffers"] = buffers
    head = json.dumps(metadata, separators=(",", ":"), allow_nan=False).encode()
    if len(head) > 1024 * 1024 or offset > 16 * 1024 * 1024:
        raise ValueError("Transport frame too large")
    stream.sendall(HEADER.pack(b"PHY1", len(head), offset) + head + b"".join(chunks))


def receive(stream):
    magic, head_size, body_size = HEADER.unpack(read_exact(stream, HEADER.size))
    if magic != b"PHY1" or not 0 < head_size <= 1024 * 1024 or body_size > 16 * 1024 * 1024:
        raise ValueError("Invalid transport frame")
    metadata = json.loads(read_exact(stream, head_size))
    body = read_exact(stream, body_size)
    arrays = {}
    expected_offset = 0
    for field in metadata.get("buffers", []):
        dtype = np.dtype(field["dtype"])
        shape = tuple(field["shape"])
        size = int(np.prod(shape)) * dtype.itemsize
        if (dtype.str not in TYPES or any(not isinstance(n, int) or n < 0 for n in shape)
                or field["offset"] != expected_offset or field["bytes"] != size
                or expected_offset + size > len(body) or field["name"] in arrays):
            raise ValueError("Invalid array layout")
        arrays[field["name"]] = np.frombuffer(body, dtype, count=size // dtype.itemsize,
                                            offset=expected_offset).reshape(shape)
        expected_offset += size
    if expected_offset != len(body):
        raise ValueError("Unclaimed transport payload")
    return metadata, arrays
