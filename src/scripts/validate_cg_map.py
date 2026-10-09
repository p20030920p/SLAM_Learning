"""Validate completed local original object maps and animation checkpoints."""
import argparse
import gzip
import hashlib
import json
import pickle
from pathlib import Path
import numpy as np

def sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):digest.update(block)
    return digest.hexdigest()

parser=argparse.ArgumentParser()
parser.add_argument('--scene-root',type=Path,required=True)
parser.add_argument('--experiment',default='none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--without-animation-checkpoints',action='store_true')
args=parser.parse_args()
post=args.scene_root/'pcd_saves'/('full_pcd_'+args.experiment+'_post.pkl.gz')
with gzip.open(post,'rb') as stream:result=pickle.load(stream)
objects=result['objects']
assert objects
points=0
for obj in objects:
    pcd=np.asarray(obj['pcd_np']);feature=np.asarray(obj['clip_ft'])
    assert pcd.ndim==2 and pcd.shape[1]==3 and len(pcd)>0
    assert feature.shape==(1024,)
    assert np.isfinite(pcd).all() and np.isfinite(feature).all()
    assert np.asarray(obj['pcd_color_np']).shape==pcd.shape
    points+=len(pcd)
cfg=result['cfg']
assert cfg.scene_id==args.scene_root.name and cfg.stride==5 and cfg.end==-1
folder=args.scene_root/'objects_all_frames'/args.experiment
frames=sorted(folder.glob('[0-9]*.pkl.gz'))
indices=[int(p.name.split('.')[0]) for p in frames]
if not args.without_animation_checkpoints:
    assert (folder/'meta.pkl.gz').is_file()
    assert indices and len(set(indices))==len(indices) and all(0<=i<400 for i in indices)
else:
    assert not frames, 'Do not confuse stale partial checkpoints with this checkpoint-free run'
paths=list((args.scene_root/'pcd_saves').glob('full_pcd_'+args.experiment+'*.pkl.gz'))
if not args.without_animation_checkpoints:paths+=frames+[folder/'meta.pkl.gz']
manifest={str(path):{'bytes':path.stat().st_size,'sha256':sha256(path)} for path in paths}
validation={'status':'validated','post_objects':len(objects),'point_memberships':points,
    'animation_checkpoints':len(frames),'animation_has_all_400_indices':indices==list(range(400)),
    'scene':cfg.scene_id,'stride':cfg.stride,'artifacts':manifest,
    'scope':'Saved object geometry/feature validity and checkpoint completeness only; not semantic accuracy'}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps({key:value for key,value in validation.items() if key!='artifacts'}),flush=True)
