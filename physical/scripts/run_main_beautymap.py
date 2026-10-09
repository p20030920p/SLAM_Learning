"""Frozen main BeautyMap adapter on previously verified fixed-sensor observations.

The legacy gt_cloud.pcd filename contains only accumulated unlabeled geometry.
No evaluation annotation, main checkout mutation or invented motion pose is used.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import difflib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import numpy as np


WORKER="""
import json,sys
from pathlib import Path
spec=json.loads(Path(sys.argv[1]).read_text())
sys.path.insert(0,str(Path(spec['snapshot'])/'src'))
from slam_learning.adapters import beautymap_run
details=beautymap_run(Path(spec['sequence']),Path(spec['output']),Path(spec['upstream']),spec['parameters'],0)
Path(spec['worker_record']).write_text(json.dumps(details,indent=2)+'\\n')
"""


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pad_author_grid(source,destination,patch_path):
    """Diagnostic variant: enlarge empty grid domain, never add point returns.

    Used only with our fixed sensor inside the raw map XY bounding box. It is
    not a general boundary solution for trajectories outside the observed map.
    """
    shutil.copytree(source,destination,ignore=shutil.ignore_patterns(".git","__pycache__","data","assets"))
    path=destination/"main.py"; before=path.read_text()
    old="    Mpts.non_negatification_all_map_points()\n    Mpts.calculate_matrix_order()\n"
    new="""    Mpts.non_negatification_all_map_points()
    # PHYSICAL DIAGNOSTIC: pad empty XY domain by half the query width + 1 cell.
    # No geometry is created; integer cell shift preserves the original bins.
    padding_cells = int(np.ceil(dis_range / (2.0 * xy_resolution))) + 1
    padding_m = padding_cells * xy_resolution
    Mpts.coordinate_offset[:2] -= padding_m
    Mpts.non_negtive_points[:, :2] += padding_m
    Mpts.non_negtive_center[:2] += padding_m
    Mpts.calculate_matrix_order()
    Mpts.matrix_order += 2 * padding_cells
