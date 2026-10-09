"""Algorithm regression on an explicit synthetic interior-window fixture.

Compares original and padded copies of the same author implementation, using
the frozen main adapter. This is a software regression, not hardware accuracy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from run_main_beautymap import WORKER,pad_author_grid


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--frozen-main",type=Path,required=True)
    ap.add_argument("--upstream",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    args.frozen_main=args.frozen_main.resolve(); args.upstream=args.upstream.resolve(); args.output=args.output.resolve()
    args.output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(args.frozen_main/"src"))
    from slam_learning.pcd import write_pcd,read_pcd
    sequence=args.output/"fixture"; (sequence/"pcd").mkdir(parents=True)
    x,y=np.meshgrid(np.arange(100)+0.25,np.arange(100)+0.25)
    floor=np.column_stack((x.ravel(),y.ravel(),np.zeros(x.size)))
    static=np.asarray([[x,y,z] for x in (45.25,46.25,47.25) for y in (45.25,46.25,47.25) for z in (.5,1,1.5,2,2.5)])
    moving=np.asarray([[x,y,z] for x in (55.25,56.25) for y in (48.25,49.25) for z in (.5,1,1.5,2,2.5)])
    scans=[np.concatenate((floor,static,moving)) for _ in range(2)]+[np.concatenate((floor,static)) for _ in range(2)]
    for i,xyz in enumerate(scans):
        write_pcd(sequence/"pcd"/f"{i:06d}.pcd",xyz,viewpoint=[50,50,1,1,0,0,0])
    write_pcd(sequence/"gt_cloud.pcd",np.concatenate(scans))
    padded=args.output/"padded-upstream"
    modification=pad_author_grid(args.upstream,padded,args.output/"grid-padding.patch")
    record={"kind":"synthetic_algorithm_regression","fixture":"100m XY floor with static columns and a disappearing synthetic column; sensor (50,50,1); 40m query entirely inside map",
            "hardware_quality_claim":False,"input_frames":4,"modification":modification,"runs":{}}
    outputs=[]
    for name,upstream in (("original",args.upstream),("padded",padded)):
        run=args.output/name; run.mkdir()
        spec={"snapshot":str(args.frozen_main),"sequence":str(sequence),"output":str(run/"cleaned.pcd"),"upstream":str(upstream),
              "parameters":{"dis_range":40,"xy_resolution":1.0,"h_res":0.5},"worker_record":str(run/"worker.json")}
        path=run/"worker-input.json"; path.write_text(json.dumps(spec,indent=2)+"\n")
        with (run/"worker.log").open("w") as log:
            completed=subprocess.run([sys.executable,"-c",WORKER,str(path)],cwd=run,stdout=log,stderr=subprocess.STDOUT)
        if completed.returncode:
            raise RuntimeError(f"{name} fixture execution failed: see {run/'worker.log'}")
        output=read_pcd(run/"cleaned.pcd").xyz(); outputs.append(output)
        record["runs"][name]={"exit_code":completed.returncode,"output_points":len(output),
            "pcd_sha256":hashlib.sha256((run/"cleaned.pcd").read_bytes()).hexdigest()}
    record["output_xyz_identical"]=bool(np.array_equal(outputs[0],outputs[1]))
    expected=np.concatenate([np.concatenate((floor,static)) for _ in range(4)]).astype(np.float32)
    record["expected_static_output_points"]=len(expected)
    record["synthetic_dynamic_input_points"]=2*len(moving)
    record["outputs_match_known_static_geometry"]=[bool(np.array_equal(output,expected)) for output in outputs]
    record["pass"]=record["output_xyz_identical"] and all(record["outputs_match_known_static_geometry"])
    (args.output/"regression.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record,indent=2))
    return int(not record["pass"])


if __name__=="__main__":
    raise SystemExit(main())
