"""Concurrent official ZIP member retrieval to complement the interval fetcher.

No transformations. Local ZIP header, central-directory sizes, original CRC,
and HTTP ETag are checked before atomic writes. The main interval fetcher
independently rechecks all files and matching label counts before success.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import struct
import threading
import zipfile
import zlib
from pathlib import Path
from fetch_kitti_intervals import RangeFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    assert 1 <= args.workers <= 8
    runtime = args.runtime.resolve()
    url = 'https://s3.eu-central-1.amazonaws.com/avg-kitti/data_odometry_velodyne.zip'
    remote = RangeFile(url)
    with zipfile.ZipFile(remote) as archive:
        infos = [archive.getinfo(f'dataset/sequences/{seq}/velodyne/{frame:06d}.bin')
                 for seq, start, end in [('00', 4390, 4530), ('01', 150, 250), ('02', 860, 950)]
                 for frame in range(start, end + 1)]
    local = threading.local()
    readers = []
    state = {'status': 'prefetching', 'pid': os.getpid(), 'url': url, 'etag': remote.etag,
             'workers': args.workers, 'files': {}, 'scope': 'Original selected ZIP members, no content changes'}
    output = runtime / 'kitti-point-prefetch.json'

    def save():
        state['http_range_bytes_transferred'] = remote.transferred + sum(r.transferred for r in readers)
        output.write_text(json.dumps(state, indent=2) + '\n')

    def fetch(info):
        target = runtime / 'data/kitti-original/data_odometry_velodyne' / info.filename
        if target.exists():
            payload = target.read_bytes()
        else:
            if not hasattr(local, 'reader'):
                local.reader = RangeFile(url)
                assert local.reader.etag == remote.etag and local.reader.size == remote.size
                readers.append(local.reader)
            reader = local.reader
            reader.seek(info.header_offset)
            # A ZIP local extra field is at most 65535 bytes. Bounded overread
            # avoids another TLS connection for every member's tiny header.
            data = reader.read(30 + len(info.filename.encode()) + 65535 + info.compress_size)
            header = struct.unpack('<4s5H3I2H', data[:30])
            assert header[0] == b'PK\x03\x04' and header[3] == info.compress_type
            name_length, extra_length = header[-2:]
            assert data[30:30 + name_length].decode('utf-8') == info.filename
            start = 30 + name_length + extra_length
            compressed = data[start:start + info.compress_size]
            assert len(compressed) == info.compress_size
            if info.compress_type == zipfile.ZIP_STORED:
                payload = compressed
            elif info.compress_type == zipfile.ZIP_DEFLATED:
                payload = zlib.decompress(compressed, -15)
            else:
                raise ValueError('Unsupported original compression method')
        assert len(payload) == info.file_size and zlib.crc32(payload) == info.CRC
        assert len(payload) % 16 == 0
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            temporary = target.with_name(target.name + f'.prefetch-{os.getpid()}-{threading.get_ident()}')
            temporary.write_bytes(payload)
            temporary.replace(target)
        return info.filename, {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                               'original_zip_crc32': f'{info.CRC:08x}'}

    save()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            pending = [pool.submit(fetch, info) for info in infos]
            for future in concurrent.futures.as_completed(pending):
                name, row = future.result()
                state['files'][name] = row
                if len(state['files']) % 10 == 0:
                    print(f'Prefetched and CRC-checked {len(state["files"])}/333', flush=True)
                    save()
        state['status'] = 'prefetched_and_crc_verified'
        save()
    except Exception as exc:
        state.update(status='failed', error=repr(exc))
        save()
        raise


if __name__ == '__main__':
    main()
