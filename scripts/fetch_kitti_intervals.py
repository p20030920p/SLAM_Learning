"""Fetch original KITTI ZIP members via HTTP Range, preserving their ZIP CRC.

This fetches the author's selected intervals, not the full 84.8 GB archive.
SemanticKITTI labels/estimated SuMa poses and KITTI calibration are separate
official inputs. KITTI GT poses are retained separately for pose experiments.
No API credentials, unofficial mirrors, or changed point/label contents.
"""
import argparse
import hashlib
import io
import json
import os
import time
import urllib.request
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


class RangeFile(io.RawIOBase):
    """Seekable ZIP64 input with bounded reads and strict HTTP consistency."""
    def __init__(self, url):
        self.url = url
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=60) as response:
            self.size = int(response.headers['Content-Length'])
            self.etag = response.headers['ETag']
            self.modified = response.headers.get('Last-Modified')
        self.position = 0
        self.transferred = 0
        self.cache_start = 0
        self.cache = b''

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if position < 0:
            raise ValueError('Negative ZIP offset')
        self.position = position
        return position

    def read(self, size=-1):
        size = min(self.size - self.position, size if size >= 0 else self.size)
        if size <= 0:
            return b''
        if size > 32 * 1024 * 1024:
            raise ValueError('Refusing oversized range; this is not a full-archive download')
        start = self.position
        if not (self.cache_start <= start and start + size <= self.cache_start + len(self.cache)):
            end = min(self.size - 1, start + max(size, 512 * 1024) - 1)
            for attempt in range(4):
                try:
                    request = urllib.request.Request(self.url, headers={
                        'Range': f'bytes={start}-{end}', 'If-Match': self.etag,
                        'Accept-Encoding': 'identity'})
                    with urllib.request.urlopen(request, timeout=90) as response:
                        if response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{self.size}':
                            raise RuntimeError('Server did not honor the exact HTTP Range')
                        if response.headers.get('ETag') != self.etag:
                            raise RuntimeError('Remote ZIP changed during download')
                        payload = response.read(end - start + 2)
                    if len(payload) != end - start + 1:
                        raise RuntimeError('Truncated HTTP Range')
                    self.cache_start, self.cache = start, payload
                    self.transferred += len(payload)
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    time.sleep(2 ** attempt)
        offset = start - self.cache_start
        payload = self.cache[offset:offset + size]
        self.position += len(payload)
        return payload


