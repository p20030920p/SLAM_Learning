"""Compare real frozen-main DUFOMap input/output using identical plot bounds."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("run",type=Path)
    args=ap.parse_args()
    record=json.loads((args.run/"record.json").read_text())
    if record["status"]!="smoke_passed":
        raise ValueError("No successful output to render")
    sys.path.insert(0,str(args.run/"main-source"/"src"))
    from slam_learning.pcd import read_pcd
    observations=json.loads((args.run/"observations.json").read_text())
    if hashlib.sha256((args.run/"cleaned.pcd").read_bytes()).hexdigest()!=record["artifacts"]["cleaned.pcd"]["sha256"]:
        raise ValueError("Output hash differs from record")
    clouds=[]
    for row in observations:
        path=args.run/row["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row["sha256"]:
            raise ValueError("Input hash differs from manifest")
        clouds.append(read_pcd(path).xyz())
    raw=np.concatenate(clouds); cleaned=read_pcd(args.run/"cleaned.pcd").xyz()
    bounds=np.column_stack((raw.min(axis=0),raw.max(axis=0)))
    fig,axes=plt.subplots(2,2,figsize=(12,9),constrained_layout=True)
    for col,(name,xyz) in enumerate((("RAW ACCUMULATION",raw),("DUFOMAP OUTPUT",cleaned))):
        # Fixed deterministic display thinning only; counts refer to full files.
        xyz=xyz[::max(1,int(np.ceil(len(xyz)/100000)))]
        for row,(a,b) in enumerate(((0,1),(0,2))):
            axis=axes[row,col]
            axis.scatter(xyz[:,a],xyz[:,b],s=0.25,c=xyz[:,2],cmap="viridis",vmin=bounds[2,0],vmax=bounds[2,1],rasterized=True)
            axis.scatter([0],[0],s=30,marker="+",color="red",label="sensor origin")
            axis.set(xlim=bounds[a],ylim=bounds[b],xlabel="XYZ"[a]+" (m)",ylabel="XYZ"[b]+" (m)",title=name if row==0 else "Side X/Z")
            axis.set_aspect("equal",adjustable="box"); axis.grid(alpha=0.2)
    fig.suptitle(f"Main DUFOMap interface smoke: {len(raw):,} input / {len(cleaned):,} output points\n"
                 "40 fixed-sensor observations; identity poses from fixed-session assumption\n"
                 f"Count ratio {record['output_input_point_ratio']*100:.2f}% is descriptive. No labels: SA / DA unavailable.",fontsize=12)
    output=args.run/"comparison.png"
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output,dpi=150)
    print(output)


if __name__=="__main__":
    main()
