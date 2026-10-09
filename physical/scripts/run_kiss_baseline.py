"""Direct offline KISS-ICP baseline, no IMU or unverified deskewing timestamps."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import numpy as np
from pyquaternion import Quaternion
from kiss_icp.config import KISSConfig
from kiss_icp.kiss_icp import KissICP


ap=argparse.ArgumentParser()
ap.add_argument("dataset",type=Path)
ap.add_argument("--output",type=Path,required=True)
ap.add_argument("--prediction",choices=("constant_velocity","zero_delta_control"),default="constant_velocity",
                help="zero_delta_control disables velocity extrapolation; diagnostic, does not fix the output pose")
ap.add_argument("--repeat-first-cloud-control",action="store_true",
                help="Repeat identical first cloud at original timestamps; synthetic zero-motion input control")
args=ap.parse_args()
dataset=json.loads((args.dataset/"clouds.json").read_text())
args.output.mkdir(parents=True,exist_ok=False)
config=KISSConfig()
config.data.min_range=0.2; config.data.max_range=20.0; config.data.deskew=False
config.mapping.voxel_size=0.08
config.registration.max_num_threads=2
config.adaptive_threshold.initial_threshold=0.3
configuration=config.model_dump()
(args.output/"parameters.json").write_text(json.dumps(configuration,indent=2)+"\n")
result={"status":"running","algorithm":"KISS-ICP","mode":"lidar","package_version":importlib.metadata.version("kiss-icp"),
        "python":sys.version,"source_sha256":dataset["source_sha256"],"dataset":str(args.dataset.resolve()),
        "decoder":dataset.get("decoder"),"configuration":configuration,
        "input_duration_s":dataset["pairs"][-1]["stamp_s"]-dataset["pairs"][0]["stamp_s"],
        "ground_truth":"User-confirmed stationary original session; no independent metric pose reference",
        "scope":"Exploratory static control, direct offline execution, not live sensor latency or moving SLAM",
        "quality_limitation":"KISS-ICP API does not report a tracking-lost flag; finite pose is not proof of correct registration",
        "deskewing":False,"imu_used":False,"prediction_policy":args.prediction,
        "repeat_first_cloud_control":args.repeat_first_cloud_control,
        "is_diagnostic_control":args.prediction!="constant_velocity" or args.repeat_first_cloud_control}
if result["is_diagnostic_control"]:
    result["scope"]="Diagnostic control: not an unchanged KISS-ICP hardware baseline; output poses still estimated"
if args.repeat_first_cloud_control:
    result["ground_truth"]="Synthetic identical first-cloud repetition; not a new real sensor session"
poses=[]; statuses=[]; matrices=[]; durations=[]; start=time.perf_counter()
try:
    odom=KissICP(config)
    for i,row in enumerate(dataset["pairs"]):
        source_row=dataset["pairs"][0] if args.repeat_first_cloud_control else row
        with np.load(args.dataset/source_row["cloud"]) as archive:
            xyz=np.asarray(archive["xyzi"][:,:3],dtype=np.float64)
        then=time.perf_counter()
        if args.prediction=="zero_delta_control":
            odom.last_delta=np.eye(4)
        _,source=odom.register_frame(xyz,np.zeros(len(xyz),dtype=np.float64))
        duration=time.perf_counter()-then
        matrix=odom.last_pose.copy()
        finite=bool(np.isfinite(matrix).all())
        if not finite:
            raise ValueError(f"Nonfinite pose at observation {i}")
        q=Quaternion(matrix=matrix[:3,:3],atol=1e-5,rtol=1e-5)
        stamp=round(row["stamp_s"]*1e9)
        poses.append({"stamp_ns":stamp,"xyz":matrix[:3,3].tolist(),"xyzw":[q.x,q.y,q.z,q.w],
                      "covariance0":9999 if i==0 else 0,"covariance_note":"No estimated covariance exposed; this field is only renderer initialization marker"})
        statuses.append({"stamp_ns":stamp,"lost":None,"quality_state":"POSE OUTPUT; QUALITY UNVERIFIED",
                         "features":0,"inliers":None,"icp_inliers_ratio":None,"source_points":len(source),
                         "time_estimation_s":duration,"latency_s":None})
        matrices.append(matrix); durations.append(duration)
        if (i+1)%50==0:
            print(f"KISS-ICP observations={i+1}/{len(dataset['pairs'])}",flush=True)
    result["status"]="evaluated"
except Exception as e:
    result.update(status="failed",error=repr(e))
finally:
    result.update(wall_execution_s=time.perf_counter()-start,published_pairs=len(poses),
                  odometry_messages=len(poses),valid_pose_count=max(0,len(poses)-1),
                  observed_output_fraction=len(poses)/len(dataset["pairs"]),lost_status_fraction=None)
    if len(matrices)>1:
        a=np.asarray(matrices)[1:]; relative=np.linalg.inv(a[0])@a
        translation=np.linalg.norm(a[:,:3,3]-a[0,:3,3],axis=1)
        angle=np.degrees(np.arccos(np.clip((np.trace(relative[:,:3,:3],axis1=1,axis2=2)-1)/2,-1,1)))
        result.update(static_translation_max_m=float(translation.max()),static_translation_final_m=float(translation[-1]),
                      static_rotation_max_deg=float(angle.max()),static_rotation_final_deg=float(angle[-1]))
        result["time_estimation_s"]={"median":float(np.median(durations)),"p95":float(np.percentile(durations,95))}
    result["static_gate_passed"]=bool(result["status"]=="evaluated" and result["observed_output_fraction"]>=0.99 and
        result.get("static_translation_max_m",float("inf"))<=0.05 and result.get("static_rotation_max_deg",float("inf"))<=2)
    result["static_gate"]={"max_translation_m":0.05,"max_rotation_deg":2,"note":"Project static stability gate; no tracking-lost state is available"}
    for name,value in (("result.json",result),("poses.json",poses),("status.json",statuses)):
        (args.output/name).write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")
print(json.dumps(result,indent=2))
raise SystemExit(int(result["status"]!="evaluated"))
