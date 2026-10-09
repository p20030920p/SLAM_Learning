"""Protect lossless RGB/depth/point data and reject truncated or inconsistent frames."""
import io
import json
from pathlib import Path
import socket
import sys
import threading
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from live_transport import HEADER, receive, send


class Buffer:
    def __init__(self, value):
        self.value = io.BytesIO(value)
    def recv(self, count):
        return self.value.read(min(count, 7))


class TransportTest(unittest.TestCase):
    def test_lossless_mixed_arrays(self):
        arrays = dict(rgb=np.arange(48, dtype='uint8').reshape(4,4,3),
                      depth=np.array([[0, 65535],[1001,2002]], dtype='<u2'),
                      points=np.array([[1,-2,3,4]],dtype='<f4'))
        a, b = socket.socketpair()
        try:
            worker = threading.Thread(target=send, args=(a, {'kind':'camera','stamp_ns':123},arrays))
            worker.start()
            metadata, actual = receive(b)
            worker.join(2)
            self.assertEqual(metadata['stamp_ns'],123)
            for key in arrays:
                np.testing.assert_array_equal(arrays[key],actual[key])
                self.assertEqual(arrays[key].dtype, actual[key].dtype)
        finally:
            a.close()
            b.close()

    def test_truncated_header(self):
        with self.assertRaises(EOFError):
            receive(Buffer(b'PHY1'))

    def test_oversize_rejected_before_payload(self):
        with self.assertRaises(ValueError):
            receive(Buffer(HEADER.pack(b'PHY1', 10, 17*1024*1024)))

    def test_inconsistent_array_layout(self):
        metadata = json.dumps({'buffers':[dict(name='depth',dtype='<u2',shape=[2],offset=0,bytes=2)]}).encode()
        with self.assertRaises(ValueError):
            receive(Buffer(HEADER.pack(b'PHY1',len(metadata),2) + metadata + b'00'))


if __name__ == '__main__':
    unittest.main()
