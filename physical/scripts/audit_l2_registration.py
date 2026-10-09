"""Descriptive geometry and registration controls on a confirmed fixed session.

Nearest-neighbour distances are to a raw reference cloud, not the algorithm's
internal map. Normal statistics describe sampled returns; they are not a
hardware fault diagnosis or an independent metric pose reference.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree


def rotation(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def cloud_at(dataset,row):
    with np.load(dataset/row["cloud"]) as archive:
        xyz=archive["xyzi"][:,:3].astype(np.float64)
    ranges=np.linalg.norm(xyz,axis=1)
    xyz=xyz[np.isfinite(xyz).all(axis=1)&(ranges>0.2)&(ranges<20)]
    _,unique=np.unique(np.floor(xyz/0.08).astype(np.int64),axis=0,return_index=True)
    return xyz[unique]


def distances(tree,xyz):
    d=tree.query(xyz,k=1,workers=2)[0]
    return {"median_m":float(np.median(d)),"p95_m":float(np.percentile(d,95)),
            "within_0_3m_fraction":float(np.mean(d<0.3))}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("dataset",type=Path)
    ap.add_argument("run",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((args.dataset/"clouds.json").read_text())
    poses=json.loads((args.run/"poses.json").read_text())
    by_stamp={p["stamp_ns"]:p for p in poses if p["covariance0"]<9999}
    rows=[r for r in manifest["pairs"] if round(r["stamp_s"]*1e9) in by_stamp]
    reference_pose=by_stamp[round(rows[0]["stamp_s"]*1e9)]
    ref_rot=rotation(reference_pose["xyzw"]); ref_pos=np.asarray(reference_pose["xyz"])
    ref_tree=cKDTree(cloud_at(args.dataset,rows[0]))
    angles=[]; yaws=[]; times=[]; translation=[]
    for row in rows:
        pose=by_stamp[round(row["stamp_s"]*1e9)]
        rel_rot=ref_rot.T@rotation(pose["xyzw"])
        angles.append(float(np.degrees(np.arccos(np.clip((np.trace(rel_rot)-1)/2,-1,1)))))
        yaws.append(np.arctan2(rel_rot[1,0],rel_rot[0,0]))
        times.append(row["stamp_s"]-rows[0]["stamp_s"])
        translation.append(np.linalg.norm(np.asarray(pose["xyz"])-ref_pos))
    unwrapped=np.degrees(np.unwrap(yaws))
    indices=np.unique(np.r_[np.linspace(1,len(rows)-1,26,dtype=int),np.argmax(angles)])
    samples=[]
    for i in indices:
        row=rows[i]; xyz=cloud_at(args.dataset,row)
        pose=by_stamp[round(row["stamp_s"]*1e9)]
        rel_rot=ref_rot.T@rotation(pose["xyzw"])
        rel_pos=ref_rot.T@(np.asarray(pose["xyz"])-ref_pos)
        transformed=xyz@rel_rot.T+rel_pos
        tree=cKDTree(xyz)
        d,neighbours=tree.query(xyz,k=min(20,len(xyz)),workers=2)
        local=xyz[neighbours]; centered=local-local.mean(axis=1,keepdims=True)
        covariance=np.einsum("nki,nkj->nij",centered,centered)/local.shape[1]
        eigenvalues,eigenvectors=np.linalg.eigh(covariance)
        planar=(eigenvalues[:,0]/np.maximum(eigenvalues.sum(axis=1),1e-12)<0.03)&(d[:,-1]<0.4)
        normals=eigenvectors[planar,:,0]
        normal_z=float(np.mean(np.abs(normals[:,2])>np.cos(np.radians(15)))) if len(normals) else None
        normal_eigen=np.linalg.eigvalsh(normals.T@normals/len(normals)).tolist() if len(normals) else None
        bins=np.unique(np.floor((np.arctan2(xyz[:,1],xyz[:,0])+np.pi)/(2*np.pi/72)).astype(int)%72)
        samples.append({"source_index":row["index"],"elapsed_s":times[i],"voxel_points":len(xyz),
                        "rotation_deg":angles[i],"unwrapped_yaw_deg":float(unwrapped[i]),
                        "translation_m":float(translation[i]),
                        "identity_to_reference":distances(ref_tree,xyz),
                        "estimated_pose_to_reference":distances(ref_tree,transformed),
                        "occupied_return_azimuth_bins_of_72":len(bins),
                        "planar_neighbourhood_fraction":float(planar.mean()),
                        "planar_normals_within_15deg_of_z_fraction":normal_z,
                        "normal_second_moment_eigenvalues":normal_eigen})
    slopes=np.polyfit(times,unwrapped,1)
    record={"kind":"fixed_session_registration_control","source_sha256":manifest["source_sha256"],
            "algorithm_result":str(args.run/"result.json"),"reference_source_index":rows[0]["index"],
            "voxel_m":0.08,"range_m":[0.2,20],"sample_policy":"26 evenly spaced registered clouds plus maximum rotation",
            "normal_policy":"20 voxel neighbours, radius <=0.4m, smallest covariance eigenvalue/trace <0.03",
            "distance_policy":"One-way source to raw reference nearest neighbour; no outlier trimming; not an internal ICP residual",
            "limitations":"Sensor fixed by user confirmation; environment was not independently labelled. This does not identify a hardware fault.",
            "yaw_linear_fit_deg_per_s":float(slopes[0]),"yaw_linear_fit_rmse_deg":float(np.sqrt(np.mean((unwrapped-np.polyval(slopes,times))**2))),
            "samples":samples}
    (args.output/"audit.json").write_text(json.dumps(record,indent=2,allow_nan=False)+"\n")
    fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    axes[0,0].plot(times,unwrapped); axes[0,0].set(ylabel="Unwrapped estimated yaw (deg)",xlabel="Time (s)",title="Fixed sensor: expected near zero")
    axes[0,1].plot(times,np.asarray(translation)*100); axes[0,1].axhline(5,color="green",ls="--",label="5 cm project target")
    axes[0,1].set(ylabel="Translation from first registered pose (cm)",xlabel="Time (s)"); axes[0,1].legend()
    for key,name in (("identity_to_reference","Identity pose"),("estimated_pose_to_reference","KISS estimated pose")):
        axes[1,0].plot([r["elapsed_s"] for r in samples],[r[key]["median_m"]*100 for r in samples],label=name)
    axes[1,0].set(ylabel="Median NN distance to raw reference (cm)",xlabel="Time (s)",title="Descriptive alignment control, not ATE"); axes[1,0].legend()
    axes[1,1].plot([r["elapsed_s"] for r in samples],[r["planar_normals_within_15deg_of_z_fraction"]*100 if r["planar_normals_within_15deg_of_z_fraction"] is not None else np.nan for r in samples])
    axes[1,1].set(ylabel="Near-vertical normals among planar supports (%)",xlabel="Time (s)",ylim=(0,100),title="Sampled planar normals: orientation distribution")
    for axis in axes.flat:
        axis.grid(alpha=0.25)
    fig.suptitle("Actual L2 / official SDK / KISS-ICP: fixed-session diagnostic")
    fig.savefig(args.output/"diagnostic.png",dpi=150)
    print(json.dumps({k:v for k,v in record.items() if k!="samples"},indent=2))


if __name__=="__main__":
    main()
