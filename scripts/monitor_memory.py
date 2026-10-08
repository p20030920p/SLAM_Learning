"""Observe an existing systemd cgroup without changing the author process."""
import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--unit',required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--interval',type=float,default=15)
parser.add_argument('--seconds',type=float,default=7200)
args=parser.parse_args()
assert args.unit.startswith('slam-author-') and args.unit.endswith('.scope')
assert args.interval>=1 and args.seconds>=args.interval
assert not args.output.exists(), 'Observation report must be new'
group=subprocess.check_output(['systemctl','--user','show',args.unit,'-p','ControlGroup','--value'],text=True).strip()
assert group.startswith('/user.slice/')
folder=Path('/sys/fs/cgroup')/group.lstrip('/')
report={'status':'observing','unit':args.unit,'cgroup':str(folder),'samples':[],
    'scope':'Observed cgroup memory includes page cache; swap is reported separately. Sampling starts after process launch, so maxima are lower bounds, not whole-run peaks or paper performance results.'}
args.output.parent.mkdir(parents=True,exist_ok=True)
def save():
    temporary=args.output.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(report,indent=2)+'\n')
    temporary.replace(args.output)
start=time.monotonic()
while True:
    if not (folder/'memory.current').exists():
        report['status']='cgroup_disappeared';break
    sample={'utc':datetime.now(timezone.utc).isoformat()}
    try:
        for key in ['memory.current','memory.swap.current','memory.max','memory.swap.max']:
            sample[key]=int((folder/key).read_text().strip())
    except FileNotFoundError:
        report['status']='cgroup_disappeared';break
    report['samples'].append(sample)
    report['observed_max_memory_bytes']=max(row['memory.current'] for row in report['samples'])
    report['observed_max_swap_bytes']=max(row['memory.swap.current'] for row in report['samples'])
    save()
    if time.monotonic()-start>=args.seconds:
        report['status']='observation_time_limit';break
    time.sleep(args.interval)
save()
print(json.dumps({key:value for key,value in report.items() if key!='samples'}),flush=True)
