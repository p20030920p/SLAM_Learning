"""ROS 2/WSL offline RTAB-Map stereo/RGB-D/ICP, observed status and poses.

Only consumes exported recordings. No IMU, fabricated motion or ground truth.
Input stamps and stereo calibration are preserved; replay uses /clock.
"""
import argparse
from array import array as byte_array
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("dataset",type=Path)
    ap.add_argument("--mode",choices=("stereo","rgbd","lidar"),default="stereo")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--speed",type=float,default=1)
    ap.add_argument("--domain",type=int,default=83)
    ap.add_argument("--limit",type=int,default=0)
    ap.add_argument("--stride",type=int,default=1,help="Replay every Nth exported observation at its original time")
    ap.add_argument("--session-type",choices=("stationary","motion"),default="stationary",
                    help="motion reports trajectory extent and endpoint separation, never a static drift pass/fail")
    args=ap.parse_args()
    if args.speed<=0 or not 0<=args.domain<=232 or args.stride<1:
        ap.error("Invalid replay options")
    args.output.mkdir(parents=True,exist_ok=False)
    os.environ.update(ROS_DOMAIN_ID=str(args.domain),ROS_LOCALHOST_ONLY="1",OMP_NUM_THREADS="2")
    import cv2
    import numpy as np
    import rclpy
    from rclpy.node import Node
    from rclpy.executors import SingleThreadedExecutor
    from sensor_msgs.msg import Image,CameraInfo,PointCloud2,PointField
    from nav_msgs.msg import Odometry
    from rosgraph_msgs.msg import Clock
    from rtabmap_msgs.msg import OdomInfo

    dataset=json.loads((args.dataset/{"stereo":"stereo.json","rgbd":"rgbd.json","lidar":"clouds.json"}[args.mode]).read_text())
    if args.mode=="rgbd":
        if dataset.get("depth_aligned_to")!="color":
            ap.error("RGB-D replay requires SDK depth aligned to color")
        dataset["pairs"]=[dict(row,stamp_s=row["color_stamp_s"],
                               color=row["files"]["rgb_png"]["path"],depth=row["files"]["depth"]["path"])
                           for row in dataset["frames"]]
    if dataset.get("status")!="exported" or len(dataset.get("pairs",[]))<2 or args.limit==1 or args.limit<0:
        ap.error("Need an exported dataset and at least two input observations")
    pairs=dataset["pairs"][::args.stride][:args.limit or None]
    if len(pairs)<2:
        ap.error("Need at least two observations after stride/limit")
    name={"stereo":"physical_stereo_odometry","rgbd":"physical_rgbd_odometry","lidar":"physical_icp_odometry"}[args.mode]
    frame={"stereo":"camera_left_optical","rgbd":"camera_color_optical","lidar":"lidar"}[args.mode]
    parameters={"use_sim_time":True,"frame_id":frame,"odom_frame_id":"physical_odom",
                "publish_tf":False,"wait_imu_to_init":False,"qos":1,"publish_null_when_lost":True}
    if args.mode in ("stereo","rgbd"):
        parameters.update(approx_sync=False,qos_camera_info=1,topic_queue_size=20,sync_queue_size=20)
    else:
        parameters.update({"Icp/Strategy":"0","Icp/VoxelSize":"0.08",
                           "Icp/PointToPlane":"true","Icp/PointToPlaneK":"20",
                           "Icp/MaxCorrespondenceDistance":"0.3","Icp/Iterations":"30",
                           "Odom/Deskewing":"false","Odom/GuessMotion":"true"})
    parameter_file=args.output/"requested-parameters.yaml"
    parameter_file.write_text(json.dumps({name:{"ros__parameters":parameters}},indent=2)+"\n")
    executable={"stereo":"stereo_odometry","rgbd":"rgbd_odometry","lidar":"icp_odometry"}[args.mode]
    command=["ros2","run","rtabmap_odom",executable,
             "--ros-args","-r",f"__node:={name}","--params-file",str(parameter_file)]
    algorithm_name={"stereo":"stereo","rgbd":"RGB-D","lidar":"ICP"}[args.mode]
    result={"status":"running","algorithm":f"RTAB-Map {algorithm_name} odometry (F2M)",
            "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "mode":args.mode,"observer_version":2,
            "dataset":str(args.dataset.resolve()),"source_sha256":dataset["source_sha256"],
            "input_duration_s":pairs[-1]["stamp_s"]-pairs[0]["stamp_s"],
            "requested_pairs":len(pairs),"replay_speed":args.speed,"input_stride":args.stride,"command":command,
            "base_frame":frame+(": x right, y down, z forward" if args.mode!="lidar" else ": official SDK XYZ"),
            "ground_truth":"User-confirmed stationary; no external pose or metric range reference",
            "scope":"Static stability only, not moving SLAM or loop closure validation"}
    result["session_type"]=args.session_type
    if args.mode=="rgbd":
        result.update(source_session_note=dataset["source_session_note"],
            timestamp_policy="SDK-associated RGB/depth re-stamped to color time for exact ROS replay; native ~10ms skew retained in rgbd.json, not hardware synchronization",
            depth_policy="Native uint16 converted to 32FC1 meters with recorded depth_unit_m; invalid zero retained",
            quality_claim=False)
    if args.session_type=="motion":
        result.update(ground_truth="Operator-selected motion session; no independent pose or metric reference",
                      scope="Moving stereo/ICP odometry replay only; no loop-closure node or motion accuracy acceptance")
    rows=[]; poses=[]; sent={}; published=0; last_map=None; publish_timing=[]
    log=(args.output/"node.log").open("w")
    process=None; node=None; executor=None; spin_thread=None
    rclpy.init()
    try:
        node=Node("physical_stereo_replay")
        pubs=({side:(node.create_publisher(Image,f"/{side}/image_rect",10),
                     node.create_publisher(CameraInfo,f"/{side}/camera_info",10)) for side in ("left","right")}
              if args.mode=="stereo" else
              {"rgb":(node.create_publisher(Image,"/rgb/image",10),node.create_publisher(CameraInfo,"/rgb/camera_info",10)),
               "depth":(node.create_publisher(Image,"/depth/image",10),)} if args.mode=="rgbd" else
              {"cloud":(node.create_publisher(PointCloud2,"/scan_cloud",10),)})
        clockpub=node.create_publisher(Clock,"/clock",10)

        def stamp_key(stamp):
            return stamp.sec*1_000_000_000+stamp.nanosec

        def receive_info(msg):
            nonlocal last_map
            key=stamp_key(msg.header.stamp)
            rows.append({"stamp_ns":key,"lost":msg.lost,"features":msg.features,
                         "matches":msg.matches,"inliers":msg.inliers,
                         "local_map_size":msg.local_map_size,"time_estimation_s":msg.time_estimation,
                         "icp_inliers_ratio":msg.icp_inliers_ratio,"icp_correspondences":msg.icp_correspondences,
                         "icp_structural_complexity":msg.icp_structural_complexity,
                         "icp_structural_distribution":msg.icp_structural_distribution,
                         "latency_s":time.monotonic()-sent[key] if key in sent else None,
                         "word_inliers":list(msg.word_inliers)})
            # The final frame's actual algorithm-local 3D landmarks are retained.
            if len(msg.local_map_values):
                last_map=np.asarray([[p.x,p.y,p.z] for p in msg.local_map_values])

        def receive_odom(msg):
            p=msg.pose.pose
            poses.append({"stamp_ns":stamp_key(msg.header.stamp),
                          "xyz":[p.position.x,p.position.y,p.position.z],
                          "xyzw":[p.orientation.x,p.orientation.y,p.orientation.z,p.orientation.w],
                          "covariance0":msg.pose.covariance[0]})

        node.create_subscription(OdomInfo,"/odom_info",receive_info,2048)
        node.create_subscription(Odometry,"/odom",receive_odom,2048)
        executor=SingleThreadedExecutor(); executor.add_node(node)
        spin_thread=threading.Thread(target=executor.spin,daemon=True); spin_thread.start()
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        wait_until=time.monotonic()+30
        while not all(p.get_subscription_count()>0 for ps in pubs.values() for p in ps):
            time.sleep(0.05)
            if process.poll() is not None or time.monotonic()>wait_until:
                raise RuntimeError("Odometry subscriptions not ready; inspect node.log")
        # Discovery of publishers/subscribers is asynchronous.
        time.sleep(1)
        subprocess.run(["ros2","param","dump",f"/{name}","--output-dir",str(args.output)],
                       stdout=log,stderr=subprocess.STDOUT,timeout=20,check=True)
        wall_start=time.monotonic()
        for row in pairs:
            due=wall_start+(row["stamp_s"]-pairs[0]["stamp_s"])/args.speed
            delay=due-time.monotonic()
            if delay>0:
                time.sleep(delay)
            ns=round(row["stamp_s"]*1e9)
            clock=Clock(); clock.clock.sec=ns//1_000_000_000; clock.clock.nanosec=ns%1_000_000_000
            clockpub.publish(clock)
            sent[ns]=time.monotonic()
            for side in (("left","right") if args.mode=="stereo" else ()):
                image=cv2.imread(str(args.dataset/row[side]),cv2.IMREAD_GRAYSCALE)
                if image is None:
                    raise OSError(row[side])
                info=CameraInfo(); info.header.stamp=clock.clock; info.header.frame_id="camera_left_optical"
                # Right uses the common rectified optical frame; P encodes its baseline.
                i=dataset[side]; info.width=i["width"]; info.height=i["height"]
                info.distortion_model="plumb_bob"; info.d=[0.0]*5
                info.k=[i["fx"],0.0,i["ppx"],0.0,i["fy"],i["ppy"],0.0,0.0,1.0]
                info.r=[1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0]
                info.p=[i["fx"],0.0,i["ppx"],-i["fx"]*dataset["baseline_m"] if side=="right" else 0.0,
                        0.0,i["fy"],i["ppy"],0.0,0.0,0.0,1.0,0.0]
                msg=Image(); msg.header=info.header; msg.height=image.shape[0]; msg.width=image.shape[1]
                msg.encoding="mono8"; msg.step=msg.width; msg.data=byte_array("B",image.tobytes())
                pubs[side][1].publish(info); pubs[side][0].publish(msg)
            if args.mode=="rgbd":
                color=cv2.imread(str(args.dataset/row["color"]))
                raw_depth=cv2.imread(str(args.dataset/row["depth"]),cv2.IMREAD_UNCHANGED)
                if color is None or raw_depth is None or raw_depth.dtype!=np.uint16 or raw_depth.shape!=color.shape[:2]:
                    raise ValueError("RGB-D image or aligned depth shape/type invalid")
                depth=(raw_depth.astype(np.float32)*dataset["depth_unit_m"]).astype("<f4")
                i=dataset["color_intrinsics"]
                info=CameraInfo(); info.header.stamp=clock.clock; info.header.frame_id=frame
                info.width=i["width"]; info.height=i["height"]; info.distortion_model="plumb_bob"; info.d=[0.0]*5
                info.k=[i["fx"],0.0,i["ppx"],0.0,i["fy"],i["ppy"],0.0,0.0,1.0]
                info.r=[1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0]
                info.p=[i["fx"],0.0,i["ppx"],0.0,0.0,i["fy"],i["ppy"],0.0,0.0,0.0,1.0,0.0]
                pubs["rgb"][1].publish(info)
                for key,data,encoding,step in (("rgb",color,"bgr8",color.shape[1]*3),
                                               ("depth",depth,"32FC1",depth.shape[1]*4)):
                    msg=Image(); msg.header=info.header; msg.height=data.shape[0]; msg.width=data.shape[1]
                    msg.encoding=encoding; msg.step=step; msg.data=byte_array("B",data.tobytes())
                    pubs[key][0].publish(msg)
            if args.mode=="lidar":
                with np.load(args.dataset/row["cloud"]) as cloud:
                    xyzi=np.asarray(cloud["xyzi"],dtype="<f4")
                msg=PointCloud2(); msg.header.stamp=clock.clock; msg.header.frame_id=frame
                msg.height=1; msg.width=len(xyzi); msg.is_dense=True; msg.is_bigendian=False
                msg.fields=[PointField(name=field,offset=i*4,datatype=PointField.FLOAT32,count=1)
                            for i,field in enumerate(("x","y","z","intensity"))]
                msg.point_step=16; msg.row_step=16*len(xyzi); msg.data=byte_array("B",xyzi.tobytes())
                pubs["cloud"][0].publish(msg)
            published+=1
            completed=time.monotonic()
            publish_timing.append({"index":published-1,"stamp_ns":ns,
                "scheduled_elapsed_s":(row["stamp_s"]-pairs[0]["stamp_s"])/args.speed,
                "publish_completed_elapsed_s":completed-wall_start,
                "deadline_lateness_s":max(0.0,completed-due)})
            if published%100==0:
                print(f"published={published}/{len(pairs)} statuses={len(rows)} poses={len(poses)}",flush=True)
            if process.poll() is not None:
                raise RuntimeError(f"Odometry process exited {process.returncode}")
        result["wall_publish_s"]=time.monotonic()-wall_start
        if len(publish_timing)>1:
            intervals=np.diff([r["publish_completed_elapsed_s"] for r in publish_timing])
            result["actual_publish_hz"]=(len(publish_timing)-1)/(publish_timing[-1]["publish_completed_elapsed_s"]-publish_timing[0]["publish_completed_elapsed_s"])
            result["publish_interval_s"]={"median":float(np.median(intervals)),"p95":float(np.percentile(intervals,95))}
            result["publish_deadline_lateness_max_s"]=max(r["deadline_lateness_s"] for r in publish_timing)
        deadline=time.monotonic()+10
        while time.monotonic()<deadline and (len(rows)<published or len(poses)<published):
            time.sleep(0.05)
        result["wall_replay_s"]=time.monotonic()-wall_start
        result["status"]="evaluated" if rows else "no_algorithm_output"
    except Exception as e:
        result.update(status="failed",error=repr(e))
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL); process.wait()
        log.close()
        if executor is not None:
            executor.shutdown(timeout_sec=5)
        if spin_thread is not None:
            spin_thread.join(timeout=5)
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
        if last_map is not None:
            np.savez_compressed(args.output/"last_local_map.npz",xyz=last_map)
        result.update(published_pairs=published,status_messages=len(rows),odometry_messages=len(poses))
        if rows:
            result["lost_status_fraction"]=sum(r["lost"] for r in rows)/len(rows)
            result["status_output_fraction"]=len({r["stamp_ns"] for r in rows})/published
            result["pose_output_fraction"]=len({p["stamp_ns"] for p in poses})/published
            result["observed_output_fraction"]=min(result["status_output_fraction"],result["pose_output_fraction"])
            for name in ("features","inliers","time_estimation_s","latency_s","icp_inliers_ratio","icp_correspondences",
                         "icp_structural_complexity","icp_structural_distribution"):
                values=[r[name] for r in rows if r[name] is not None]
                result[name]={"median":float(np.median(values)),"p95":float(np.percentile(values,95))} if values else None
        valid=[p for p in poses if np.isfinite(p["covariance0"]) and p["covariance0"]<9999
               and np.isfinite(p["xyz"]).all() and np.isfinite(p["xyzw"]).all() and np.linalg.norm(p["xyzw"])>1e-9]
        result["valid_pose_count"]=len(valid)
        result["high_covariance_pose_count"]=len(poses)-len(valid)
        result["pose_filter_note"]="Initial/high-covariance discontinuity poses excluded; lost status separately counted"
        from live_metrics import match_observations
        candidates=[[round(row["stamp_s"]*1e9)] for row in pairs[:published]]
        valid_matches=match_observations(candidates,[p["stamp_ns"] for p in valid])
        tracked_matches=match_observations(candidates,[r["stamp_ns"] for r in rows if not r["lost"]])
        result["valid_tracking_input_fraction"]=len(valid_matches & tracked_matches)/published if published else 0
        result["coverage_policy"]="One-to-one native output matching to actual input within 1us; valid pose AND non-lost status"
        if valid:
            xyz=np.asarray([p["xyz"] for p in valid]); delta=xyz-xyz[0]
            q=np.asarray([p["xyzw"] for p in valid]); q/=np.linalg.norm(q,axis=1)[:,None]
            angles=np.degrees(2*np.arccos(np.clip(np.abs(q@q[0]),0,1)))
            result.update(translation_excursion_max_m=float(np.linalg.norm(delta,axis=1).max()),
                          translation_endpoint_separation_m=float(np.linalg.norm(delta[-1])),
                          rotation_excursion_max_deg=float(angles.max()),
                          rotation_endpoint_separation_deg=float(angles[-1]),
                          estimated_path_length_m=float(np.linalg.norm(np.diff(xyz,axis=0),axis=1).sum()))
            if args.session_type=="stationary":
                result.update(static_translation_max_m=result["translation_excursion_max_m"],
                              static_translation_final_m=result["translation_endpoint_separation_m"],
                              static_rotation_max_deg=result["rotation_excursion_max_deg"],
                              static_rotation_final_deg=result["rotation_endpoint_separation_deg"])
        if args.session_type=="stationary":
            result["static_gate"]={"max_translation_m":0.05,"max_rotation_deg":2.0,
                                   "loss_fraction":0.0,"minimum_output_fraction":0.99,
                                   "note":"Project engineering target, not device specification or ATE"}
            result["static_gate_passed"]=bool(result["status"]=="evaluated" and valid and
                result["valid_tracking_input_fraction"]>=0.99 and result["lost_status_fraction"]==0 and
                result["static_translation_max_m"]<=0.05 and result["static_rotation_max_deg"]<=2)
            if args.mode=="rgbd":
                result["clean_static_acceptance"]=None if not dataset["source_session_note"].get("pure_static_scene_eligible") else result["static_gate_passed"]
        else:
            result.update(static_gate=None,static_gate_passed=None,
                          trajectory_metrics_note="Estimated trajectory extent/path/endpoint separation; not drift, ATE or motion error without independent physical references")
            result["motion_tracking_summary"]={
                "valid_pose_fraction":len(valid)/published if published else 0,
                "minimum_available_fraction_target":0.95,
                "note":"Availability target only; inspect lost/output coverage separately. No motion precision gate was evaluated."}
        period=result["input_duration_s"]/max(1,len(pairs)-1)
        result["timing_gate"]={"input_period_s":period,"compute_p95_below_period":bool(rows and result["time_estimation_s"]["p95"]<period),
                               "callback_latency_p95_below_two_periods":bool(rows and result["latency_s"]["p95"]<period*2),
                               "note":"Observed software replay, not sensor acquisition latency or an unloaded benchmark"}
        for name,value in (("result.json",result),("status.json",rows),("poses.json",poses),("publish-timing.json",publish_timing)):
            (args.output/name).write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,indent=2))
    return int(result["status"]!="evaluated")


if __name__=="__main__":
    raise SystemExit(main())
