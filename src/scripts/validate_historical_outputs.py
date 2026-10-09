"""Recheck all seven historical-protocol maps and their original records."""
import argparse
import json
from pathlib import Path
from validate_kitti_prepared import sha256
from validate_kitti_results import validate_cloud

parser = argparse.ArgumentParser()
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
state = json.loads((args.run / 'outcomes.json').read_text())
assert state['status'] == 'executed_historical_protocol'
names = ['00-dufomap', '01-dufomap', '01-beautymap', '02-dufomap', '02-beautymap', '02-beautymap_xy05', '02-beautymap_xy20']
artifacts, maps = {}, {}
for name in [*names, '00-scores', '01-scores', '02-scores']:
    record_path = args.run / name / 'record.json'
    record = json.loads(record_path.read_text())
    assert record['status'] == 'executed' and record['exit_code'] == 0
    assert record['source_dirty_before'] == '' and record['source_dirty_after'] == ''
    for key, expected in record['artifacts'].items():
        path = Path(key) if Path(key).is_absolute() else record_path.parent / key
        assert path.stat().st_size == expected['bytes'] and sha256(path) == expected['sha256']
        if name in names and key.endswith('_output.pcd'):
            maps[name] = {'path': str(path), 'points': validate_cloud(path)}
            artifacts[str(path)] = expected
assert len(maps) == 7
prepared = json.loads((args.run / 'validation.json').read_text())['prepared']
for seq in prepared:
    prepared[seq]['released_comparison_performed'] = seq == '00'
    if seq != '00':
        prepared[seq]['same_release_point_count'] = None
        prepared[seq]['byte_identical_release_scans'] = None
result = {'status': 'validated', 'maps': maps, 'artifacts': artifacts, 'prepared': prepared,
          'scope': 'Seven completed original maps, finite geometry, layouts, SHA-256 and recorded original logs; only 00 was compared with a released input. No new accuracy formula.'}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'artifacts'}, indent=2), flush=True)
