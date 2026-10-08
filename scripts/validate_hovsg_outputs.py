"""Validate the original saved HOV-SG feature-map contract, without inference."""
import argparse
import json
from pathlib import Path
import open3d as o3d
import torch

parser=argparse.ArgumentParser()
parser.add_argument('--artifacts',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
mask=torch.load(args.artifacts/'mask_feats.pt',map_location='cpu',weights_only=True)
full=torch.load(args.artifacts/'full_feats.pt',map_location='cpu',weights_only=True)
pcd=o3d.io.read_point_cloud(str(args.artifacts/'full_pcd.ply'))
objects=sorted((args.artifacts/'objects').glob('pcd_*.ply'))
assert mask.ndim==2 and mask.shape[1]==1024 and mask.shape[0]>0
assert full.shape==(len(pcd.points),1024) and len(pcd.points)>0
assert len(objects)==mask.shape[0],(len(objects),mask.shape)
assert torch.isfinite(mask).all() and torch.isfinite(full).all()
for index in range(len(objects)):
    path=args.artifacts/'objects'/('pcd_'+str(index)+'.ply')
    assert path.is_file()
result={'status':'validated','mask_feature_shape':list(mask.shape),'full_feature_shape':list(full.shape),
        'object_pointcloud_files':len(objects),'full_points':len(pcd.points),'feature_dimension':1024,
        'scope':'Saved-feature contract only; no semantic-accuracy or hierarchy-completion claim'}
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