"""
    if before.count(old)!=1:
        raise ValueError("Pinned BeautyMap grid construction changed")
    after=before.replace(old,new); path.write_text(after)
    patch_path.write_text("".join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
                                                    fromfile="author/main.py",tofile="control/main.py")))
    return {"kind":"empty_grid_domain_padding_control","original_main_py_sha256":hashlib.sha256(before.encode()).hexdigest(),
            "patched_main_py_sha256":digest(path),"assumption":"Fixed sensor origin inside raw map XY extent",
            "geometry_added":False,"query_parameters_changed":False}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("fixed_session_input",type=Path,help="Successful DUFOMap hardware run with original observations and PCDs")
    ap.add_argument("--main-repo",type=Path,required=True)
    ap.add_argument("--upstream",type=Path,required=True)
    ap.add_argument("--commit",default="354b02d69ccc90304174f6d36010d25043d739ca")
    ap.add_argument("--fixed-sensor-session",action="store_true")
    ap.add_argument("--pad-small-map-control",action="store_true",
                    help="Diagnostic per-run author copy with empty grid padding; not unchanged main behavior")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if not args.fixed_sensor_session:
        ap.error("Require --fixed-sensor-session: source poses must come from a confirmed physically fixed session")
    args.fixed_session_input=args.fixed_session_input.resolve()
    args.upstream=args.upstream.resolve(); args.output=args.output.resolve()
    args.output.mkdir(parents=True,exist_ok=False)
    record={"kind":"hardware_main_adapter_smoke","method":"BeautyMap","status":"running",
            "started_at":datetime.now(timezone.utc).isoformat(),"main_commit":args.commit,"exit_code":None,
            "fixed_sensor_session_acknowledged":True,
            "pose_source":"Identity relative pose from user-confirmed fixed sensor session; not estimated odometry",
            "scope":"Reuse same 40 actual observations as DUFOMap; interface execution only",
            "map_input_note":"Legacy gt_cloud.pcd is unlabeled raw XYZ union, not ground truth",
            "evaluation":{"SA":None,"DA":None,"reason":"No point-level annotation or controlled dynamic events"}}
    start=time.perf_counter()
    try:
        snapshot=args.output/"main-source"; record["source_blobs"]={}
        for relative in ("src/slam_learning/__init__.py","src/slam_learning/adapters.py","src/slam_learning/pcd.py",
                         "configs/methods.json","configs/upstreams.json"):
            blob=subprocess.check_output(["git","-C",str(args.main_repo),"show",f"{args.commit}:{relative}"])
            destination=snapshot/relative; destination.parent.mkdir(parents=True,exist_ok=True); destination.write_bytes(blob)
            record["source_blobs"][relative]=hashlib.sha256(blob).hexdigest()
        expected=json.loads((snapshot/"configs/upstreams.json").read_text())["beautymap"]["commit"]
        actual=subprocess.check_output(["git","-C",str(args.upstream),"rev-parse","HEAD"],text=True).strip()
        dirty=subprocess.check_output(["git","-C",str(args.upstream),"status","--porcelain"],text=True).strip()
        if actual!=expected or dirty:
            raise ValueError("BeautyMap upstream must match the pinned main commit and be clean")
        record["upstream_commit"]=actual
        sys.path.insert(0,str(snapshot/"src"))
        from slam_learning.pcd import read_pcd,write_pcd
        previous=json.loads((args.fixed_session_input/"record.json").read_text())
        if previous["kind"]!="hardware_main_adapter_smoke" or previous["status"]!="smoke_passed":
            raise ValueError("Source is not a successful hardware adapter session")
        observations=json.loads((args.fixed_session_input/"observations.json").read_text())
        if digest(args.fixed_session_input/"observations.json")!=previous["artifacts"]["observations.json"]["sha256"]:
            raise ValueError("Observation manifest hash mismatch")
        record["source_sha256"]=previous["source_sha256"]
        record["source_observations_sha256"]=digest(args.fixed_session_input/"observations.json")
        sequence=args.output/"source-sequence"; (sequence/"pcd").mkdir(parents=True)
        clouds=[]
        for i,row in enumerate(observations):
            if not np.array_equal(np.asarray(row["T_world_sensor"]),np.eye(4)):
                raise ValueError("Only confirmed fixed-session identity poses are supported")
            source=args.fixed_session_input/row["file"]
            if digest(source)!=row["sha256"]:
                raise ValueError("Source PCD hash mismatch")
            cloud=read_pcd(source)
            if cloud.records.dtype.names!=("x","y","z") or cloud.viewpoint!=[0,0,0,1,0,0,0]:
                raise ValueError("Expected unlabeled XYZ and identity VIEWPOINT")
            clouds.append(cloud.xyz())
            shutil.copyfile(source,sequence/"pcd"/f"{i:06d}.pcd")
        raw=np.concatenate(clouds)
        if args.pad_small_map_control and not np.all((raw[:,:2].min(axis=0)<=0)&(raw[:,:2].max(axis=0)>=0)):
            raise ValueError("Padding control requires fixed sensor origin inside raw map XY extent")
        write_pcd(sequence/"gt_cloud.pcd",raw)
        record["input_frames"]=len(clouds); record["input_points"]=len(raw)
        parameters=json.loads((snapshot/"configs/methods.json").read_text())["beautymap"]["parameters"]
        record["parameters"]=parameters
        record["package_versions"]={name:importlib.metadata.version(name) for name in ("numpy","scipy","fire","dztimer","tqdm")}
        worker_upstream=args.upstream
        if args.pad_small_map_control:
            worker_upstream=args.output/"control-upstream"
            record["diagnostic_modification"]=pad_author_grid(args.upstream,worker_upstream,args.output/"grid-padding.patch")
            record["scope"]="Per-run author grid-padding diagnostic; frozen main adapter, modified author copy; no quality acceptance"
        spec={"snapshot":str(snapshot),"sequence":str(sequence),"output":str(args.output/"cleaned.pcd"),
              "upstream":str(worker_upstream),"parameters":parameters,"worker_record":str(args.output/"worker.json")}
        spec_path=args.output/"worker-input.json"; spec_path.write_text(json.dumps(spec,indent=2)+"\n")
        then=time.perf_counter()
        with (args.output/"worker.log").open("w") as log:
            run=subprocess.run([sys.executable,"-c",WORKER,str(spec_path)],cwd=args.output,stdout=log,stderr=subprocess.STDOUT)
        record["worker_wall_s"]=time.perf_counter()-then; record["exit_code"]=run.returncode
        if run.returncode:
            raise RuntimeError("Frozen main adapter failed; see worker.log")
        record["worker"]=json.loads((args.output/"worker.json").read_text())
        skip=re.findall(r"Skip the (\d+) frame:", (args.output/"worker.log").read_text())
        record["skipped_frame_indices"]=list(map(int,skip))
        record["observed_processed_frames"]=len(clouds)-len(skip)
        output=read_pcd(args.output/"cleaned.pcd")
        finite=bool(np.isfinite(output.xyz()).all())
        if not finite or not len(output.records):
            raise ValueError("Output must contain finite points")
        record.update(status="smoke_passed",output_points=len(output.records),output_finite=finite,
                      output_fields=list(output.records.dtype.names),output_input_point_ratio=len(output.records)/len(raw))
        record["ratio_note"]="Point count ratio only, not static retention or dynamic removal accuracy"
    except Exception as e:
        record.update(status="failed",error=repr(e),traceback=traceback.format_exc())
        if record["exit_code"] in (None,0): record["exit_code"]=1
    finally:
        record["wall_execution_s"]=time.perf_counter()-start
        record["artifacts"]={name:{"sha256":digest(args.output/name),"bytes":(args.output/name).stat().st_size}
                             for name in ("cleaned.pcd","worker.log","worker.json","compatibility.patch","grid-padding.patch","source-sequence/gt_cloud.pcd")
                             if (args.output/name).exists()}
        (args.output/"record.json").write_text(json.dumps(record,indent=2,allow_nan=False)+"\n")
    print(json.dumps(record,indent=2))
    return record["exit_code"]


if __name__=="__main__":
    raise SystemExit(main())
