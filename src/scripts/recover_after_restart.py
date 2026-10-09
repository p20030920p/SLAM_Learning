"""Mark only prior-boot running records as interrupted; never infer success."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
args=parser.parse_args()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
now=datetime.now(timezone.utc).isoformat()
count=0
for path in (args.runtime/'runs').rglob('*.json'):
    if path.name not in ['record.json','outcomes.json']:continue
    data=json.loads(path.read_text())
    previous=data.get('boot_id')
    status=data.get('status','')
    active=status=='running' or status.startswith('running_') or status.startswith('waiting_')
    if not (previous and previous!=boot and active):continue
    data.update(status='interrupted',recovered_at=now,
        interruption_reason='Previous WSL boot; old process cannot still be running. No algorithm-failure or successful-exit claim.')
    if path.name=='record.json':data['exit_code']=None
    path.write_text(json.dumps(data,indent=2)+'\n')
    count+=1;print('Marked prior-boot interruption: '+str(path),flush=True)
print('Recovered '+str(count)+' prior-boot records. Existing artifacts preserved; partial stages are not marked complete.',flush=True)
