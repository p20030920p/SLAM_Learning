"""Record actual RealSense model and supported streams; never invent an IMU."""
import argparse
import collections
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import queue
import time

import cv2
import numpy as np
import pyrealsense2 as rs


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=30)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--record-raw",action="store_true")
    args=ap.parse_args()
    if args.seconds <= 0:
        ap.error("seconds must be positive")
    args.output.mkdir(parents=True,exist_ok=False)
    record={"started_at":datetime.now(timezone.utc).isoformat(),"status":"running","evaluation_completed":False,
            "sdk":importlib.metadata.version("pyrealsense2"),"requested_video":"640x480@30 color, depth, infrared1, infrared2"}
    pipeline=rs.pipeline()
    started=False
    samples=collections.defaultdict(list)
    q=queue.Queue(maxsize=4)
    video=None
    start=time.monotonic()
    processed=0
    valid=[]
    medians=[]
    try:
        devices=list(rs.context().query_devices())
        if len(devices)!=1:
            raise RuntimeError(f"Expected one RealSense, found {len(devices)}")
        device=devices[0]
        record["device"]={str(k).split(".")[-1]:device.get_info(k) for k in
            (rs.camera_info.name,rs.camera_info.serial_number,rs.camera_info.firmware_version,rs.camera_info.usb_type_descriptor) if device.supports(k)}
        supported={p.stream_type() for s in device.sensors for p in s.get_stream_profiles()}
        record["imu_available"]=rs.stream.accel in supported and rs.stream.gyro in supported
        config=rs.config()
        config.enable_device(device.get_info(rs.camera_info.serial_number))
        config.enable_stream(rs.stream.color,640,480,rs.format.bgr8,30)
        config.enable_stream(rs.stream.depth,640,480,rs.format.z16,30)
        for index in (1,2):
            config.enable_stream(rs.stream.infrared,index,640,480,rs.format.y8,30)
        if record["imu_available"]:
            config.enable_stream(rs.stream.accel)
            config.enable_stream(rs.stream.gyro)
        if args.record_raw:
            config.enable_record_to_file(str(args.output/"raw.db3"))

        def receive(frame):
            frames=list(frame.as_frameset()) if frame.is_frameset() else [frame]
            now=time.monotonic()
            for f in frames:
                p=f.get_profile()
                samples[f"{p.stream_type()}:{p.stream_index()}"].append([f.get_frame_number(),f.get_timestamp(),now,str(f.get_frame_timestamp_domain())])
            if frame.is_frameset():
                try:
                    q.put_nowait(frame.as_frameset())
                except queue.Full:
                    pass

        profile=pipeline.start(config,receive)
        started=True
        record["depth_scale_m"]=profile.get_device().first_depth_sensor().get_depth_scale()
        record["intrinsics"]={}
        record["extrinsics_to_depth"]={}
        depth_profile=profile.get_stream(rs.stream.depth)
        for p in profile.get_streams():
            key=f"{p.stream_type()}:{p.stream_index()}"
            if p.is_video_stream_profile():
                intr=p.as_video_stream_profile().get_intrinsics()
                record["intrinsics"][key]={k:getattr(intr,k) for k in ("width","height","fx","fy","ppx","ppy","coeffs")}
                record["intrinsics"][key]["model"]=str(intr.model)
            ext=p.get_extrinsics_to(depth_profile)
            record["extrinsics_to_depth"][key]={"rotation_column_major":ext.rotation,"translation_m":ext.translation}
        video=cv2.VideoWriter(str(args.output/"preview.mp4"),cv2.VideoWriter_fourcc(*"mp4v"),30,(1280,1000))
        if not video.isOpened():
            raise RuntimeError("Cannot open video writer")
        start=time.monotonic()
        while time.monotonic()-start<args.seconds:
            frames=q.get(timeout=5)
            color=frames.get_color_frame(); depth=frames.get_depth_frame()
            left=frames.get_infrared_frame(1); right=frames.get_infrared_frame(2)
            if not all((color,depth,left,right)):
                continue
            rgb=np.asanyarray(color.get_data()).copy()
            z=np.asanyarray(depth.get_data()).copy()
            ir1=np.asanyarray(left.get_data()).copy(); ir2=np.asanyarray(right.get_data()).copy()
            if time.monotonic()-start>=2:
                valid.append(float((z>0).mean()))
                roi=z[200:280,280:360]
                medians.append(float(np.median(roi[roi>0])*record["depth_scale_m"]) if (roi>0).any() else None)
            zcolor=cv2.applyColorMap(cv2.convertScaleAbs(z,alpha=255*record["depth_scale_m"]/5),cv2.COLORMAP_TURBO)
            zcolor[z==0]=0
            panes=[rgb,zcolor,cv2.cvtColor(ir1,cv2.COLOR_GRAY2BGR),cv2.cvtColor(ir2,cv2.COLOR_GRAY2BGR)]
            for pane,label in zip(panes,["RGB","RAW DEPTH: BLACK=INVALID, 0-5m","LEFT IR","RIGHT IR"]):
                cv2.putText(pane,label,(10,30),0,0.65,(255,255,255),2)
            canvas=np.vstack((np.hstack(panes[:2]),np.hstack(panes[2:]),np.zeros((40,1280,3),dtype=np.uint8)))
            cv2.putText(canvas,f"{record['device']['name']} RAW CAPTURE {time.monotonic()-start:.1f}s | NO SLAM | IMU={record['imu_available']}",(10,986),0,0.65,(255,255,255),1)
            video.write(canvas)
            processed+=1
            if time.monotonic()-start>=2 and not (args.output/"preview.png").exists():
                cv2.imwrite(str(args.output/"preview.png"),canvas)
                cv2.imwrite(str(args.output/"color.png"),rgb)
                cv2.imwrite(str(args.output/"depth.png"),z)
                cv2.imwrite(str(args.output/"ir1.png"),ir1)
                cv2.imwrite(str(args.output/"ir2.png"),ir2)
        record["status"]="received" if all(samples[f"stream.{s}:{i}"] for s,i in (("color",0),("depth",0),("infrared",1),("infrared",2))) else "incomplete"
    except Exception as e:
        record.update(status="failed",error=repr(e))
    finally:
        record["elapsed_seconds"]=time.monotonic()-start
        if started:
            pipeline.stop()
        if video:
            video.release()
        record["streams"]={}
        for key,rows in samples.items():
            # A synchronized frameset can repeat a slower frame; count unique frames.
            unique={r[0]:r for r in rows}
            a=np.asarray([[r[0],r[1],r[2]] for r in unique.values()])
            d=np.diff(a[:,1]); n=np.diff(a[:,0])
            record["streams"][key]={"unique_frames":len(a),"sensor_hz":1000*(len(a)-1)/(a[-1,1]-a[0,1]) if len(a)>1 else None,
                "sequence_missing":int(np.maximum(n-1,0).sum()),"timestamp_non_increasing":int((d<=0).sum()),
                "max_sensor_gap_ms":float(d.max()) if len(d) else None,"timestamp_domains":sorted({r[3] for r in rows})}
        record["processed_video_frames"]=processed
        record["depth_valid_fraction_median"]=float(np.median(valid)) if valid else None
        finite=[x for x in medians if x is not None]
        record["center_depth_median_m"]=float(np.median(finite)) if finite else None
        record["center_depth_temporal_std_m"]=float(np.std(finite)) if finite else None
        record["depth_note"]="Whole-frame fill and central ROI describe this scene; no measured range target or accuracy claim."
        (args.output/"frames.json").write_text(json.dumps(samples)+"\n",encoding="utf-8")
        raw=args.output/"raw.db3"
        if raw.exists():
            with raw.open("rb") as f:
                record["raw"]={"bytes":raw.stat().st_size,"sha256":hashlib.file_digest(f,"sha256").hexdigest()}
        (args.output/"capture.json").write_text(json.dumps(record,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(record,indent=2))
    return int(record["status"]!="received")


if __name__=="__main__":
    raise SystemExit(main())
