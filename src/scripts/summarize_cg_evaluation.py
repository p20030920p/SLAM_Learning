"""Copy metrics from a successful original single-scene CSV, without recomputing."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--run-root',type=Path,required=True)
parser.add_argument('--scene',required=True)
args=parser.parse_args()
record_path=args.run_root/'evaluation/record.json'
record=json.loads(record_path.read_text())
assert record['status']=='executed' and record['exit_code']==0
assert record['method']=='ConceptGraphs-evaluation'
assert 'ONLY '+args.scene+' selected' in record['scope']
paths=[Path(name) for name in record['artifacts'] if name.endswith('replica_ex6_results.csv')]
assert len(paths)==1
path=paths[0]
digest=hashlib.sha256(path.read_bytes()).hexdigest()
assert digest==record['artifacts'][str(path)]['sha256']
rows=list(csv.DictReader(path.open()))
assert {row['scene_id'] for row in rows}=={args.scene,'all'}
result=[]
for row in rows:
    values={key:float(row[key]) for key in ['miou','mrecall','mprecision','mf1score','fmiou']}
    assert all(math.isfinite(value) and 0<=value<=100 for value in values.values())
    result.append({'scene_id':row['scene_id'],**values})
report={'status':'summarized_original_csv','scene':args.scene,'units':'percent',
    'rows':result,'csv':str(path),'csv_sha256':digest,'record':str(record_path),
    'excluded_classes':['other','floor','wall','ceiling','door','window'],
    'scope':'Original single-scene evaluator; all aggregates only this selected scene, not the eight-scene benchmark. Frontend/resource scope follows stage records. Native author GT support and interpolation; not a cross-method ranking or H1 test.'}
(args.run_root/'metrics.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
