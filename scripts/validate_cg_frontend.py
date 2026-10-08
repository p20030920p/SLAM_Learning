"""Check completeness and numerical validity of trusted local author outputs."""
import argparse
import gzip
import hashlib
import json
import pickle
from pathlib import Path
import numpy as np


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--scene-root', type=Path, required=True)
parser.add_argument('--variant', default='none')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
rgb = sorted((args.scene_root / 'results').glob('frame*.jpg'))
assert len(rgb) == 2000, ('Expected full 2000-frame author scene', len(rgb))
expected = {path.with_suffix('.pkl.gz').name for path in rgb[::5]}
detections = args.scene_root / ('gsa_detections_' + args.variant)
actual = {path.name for path in detections.glob('*.pkl.gz')}
assert actual == expected, {'missing': sorted(expected-actual), 'unexpected': sorted(actual-expected)}
manifest = {}
counts = []
for name in sorted(expected):
    path = detections / name
    with gzip.open(path, 'rb') as stream:
        result = pickle.load(stream)
    count = len(result['xyxy'])
    assert result['mask'].shape[0] == count
    assert np.asarray(result['image_feats']).shape == (count, 1024)
    assert np.asarray(result['text_feats']).shape == (count, 1024)
    for key in ['xyxy', 'confidence', 'image_feats', 'text_feats']:
        assert np.isfinite(result[key]).all(), (name, key)
    assert len(result['image_crops']) == count
    visualization = args.scene_root / ('gsa_vis_' + args.variant) / name.replace('.pkl.gz', '.jpg')
    assert visualization.is_file() and visualization.stat().st_size > 0
    for file in [path, visualization]:
        manifest[str(file)] = {'bytes': file.stat().st_size, 'sha256': sha256(file)}
    counts.append(count)
classes = args.scene_root / ('gsa_classes_' + args.variant + '.json')
json.loads(classes.read_text())
manifest[str(classes)] = {'bytes': classes.stat().st_size, 'sha256': sha256(classes)}
summary = {'status': 'validated', 'source_frames': len(rgb), 'stride': 5, 'processed_frames': len(expected),
           'variant': args.variant, 'detections_total': sum(counts), 'detections_min': min(counts),
           'detections_max': max(counts), 'feature_dimension': 1024, 'artifacts': manifest}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(summary, indent=2) + '\n')
print('Validated all 400 expected masks/features/visualizations, finite 1024D CLIP features', flush=True)
