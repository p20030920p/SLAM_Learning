"""Bind a failed local execution to kernel/unit evidence and preserve partial maps."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
parser.add_argument('--name',required=True)
parser.add_argument('--record',type=Path,required=True)
parser.add_argument('--unit',required=True)
parser.add_argument('--last-stage',required=True)
parser.add_argument('--preserve-map',type=Path)
args=parser.parse_args()
r=args.runtime.resolve();root=r/'runs'/args.name
assert root.resolve().is_relative_to(r/'runs')
record=json.loads(args.record.read_text())
assert record['status']=='failed' and record['exit_code']==-9
folder=root/'diagnostics';folder.mkdir(exist_ok=True)
assert not any((folder/name).exists() for name in ['systemd-oom.log','kernel-oom.log','failure-diagnosis.json']), 'Failure evidence already exists'
unit=subprocess.check_output(['journalctl','--user','-u',args.unit,'--no-pager'],text=True)
assert 'OOM killer' in unit
(folder/'systemd-oom.log').write_text(unit)
lines=subprocess.check_output(['journalctl','-k','--no-pager'],text=True).splitlines()
indices=[i for i,line in enumerate(lines) if args.unit in line and 'oom-kill:' in line]
assert indices
index=indices[-1]
start=max(0,index-110)
for i in range(index-1,start-1,-1):
    if 'invoked oom-killer' in lines[i]:start=i;break
(folder/'kernel-oom.log').write_text('\n'.join(lines[start:index+4])+'\n')
result={'status':'failed','exit_code':-9,'cause':'Memory cgroup OOM confirmed by kernel and systemd unit',
    'last_stage':args.last_stage,'record':str(args.record),'unit':args.unit,
    'scope':'Resource failure, not an algorithm-accuracy result. No final map/evaluation completion inferred.'}
if args.preserve_map:
    path=args.preserve_map.resolve()
    assert path.is_relative_to(r/'data') and path.is_file()
    destination=root/'partial-outputs'/path.name
    assert destination.resolve().is_relative_to(root) and not destination.exists()
    destination.parent.mkdir(exist_ok=True)
    hasher=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):hasher.update(block)
    digest=hasher.hexdigest()
    result['partial_map']={'original_path':str(path),'preserved_path':str(destination),
        'bytes':path.stat().st_size,'sha256':digest,'validity':'Unverified interrupted serialization; excluded from evaluation'}
    path.rename(destination)
(folder/'failure-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
