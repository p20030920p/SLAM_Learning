"""Execute a pinned author semantic entry with explicit paths and resource bounds."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
parser.add_argument('--mode',choices=['hovsg','cg-none','cg-detect'],required=True)
parser.add_argument('--scene',default='room0')
parser.add_argument('--name',required=True)
parser.add_argument('--timeout',type=int,default=7200)
parser.add_argument('--allocator-conf',default='')
parser.add_argument('--sam-batch',type=int,default=144)
args=parser.parse_args()
r=args.runtime.resolve()
active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
if active:raise RuntimeError('A CUDA process is active; refusing a concurrent GPU experiment')
os.environ.update(OMP_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',MKL_NUM_THREADS='8',WANDB_MODE='disabled',
                  HF_HUB_CACHE=str(r/'cache/huggingface/hub'),
                  GSA_PATH=str(r/'dependencies/Grounded-Segment-Anything'))
if args.allocator_conf:os.environ['PYTORCH_CUDA_ALLOC_CONF']=args.allocator_conf
output=r/'runs'/args.name
if args.mode=='hovsg':
    source=r/'upstream/hovsg';cwd=source
    command=[r/'envs/hovsg/bin/python','application/semantic_segmentation.py',
        'main.dataset=replica','main.scene_id='+args.scene,
        'main.dataset_path='+str(r/'data/replica-full/Replica'/args.scene),
        'main.save_path='+str(output/'artifacts'),
        'models.clip.checkpoint='+str(r/'weights/laion2b_s32b_b79k.bin'),
        'models.sam.checkpoint='+str(r/'weights/sam_vit_h_4b8939.pth'),
        'hydra.run.dir='+str(output/'hydra')]
    if args.sam_batch != 144:command+=['models.sam.points_per_batch='+str(args.sam_batch)]
    artifacts=[output/'artifacts/replica'/name for name in ['full_pcd.ply','masked_pcd.ply','mask_feats.pt','full_feats.pt']]
else:
    source=r/'upstream/conceptgraphs';cwd=source/'conceptgraph'
    command=[r/'envs/conceptgraphs/bin/python','scripts/generate_gsa_results.py',
        '--dataset_root',r/'data/replica-full/Replica','--dataset_config',
        source/'conceptgraph/dataset/dataconfigs/replica/replica.yaml','--scene_id',args.scene,
        '--class_set','none' if args.mode=='cg-none' else 'ram','--stride','5']
    if args.mode=='cg-detect':command+=['--box_threshold','0.2','--text_threshold','0.2',
                                       '--add_bg_classes','--accumu_classes','--exp_suffix','withbg_allclasses']
    variant='none' if args.mode=='cg-none' else 'ram_withbg_allclasses'
    artifacts=[r/'data/replica-full/Replica'/args.scene/('gsa_classes_'+variant+'.json')]
scope=f'Full 2000-frame Replica {args.scene}, author {args.mode} entry; 14GiB RAM/2GiB swap cgroup; timeout {args.timeout}s'
if args.sam_batch==144 and args.mode!='cg-detect':scope+='; original SAM points_per_batch=144'
if args.mode=='cg-detect':scope+='; original RAM+DINO and box-prompted SAM'
if args.allocator_conf:scope+='; allocator environment variant '+args.allocator_conf
if args.sam_batch != 144:
    if args.mode!='hovsg':raise ValueError('SAM batch override is exposed by the original HOV-SG Hydra config only')
    scope+='; explicit resource compatibility config models.sam.points_per_batch='+str(args.sam_batch)+' instead of 144'
limited=['systemd-run','--user','--scope','--unit','slam-author-'+args.name,
         '-p','MemoryMax=14G','-p','MemorySwapMax=2G',*map(str,command)]
recorder=[sys.executable,str(Path(__file__).with_name('record_command.py')),
    '--output',str(output),'--cwd',str(cwd),'--source',str(source),'--method',args.mode,
    '--scope',scope,'--timeout',str(args.timeout)]
for artifact in artifacts:recorder+=['--artifact',str(artifact)]
raise SystemExit(subprocess.call([*recorder,'--',*limited]))