def full_zip(url, archive, destination):
    """Download small official ZIPs, check every CRC before extraction."""
    if not archive.exists():
        temporary = archive.with_suffix('.zip.partial')
        with urllib.request.urlopen(url, timeout=120) as response, temporary.open('wb') as output:
            expected = int(response.headers['Content-Length'])
            while block := response.read(1024 * 1024):
                output.write(block)
        if temporary.stat().st_size != expected:
            raise RuntimeError('Incomplete archive: ' + str(archive))
        temporary.rename(archive)
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            if not (destination / member.filename).resolve().is_relative_to(destination.resolve()):
                raise ValueError('ZIP path escape')
        bad = z.testzip()
        if bad:
            raise RuntimeError('CRC failed: ' + bad)
        z.extractall(destination)
    return {'url': url, 'bytes': archive.stat().st_size, 'sha256': sha256(archive), 'zip_crc': 'all members verified'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--name', default='kitti-selected-inputs-01')
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    run = runtime / 'runs' / args.name
    run.mkdir(parents=True, exist_ok=False)
    base = runtime / 'data/kitti-original'
    base.mkdir(parents=True, exist_ok=True)
    (runtime / 'downloads').mkdir(exist_ok=True)
    state = {'status': 'downloading', 'pid': os.getpid(), 'started_utc': datetime.now(timezone.utc).isoformat(),
             'intervals_inclusive': {'00': [4390, 4530], '01': [150, 250], '02': [860, 950]},
             'scope': 'Only author selected KITTI frames; original calibration, labels, SuMa poses; GT poses separate',
             'source_pages': ['https://www.semantic-kitti.org/dataset.html#download',
                              'https://github.com/ethz-asl/TULIP#data-preparation'],
             'archives': {}, 'members': {}}

    def save():
        (run / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')

    save()
    try:
        s3 = 'https://s3.eu-central-1.amazonaws.com/avg-kitti/'
        for name, url in [
            ('data_odometry_labels', 'https://www.semantic-kitti.org/assets/data_odometry_labels.zip'),
            ('data_odometry_calib', s3 + 'data_odometry_calib.zip'),
            ('data_odometry_poses', s3 + 'data_odometry_poses.zip')]:
            print('Fetching and checking ' + name, flush=True)
            state['archives'][name] = full_zip(url, runtime / 'downloads' / (name + '.zip'), base / name)
            save()
        remote = RangeFile(s3 + 'data_odometry_velodyne.zip')
        state['archives']['velodyne_partial'] = {'url': remote.url, 'archive_bytes': remote.size,
            'etag': remote.etag, 'last_modified': remote.modified,
            'integrity': 'Per-member original ZIP CRC + local SHA-256; entire archive NOT downloaded/hashed'}
        with zipfile.ZipFile(remote) as z:
            for seq, (start, end) in state['intervals_inclusive'].items():
                for frame in range(start, end + 1):
                    name = f'dataset/sequences/{seq}/velodyne/{frame:06d}.bin'
                    info = z.getinfo(name)
                    target = base / 'data_odometry_velodyne' / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.is_file():
                        payload = target.read_bytes()
                    else:
                        payload = z.read(info)  # zipfile verifies the original member CRC
                    if len(payload) != info.file_size or zlib.crc32(payload) != info.CRC or len(payload) % 16:
                        raise RuntimeError('Member integrity failed: ' + name)
                    if not target.exists():
                        temporary = target.with_suffix('.bin.partial')
                        temporary.write_bytes(payload)
                        temporary.rename(target)
                    state['members'][name] = {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                        'original_zip_crc32': f'{info.CRC:08x}', 'compressed_bytes': info.compress_size,
                        'zip_header_offset': info.header_offset}
                    if len(state['members']) % 10 == 0:
                        print(f'Original point clouds {len(state["members"])}/333; HTTP bytes {remote.transferred}', flush=True)
                        save()
        for seq, (start, end) in state['intervals_inclusive'].items():
            label_root = base / 'data_odometry_labels/dataset/sequences' / seq
            point_root = base / 'data_odometry_velodyne/dataset/sequences' / seq / 'velodyne'
            for frame in range(start, end + 1):
                point = point_root / f'{frame:06d}.bin'
                label = label_root / 'labels' / f'{frame:06d}.label'
                if label.stat().st_size // 4 != point.stat().st_size // 16:
                    raise RuntimeError('Point/label count mismatch')
                state['members'][str(label.relative_to(base))] = {'bytes': label.stat().st_size, 'sha256': sha256(label)}
            for path in [label_root / 'poses.txt', base / 'data_odometry_calib/dataset/sequences' / seq / 'calib.txt',
                         base / 'data_odometry_poses/dataset/poses' / (seq + '.txt')]:
                state['members'][str(path.relative_to(base))] = {'bytes': path.stat().st_size, 'sha256': sha256(path)}
        state['http_range_bytes_transferred'] = remote.transferred
        state['point_clouds'] = 333
        state['status'] = 'downloaded_and_verified'
        state['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save()
        (runtime / 'kitti-selected-manifest.json').write_text(json.dumps(state, indent=2) + '\n')
        print('Verified 333 original point clouds, matching label counts and both pose sources.', flush=True)
    except Exception as exc:
        state['status'], state['error'] = 'failed', repr(exc)
        save()
        raise


if __name__ == '__main__':
    main()
