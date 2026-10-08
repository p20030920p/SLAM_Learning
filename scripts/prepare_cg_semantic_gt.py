"""Verify/extract the exact public ConceptGraphs semantic GT archive.

The mesh GT used by HOV-SG is a different input and cannot replace this HDF5 GT.
Download with the author's Google Drive ID before invoking this script.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--runtime', type=Path, required=True)
args = parser.parse_args()
r = args.runtime.resolve()
archive_path = r / 'downloads/conceptgraphs-Replica-semantic.zip'
partial = archive_path.with_suffix('.zip.partial')
if not archive_path.exists() and partial.exists():
    with zipfile.ZipFile(partial) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError('Archive CRC failed: ' + bad)
    partial.rename(archive_path)
destination = r / 'data/Replica-semantic'
destination.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive_path) as archive:
    bad = archive.testzip()
    if bad:
        raise RuntimeError('Archive CRC failed: ' + bad)
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if not target.is_relative_to(destination):
            raise ValueError('Unsafe archive path')
        archive.extract(member, destination)
scenes = {}
for scene in ['office_0', 'office_1', 'office_2', 'office_3', 'office_4', 'room_0', 'room_1', 'room_2']:
    sequence = destination / scene / 'Sequence_1'
    files = [sequence / 'traj_w_c.txt']
    files += [sequence / 'saved-maps-gt/pointclouds' / ('pc_' + name + '.h5')
              for name in ['points', 'colors', 'features', 'embeddings', 'confidences']]
    scenes[scene] = {str(path.relative_to(destination)): {
        'bytes': path.stat().st_size, 'sha256': sha256(path)} for path in files}
manifest = {'source': 'https://drive.google.com/file/d/1NhQIM5PCH5L5vkZDSRq6YF1bRaSX2aem/view',
            'archive_bytes': archive_path.stat().st_size, 'archive_sha256': sha256(archive_path),
            'zip_crc': 'verified', 'root': str(destination), 'scenes': scenes}
(r / 'conceptgraphs-semantic-gt-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Verified original ConceptGraphs HDF5 GT and Sequence_1 poses for all 8 scenes', flush=True)
