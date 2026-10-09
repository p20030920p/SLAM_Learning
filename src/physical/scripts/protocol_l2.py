"""L2 wire decoder, based on Unitree SDK2 commit 0e3c51f.

The coordinate conversion is adapted from Unitree's BSD-3-Clause utilities.
Copyright (c) 2024, Unitree Robotics. See THIRD_PARTY_UNITREE.txt.
Raw packet timestamps are device timestamps; they are not a shared PC clock.
"""
import collections
import struct
import zlib

import numpy as np

MAGIC = b"\x55\xaa\x05\x0a"
POINT_DTYPE = np.dtype([
    ("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("intensity", "<f4"),
    ("time", "<f4"), ("ring", "<u4"),
])


class Parser:
    def __init__(self):
        self.buffer = bytearray()
        self.counts = collections.Counter()
        self.sizes = collections.Counter()
        self.crc_errors = 0
        self.discarded_bytes = 0

    def feed(self, chunk):
        self.buffer.extend(chunk)
        while len(self.buffer) >= 12:
            i = self.buffer.find(MAGIC)
            if i < 0:
                self.discarded_bytes += len(self.buffer) - 3
                del self.buffer[:-3]
                break
            if i:
                self.discarded_bytes += i
                del self.buffer[:i]
            if len(self.buffer) < 12:
                break
            kind, size = struct.unpack_from("<II", self.buffer, 4)
            if not 24 <= size <= 65536:
                self.discarded_bytes += 1
                del self.buffer[0]
                continue
            if len(self.buffer) < size:
                break
            packet = bytes(self.buffer[:size])
            crc = struct.unpack_from("<I", packet, size - 12)[0]
            # Firmware CRC covers payload only (header comment is misleading).
            if packet[-2:] != b"\x00\xff" or zlib.crc32(packet[12:-12]) != crc:
                self.crc_errors += 1
                del self.buffer[0]
                continue
            del self.buffer[:size]
            self.counts[kind] += 1
            self.sizes[f"{kind}:{size}"] += 1
            yield kind, packet


def info(packet):
    seq, payload, sec, nsec = struct.unpack_from("<4I", packet, 12)
    return seq, sec + nsec * 1e-9


def points(packet, *, sdk_float_angles=False):
    if len(packet) != 1044:
        raise ValueError(f"Unexpected point packet size {len(packet)}")
    a, b, theta_bias, alpha_bias, beta, xi, range_bias, scale = struct.unpack_from("<8f", packet, 64)
    theta0, theta_step, period, rmin, rmax, alpha0, alpha_step, dt = struct.unpack_from("<8f", packet, 96)
    n = struct.unpack_from("<I", packet, 128)[0]
    if n > 300:
        raise ValueError(f"Invalid point count {n}")
    raw = np.frombuffer(packet, dtype="<u2", count=n, offset=132)
    reflect = np.frombuffer(packet, dtype="u1", count=n, offset=732)
    j = np.arange(n, dtype=np.float64)
    distance = scale * (raw.astype(np.float64) + range_bias)
    alpha = alpha0 + alpha_bias + j * alpha_step
    theta = theta0 + theta_bias + j * theta_step
    if sdk_float_angles and n:
        # Diagnostic control: match SDK float32 initialization and sequential
        # angle addition. Default retains the first baseline's vectorized math.
        alpha=np.empty(n,dtype=np.float32); theta=np.empty(n,dtype=np.float32)
        alpha[0]=np.float32(alpha0)+np.float32(alpha_bias)
        theta[0]=np.float32(theta0)+np.float32(theta_bias)
        for k in range(1,n):
            alpha[k]=alpha[k-1]+np.float32(alpha_step)
            theta[k]=theta[k-1]+np.float32(theta_step)
        # Keep the remaining calculation in the original double precision.
        alpha=alpha.astype(np.float64); theta=theta.astype(np.float64)
    A = (-np.cos(beta)*np.sin(xi) + np.sin(beta)*np.cos(xi)*np.sin(alpha))*distance + b
    B = np.cos(alpha)*np.cos(xi)*distance
    C = (np.sin(beta)*np.sin(xi) + np.cos(beta)*np.cos(xi)*np.sin(alpha))*distance
    out = np.empty(n, dtype=POINT_DTYPE)
    out["x"] = np.cos(theta)*A - np.sin(theta)*B
    out["y"] = np.sin(theta)*A + np.cos(theta)*B
    out["z"] = C + a
    out["intensity"] = reflect
    out["time"] = j*dt
    # Official single-line converter uses ring=1. Grouping 18 lines is a
    # consumer convention, not an invented physical 18-beam sensor identity.
    out["ring"] = 1
    return out[(raw > 0) & (distance >= max(0, rmin)) & (distance <= min(100, rmax))]


def user_command(command, value=0):
    """SDK2 volatile user control packet; caller must document hardware writes."""
    body = MAGIC + struct.pack("<II2I", 100, 32, command, value)
    return body + struct.pack("<II2s2s", zlib.crc32(body[12:]), 0, b"\0\0", b"\0\xff")


def version_request():
    return user_command(3)
