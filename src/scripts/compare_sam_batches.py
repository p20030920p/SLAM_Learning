"""Compare saved author-batch and microbatch masks/features on common frames.

This checks numerical changes on observed frames; it does not prove equality
on unobserved frames. Trusted local pickle outputs only. No GPU/model execution.
"""
import argparse
import gzip
import hashlib
import json
import pickle
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment

parser=argparse.ArgumentParser()
parser.add_argument('--original',type=Path,required=True)
parser.add_argument('--compatible',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
original={p.name:p for p in args.original.glob('*.pkl.gz')}
compatible={p.name:p for p in args.compatible.glob('*.pkl.gz')}
common=sorted(set(original)&set(compatible))
assert common,'No completed common frame files'
rows=[]
for name in common:
    with gzip.open(original[name],'rb') as stream:a=pickle.load(stream)
    with gzip.open(compatible[name],'rb') as stream:b=pickle.load(stream)
    box_a,box_b=np.asarray(a['xyxy']),np.asarray(b['xyxy'])
    lo=np.maximum(box_a[:,None,:2],box_b[None,:,:2])
    hi=np.minimum(box_a[:,None,2:],box_b[None,:,2:])
    intersection=np.maximum(hi-lo,0).prod(-1)
    area_a=np.maximum(box_a[:,2:]-box_a[:,:2],0).prod(-1)
    area_b=np.maximum(box_b[:,2:]-box_b[:,:2],0).prod(-1)
    iou=intersection/np.maximum(area_a[:,None]+area_b[None,:]-intersection,1e-8)
    ia,ib=linear_sum_assignment(-iou)
    mask_ious=[];cosines=[]
    for x,y in zip(ia,ib):
        ma,mb=a['mask'][x].astype(bool),b['mask'][y].astype(bool)
        mask_ious.append(float(np.logical_and(ma,mb).sum()/max(np.logical_or(ma,mb).sum(),1)))
        fa,fb=a['image_feats'][x],b['image_feats'][y]
        cosines.append(float(np.dot(fa,fb)/(np.linalg.norm(fa)*np.linalg.norm(fb))))
    rows.append({'frame':name,'original_count':len(box_a),'compatible_count':len(box_b),
                 'mask_iou_min':min(mask_ious),'mask_iou_mean':float(np.mean(mask_ious)),
                 'clip_cosine_min':min(cosines),'clip_cosine_mean':float(np.mean(cosines)),
                 'original_sha256':hashlib.sha256(original[name].read_bytes()).hexdigest(),
                 'compatible_sha256':hashlib.sha256(compatible[name].read_bytes()).hexdigest()})
result={'status':'measured','matching':'Hungarian matching on box IoU, then mask IoU and CLIP cosine',
        'frames':rows,'scope':'Only common saved frames. Not proof of full-sequence or bitwise equality.'}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(result,indent=2)+'\n')
print('Compared '+str(len(rows))+' common frames; minimum mask IoU '+str(min(x['mask_iou_min'] for x in rows))+
      ', minimum CLIP cosine '+str(min(x['clip_cosine_min'] for x in rows)),flush=True)
