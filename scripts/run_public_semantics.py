"""Continue the seven remaining public Replica scenes after room0 validation.

Serial, local execution only. Canonical sources stay unchanged. All SAM
microbatch/configuration variants remain explicit. Missing LLaVA/HM3D stages
are not silently replaced. No API requests are made by this orchestrator.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
parser.add_argument('--wait-cg',type=Path,required=True)
parser.add_argument('--wait-hov',type=Path,required=True)
parser.add_argument('--name',required=True)
parser.add_argument('--include-detect',action='store_true',help='Also run the unmodified author RAM+DINO frontend and Detect mapping/evaluation')
args=parser.parse_args()
r=args.runtime.resolve();root=r/'runs'/args.name
root.mkdir(parents=True,exist_ok=False)
(root/'orchestration.log').touch(exist_ok=False)
scripts=Path(__file__).resolve().parent
state={'status':'waiting_for_room0','pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
       'scope':'All 8 public Replica scenes, local computation; SAM-only microbatch16 compatibility; optional unchanged RAM+DINO Detect; no API/HM3D/LLaVA',
       'scenes':{}}
def save():(root/'outcomes.json').write_text(json.dumps(state,indent=2)+'\n')
def on_exception(kind,value,traceback):
    state.update(status='failed',error_type=kind.__name__,error=str(value));save()
    sys.__excepthook__(kind,value,traceback)
sys.excepthook=on_exception
def wait_terminal(path):
    while True:
        data=json.loads(path.read_text())
        if data['status'] in ['executed_single_scene','failed','frontend_not_complete']:return data
        if any(code != 0 for code in data.get('stages',{}).values()):
            # Older supervisor versions did not mark their parent terminal state
            # after an explicitly recorded nonzero child exit.
            data.update(status='failed',recovered_terminal_state='Nonzero child exit recorded')
            path.write_text(json.dumps(data,indent=2)+'\n');return data
        if data.get('boot_id') and data['boot_id']!=state['boot_id']:
            raise RuntimeError('Prerequisite supervisor belongs to a previous boot')
        time.sleep(10)
def wait_gpu():
    while subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():time.sleep(10)
def run_script(script,arguments):
    with (root/'orchestration.log').open('ab') as log:
        return subprocess.call([sys.executable,str(scripts/script),*map(str,arguments)],stdout=log,stderr=subprocess.STDOUT)

def run_detect(scene,row,rgb_record):
    prefix=args.name+'-'+scene+'-detect'
    state['status']='running_'+scene+'_detect_frontend';save();wait_gpu()
    code=run_script('run_semantic_entry.py',['--runtime',r,'--mode','cg-detect','--scene',scene,'--name',prefix+'-frontend'])
    row['detect_frontend_exit']=code;save()
    if code:
        row['detect_stages_exit']='not run; frontend failed';save();return False
    state['status']='running_'+scene+'_detect_stages';save()
    code=run_script('run_cg_stages.py',['--runtime',r,'--scene',scene,'--variant','detect',
        '--wait-record',r/'runs'/(prefix+'-frontend')/'record.json','--name',prefix+'-stages','--rgb-record',rgb_record])
    row['detect_stages_exit']=code;save();return code==0

save()
cg=wait_terminal(args.wait_cg)
hov=wait_terminal(args.wait_hov)
state['scenes']['room0']={'conceptgraphs':cg['status'],'hovsg':hov['status']};save()
if cg['status']!='executed_single_scene':raise RuntimeError('First complete CG chain failed; not repeating it across seven scenes')
hov_enabled=hov['status']=='executed_single_scene'
detect_enabled=args.include_detect
if detect_enabled:
    detect_enabled=run_detect('room0',state['scenes']['room0'],args.wait_cg.parent/'rgb-fusion/record.json')
    if not detect_enabled:
        state['scenes']['room0']['detect_note']='Do not repeat an unresolved first Detect failure across seven scenes';save()
for scene in ['office0','office1','office2','office3','office4','room1','room2']:
    row={};state['scenes'][scene]=row
    prefix=args.name+'-'+scene
    state.update(status='running_'+scene+'_cg_frontend');save();wait_gpu()
    frontend=prefix+'-cg-frontend'
    row['cg_frontend_exit']=run_script('run_cg_resource_frontend.py',[
        '--runtime',r,'--scene',scene,'--name',frontend,'--sam-batch','16']);save()
    if row['cg_frontend_exit']==0:
        state['status']='running_'+scene+'_cg_stages';save()
        cg_name=prefix+'-cg-stages'
        row['cg_stages_exit']=run_script('run_cg_stages.py',[
            '--runtime',r,'--scene',scene,'--wait-record',r/'runs'/frontend/'record.json','--name',cg_name]);save()
    else:row['cg_stages_exit']='not run; frontend failed'
    if detect_enabled and row['cg_stages_exit']==0:
        detect_enabled=run_detect(scene,row,r/'runs'/cg_name/'rgb-fusion/record.json')
    else:row['detect_stages_exit']='not run; disabled, unresolved Detect failure, or no validated same-scene RGB surface'
    if hov_enabled:
        state['status']='running_'+scene+'_hovsg';save()
        if row['cg_stages_exit']==0:
            wait=r/'runs'/cg_name/'outcomes.json'
        else:wait=args.wait_cg  # Completed first scene; HOV does not require CG's objects.
        row['hovsg_exit']=run_script('run_hovsg_stages.py',[
            '--runtime',r,'--scene',scene,'--wait-outcomes',wait,'--name',prefix+'-hovsg','--sam-batch','16']);save()
        if row['hovsg_exit']!=0:
            hov_enabled=False
            row['note']='Do not repeat an unresolved HOV failure on remaining scenes; CG may continue'
    else:row['hovsg_exit']='not run; unresolved first HOV failure'
    save()
complete_cg=all(row.get('cg_stages_exit')==0 for scene,row in state['scenes'].items() if scene!='room0')
complete_detect=args.include_detect and all(row.get('detect_stages_exit')==0 for row in state['scenes'].values())
for method,complete,exp in [
    ('cg',complete_cg,'none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub'),
    ('detect',complete_detect,'ram_withbg_allclasses_overlap_maskconf0.25_simsum1.2_dbscan.1')]:
    if not complete:continue
    wait_gpu();state['status']='running_unmodified_eight_scene_'+method+'_evaluation';save()
    source=r/'upstream/conceptgraphs'
    work=root/(method+'-full-evaluation-work');work.mkdir()
    os.environ.update(HF_HUB_CACHE=str(r/'cache/huggingface/hub'),OMP_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',MKL_NUM_THREADS='8')
    command=[r/'envs/conceptgraphs/bin/python',source/'conceptgraph/scripts/eval_replica_semseg.py',
        '--replica_root',r/'data/replica-full/Replica','--replica_semantic_root',r/'data/Replica-semantic',
        '--n_exclude','6','--pred_exp_name',exp]
    with (root/'orchestration.log').open('ab') as log:
        code=subprocess.call([sys.executable,str(scripts/'record_command.py'),'--output',str(root/(method+'-eight-scene-evaluation')),
            '--cwd',str(work),'--source',str(source),'--method','ConceptGraphs-original-eight-scene-evaluation',
            '--scope','UNMODIFIED original evaluator, all eight scenes, original HDF5 GT; '+('SAM-only batch16 compatibility' if method=='cg' else 'unchanged RAM+DINO box-prompted SAM frontend; actual mapping suffix from author command'),
            '--timeout','7200','--artifact',str(work/'results'/exp/'replica_ex6_results.csv'),'--',*map(str,command)],
            stdout=log,stderr=subprocess.STDOUT)
    state['eight_scene_'+method+'_evaluation_exit']=code;save()
state['status']='finished_with_recorded_outcomes';save()
print('Public semantic queue finished; read outcomes for exact completed/failed scope',flush=True)
