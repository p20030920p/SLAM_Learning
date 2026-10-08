"""Frozen main DUFOMap adapter on fixed-sensor hardware input, no fabricated GT.

Snapshot only required blobs from the specified commit into this run directory.
Main checkout, its pinned dataset, environment and recorded results stay intact.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import numpy as np


ap=argparse.ArgumentParser()
ap.add_argument("dataset",type=Path)
ap.add_argument("--main-repo",type=Path,required=True)
ap.add_argument("--commit",default="354b02d69ccc90304174f6d36010d25043d739ca")
ap.add_argument("--output",type=Path,required=True)
ap.add_argument("--fixed-sensor-session",action="store_true",
                help="Explicitly acknowledge that the input session has a physically fixed sensor")
args=ap.parse_args()
if not args.fixed_sensor_session:
    ap.error("This interface smoke uses identity poses: require --fixed-sensor-session for a confirmed fixed recording")
args.dataset=args.dataset.resolve(); args.output=args.output.resolve()
args.output.mkdir(parents=True,exist_ok=False)
manifest=json.loads((args.dataset/"clouds.json").read_text())
record={"kind":"hardware_main_adapter_smoke","method":"DUFOMap","status":"running",
        "started_at":datetime.now(timezone.utc).isoformat(),"main_commit":args.commit,
        "source_sha256":manifest["source_sha256"],"source_blobs":{},"exit_code":None,
        "pose_source":"Identity relative pose from user-confirmed fixed sensor session; not estimated odometry",
        "scope":"40 observations at approximately 1Hz; execution/interface smoke only",
        "fixed_sensor_session_acknowledged":True,
        "evaluation":{"SA":None,"DA":None,"reason":"No point-level static/dynamic annotation or event ground truth"}}
snapshot=args.output/"main-source"
for relative in ("src/slam_learning/__init__.py","src/slam_learning/adapters.py","src/slam_learning/pcd.py","configs/methods.json"):
    blob=subprocess.check_output(["git","-C",str(args.main_repo),"show",f"{args.commit}:{relative}"])
    destination=snapshot/relative; destination.parent.mkdir(parents=True,exist_ok=True); destination.write_bytes(blob)
    record["source_blobs"][relative]=hashlib.sha256(blob).hexdigest()
sys.path.insert(0,str(snapshot/"src"))
from slam_learning.adapters import dufomap_run
from slam_learning.pcd import write_pcd,read_pcd
parameters=json.loads((snapshot/"configs/methods.json").read_text())["dufomap"]["parameters"]
record["parameters"]=parameters
record["package_versions"]={p:importlib.metadata.version(p) for p in ("dufomap","numpy")}
if record["package_versions"]["dufomap"]!="1.1.1":
    raise RuntimeError("Frozen main requires dufomap 1.1.1")
sequence=args.output/"input"; (sequence/"pcd").mkdir(parents=True)
elapsed=np.asarray([r["elapsed_s"] for r in manifest["pairs"]])
indices=np.unique(np.searchsorted(elapsed,elapsed[0]+np.arange(40)))
if len(indices)!=40 or indices[-1]>=len(elapsed):
    raise ValueError("Need 40 distinct observations spanning 39 seconds")
observations=[]; input_points=0
for i,index in enumerate(indices):
    row=manifest["pairs"][index]
    with np.load(args.dataset/row["cloud"]) as archive:
        xyz=archive["xyzi"][:,:3]
    path=sequence/"pcd"/f"{i:06d}.pcd"
    write_pcd(path,xyz,viewpoint=[0,0,0,1,0,0,0])
    input_points+=len(xyz)
    observations.append({"index":i,"source_index":int(index),"stamp_s":row["stamp_s"],"T_world_sensor":np.eye(4).tolist(),
                         "file":str(path.relative_to(args.output)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
(args.output/"observations.json").write_text(json.dumps(observations,indent=2)+"\n")
record["input_points"]=input_points; record["input_frames"]=len(observations)
original=Path.cwd(); start=time.perf_counter()
try:
    os.chdir(args.output)
    record["worker"]=dufomap_run(sequence,args.output/"cleaned.pcd",parameters,0)
    cloud=read_pcd(args.output/"cleaned.pcd")
    record.update(status="smoke_passed",exit_code=0,output_points=len(cloud.records),
                  output_finite=bool(np.isfinite(cloud.xyz()).all()),output_fields=list(cloud.records.dtype.names))
    record["output_input_point_ratio"]=len(cloud.records)/input_points
    record["ratio_note"]="Descriptive count ratio only, not static retention or dynamic removal accuracy"
except Exception as e:
    record.update(status="failed",exit_code=1,error=repr(e),traceback=traceback.format_exc())
finally:
    os.chdir(original)
    record["wall_execution_s"]=time.perf_counter()-start
    record["artifacts"]={name:{"sha256":hashlib.sha256((args.output/name).read_bytes()).hexdigest(),"bytes":(args.output/name).stat().st_size}
                         for name in ("cleaned.pcd","observations.json") if (args.output/name).exists()}
    (args.output/"record.json").write_text(json.dumps(record,indent=2,allow_nan=False)+"\n")
print(json.dumps(record,indent=2))
raise SystemExit(record["exit_code"])
