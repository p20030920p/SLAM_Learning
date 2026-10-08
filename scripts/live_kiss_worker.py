"""Isolated KISS environment worker; fixed binary I/O, no ROS dependencies."""
import struct
import sys
import numpy as np
from kiss_icp.config import KISSConfig
from kiss_icp.kiss_icp import KissICP


def read_exact(count):
    data = bytearray()
    while len(data) < count:
        chunk = sys.stdin.buffer.read(count - len(data))
        if not chunk:
            raise EOFError
        data.extend(chunk)
    return data


config = KISSConfig()
config.data.min_range = 0.2
config.data.max_range = 20.0
config.data.deskew = False
config.mapping.voxel_size = 0.08
config.registration.max_num_threads = 2
config.adaptive_threshold.initial_threshold = 0.3
odometry = KissICP(config)
try:
    while True:
        count = struct.unpack("<I", read_exact(4))[0]
        if not 0 < count < 1000000:
            raise ValueError("Invalid KISS worker point count")
        xyz = np.frombuffer(read_exact(count * 12), dtype="<f4").reshape(-1, 3).astype(float)
        odometry.register_frame(xyz, np.zeros(len(xyz)))
        matrix = odometry.last_pose
        if not np.isfinite(matrix).all():
            raise ValueError("KISS returned nonfinite pose")
        sys.stdout.buffer.write(np.asarray(matrix, dtype="<f8").tobytes())
        sys.stdout.buffer.flush()
except (EOFError, KeyboardInterrupt):
    pass
