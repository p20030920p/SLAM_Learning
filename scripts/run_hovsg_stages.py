"""Serialize HOV-SG after the current ConceptGraphs chain on this one GPU."""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
parser.add_argument('--wait-outcomes',type=Path,required=True)
parser.add_argument('--name',required=True)
parser.add_argument('--scene',default='room0')
parser.add_argument('--sam-batch',type=int,default=16)
args=parser.parse_args()
r=args.runtime.resolve();root=r/'runs'/args.name
root.mkdir(parents=True,exist_ok=False)
scripts=Path(__file__).resolve().parent
state={'status':'waiting_for_conceptgraphs','wait_outcomes':str(args.wait_outcomes),'sam_batch':args.sam_batch,
       'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'pid':os.getpid(),'stages':{}}
def save(): (root/'outcomes.json').write_text(json.dumps(state,indent=2)+'\n')
def on_exception(kind,value,traceback):
    state.update(status='failed',error_type=kind.__name__,error=str(value));save()
    sys.__excepthook__(kind,value,traceback)
sys.excepthook=on_exception
def wait_gpu():
    while subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():time.sleep(10)
def fail(stage,code):
    state.update(status='failed',failed_stage=stage);state['stages'][stage]=code;save()
    raise RuntimeError('Author HOV-SG stage did not complete: '+stage)
save()
while True:
    previous=json.loads(args.wait_outcomes.read_text())
    if previous['status'] in ['executed_single_scene','failed','frontend_not_complete']:break
    time.sleep(10)
state['previous_chain_status']=previous['status'];state['status']='waiting_for_gpu';save();wait_gpu()
feature_name=args.name+'-features'
state.update(status='running_feature_map');save()
code=subprocess.call([sys.executable,str(scripts/'run_semantic_entry.py'),'--runtime',str(r),
    '--mode','hovsg','--scene',args.scene,'--name',feature_name,'--timeout','7200','--sam-batch',str(args.sam_batch)])
if code:fail('feature_map',code)
state['stages']['feature_map']=0;save()
python=r/'envs/hovsg/bin/python'
artifacts=r/'runs'/feature_name/'artifacts/replica'
subprocess.run([str(python),str(scripts/'validate_hovsg_outputs.py'),'--artifacts',str(artifacts),
    '--output',str(root/'validation.json')],check=True)
state['status']='waiting_for_ground_truth';save()
gt_manifest=r/'replica-original-manifest.json'
while not gt_manifest.is_file():time.sleep(10)
gt=json.loads(gt_manifest.read_text())
assert gt['gzip_crc']=='verified'
alias=gt['scenes'][args.scene]['original_scene_name']
work=root/'evaluation-work';work.mkdir()
wait_gpu();state['status']='running_evaluation';save()
source=r/'upstream/hovsg'
os.environ.update(OMP_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',MKL_NUM_THREADS='8',WANDB_MODE='disabled')
command=[python,source/'application/eval/evaluate_sem_seg.py','main.dataset=replica','main.scene_name='+alias,
    'main.feature_map_path='+str(artifacts),'main.replica_dataset_gt_path='+gt['root'],
    'main.replica_color_map='+str(work/'class_id_colors.json'),
    'models.clip.checkpoint='+str(r/'weights/laion2b_s32b_b79k.bin'),
    'hydra.run.dir='+str(work/'hydra')]
limited=['systemd-run','--user','--scope','--unit','slam-author-'+args.name+'-evaluation',
    '-p','MemoryMax=14G','-p','MemorySwapMax=2G',*map(str,command)]
code=subprocess.call([sys.executable,str(scripts/'record_command.py'),'--output',str(root/'evaluation'),
    '--cwd',str(work),'--source',str(source),'--method','HOV-SG-semantic-evaluation',
    '--scope','Original semantic evaluator, original Replica '+alias+' mesh/info; single scene; frontend SAM batch '+str(args.sam_batch)+' compatibility config; full RGB-D 1200x680, skip_frames=10',
    '--timeout','7200','--',*limited])
if code:fail('evaluation',code)
log=(root/'evaluation/run.log').read_text()
metrics={}
for metric in ['miou','fmiou','macc','pacc']:
    values=re.findall(r'^'+metric+r':\s+([0-9.eE+-]+)\s*$',log,re.MULTILINE)
    assert len(values)==1,(metric,values)
    metrics[metric]=float(values[0]);assert math.isfinite(metrics[metric])
(root/'metrics.json').write_text(json.dumps({'scene':args.scene,'gt_scene':alias,'units':'fraction (0..1)',
    'metrics':metrics,'scope':'Single scene, resource compatibility config. Original author evaluator, not eight-scene mean.'},indent=2)+'\n')
state['stages']['evaluation']=0;state['status']='executed_single_scene';save()
print('HOV-SG original feature-map/evaluation stages completed with recorded resource config',flush=True)
