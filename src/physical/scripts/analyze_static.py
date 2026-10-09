"""Summarize a user-confirmed fixed-device session; do not overwrite raw data."""
import argparse
import json
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("session",type=Path)
    args=ap.parse_args()
    camera=json.loads((args.session/"camera/capture.json").read_text(encoding="utf-8"))
    lidar=json.loads((args.session/"l2/audit.json").read_text(encoding="utf-8"))
    a=np.loadtxt(args.session/"l2/imu.csv",delimiter=",",skiprows=1)
    elapsed=a[:,2]-a[0,2]
    train=a[elapsed<10]
    test=a[elapsed>=10]
    if len(train)<100 or len(test)<100:
        raise ValueError("Need >10 seconds of data and separate calibration/evaluation samples")
    bias=np.mean(train[:,7:10],axis=0)
    residual=np.linalg.norm(test[:,7:10]-bias,axis=1)
    gyro_mean=np.mean(test[:,7:10],axis=0)
    accel_mean=np.mean(test[:,10:13],axis=0)
    result={"kind":"static_sensor_audit","user_confirmed_fixed":True,
        "algorithm_evaluation_completed":False,
        "session":str(args.session),
        "camera":{"streams":camera["streams"],"depth_valid_fraction_median":camera["depth_valid_fraction_median"],
            "center_depth_median_m":camera["center_depth_median_m"],"center_depth_temporal_std_m":camera["center_depth_temporal_std_m"],
            "reference_range_available":False},
        "l2_transport_and_clock":lidar,
        "imu":{"calibration_window_host_s":10,"evaluation_sample_count":len(test),
            "gyro_raw_mean":gyro_mean.tolist(),"gyro_first10s_bias_estimate":bias.tolist(),
            "gyro_std_per_axis":np.std(test[:,7:10],axis=0).tolist(),
            "gyro_bias_subtracted_norm_median":float(np.median(residual)),
            "gyro_bias_subtracted_norm_p95":float(np.percentile(residual,95)),
            "accel_mean":accel_mean.tolist(),"accel_mean_norm":float(np.linalg.norm(accel_mean)),
            "accel_std_per_axis":np.std(test[:,10:13],axis=0).tolist(),
            "note":"Raw SDK angular-velocity convention retained; no unit change or permanent calibration applied. Validate unit/axis with controlled rotation before LIO."}}
    (args.session/"static-audit.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
