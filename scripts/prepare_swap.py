"""Add an explicit temporary swap file inside this task's Linux runtime.

Run as root. This does not change fstab or WSL configuration. Existing files
are reused only with this helper's matching manifest; never reformatted.
"""
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
parser.add_argument('--gib',type=int,default=48)
args=parser.parse_args()
assert os.geteuid()==0, 'Run this resource setup as root'
assert 1<=args.gib<=64
r=args.runtime.resolve()
assert (r/'upstream/conceptgraphs/.git').exists(), 'Expected the dedicated author runtime'
folder=r/'resources'
assert folder.resolve().is_relative_to(r)
folder.mkdir(exist_ok=True)
path=folder/'author-temporary.swap'
manifest=folder/'swap-manifest.json'
assert path.resolve().is_relative_to(r) and not path.is_symlink()
before=Path('/proc/swaps').read_text()
size=args.gib*1024**3
if path.exists():
    previous=json.loads(manifest.read_text())
    assert previous['path']==str(path) and previous['bytes']==size and path.stat().st_size==size
else:
    free=os.statvfs(folder).f_bavail*os.statvfs(folder).f_frsize
    assert free>size+64*1024**3, 'Keep at least 64 GiB free beyond this temporary swap'
    descriptor=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    os.close(descriptor)
    subprocess.run(['fallocate','-l',str(size),str(path)],check=True)
    subprocess.run(['mkswap',str(path)],check=True)
    manifest.write_text(json.dumps({'path':str(path),'bytes':size,'status':'formatted_not_enabled'},indent=2)+'\n')
if not any(line.split()[0]==str(path) for line in before.splitlines()[1:]):
    subprocess.run(['swapon',str(path)],check=True)
after=Path('/proc/swaps').read_text()
assert any(line.split()[0]==str(path) for line in after.splitlines()[1:])
data={'status':'enabled','path':str(path),'bytes':size,'gib':args.gib,
    'checked_at':datetime.now(timezone.utc).isoformat(),'swaps_before':before,'swaps_after':after,
    'scope':'Temporary local resource compatibility; no algorithm/source/data/threshold change; not a paper resource-performance result',
    'persistent_configuration_changed':False,
    'cleanup':'After all jobs finish and RAM permits, run swapoff on this exact path as root, then remove this task-owned file. Not added to fstab.'}
manifest.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2),flush=True)
