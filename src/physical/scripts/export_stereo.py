"""Export actual rectified IR pairs and calibration from a RealSense recording."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import cv2
import numpy as np
import pyrealsense2 as rs


def intrinsics(profile):
    i=profile.as_video_stream_profile().get_intrinsics()
    return {k:getattr(i,k) for k in ("width","height","fx","fy","ppx","ppy","coeffs")} | {"model":str(i.model)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("recording",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--stride",type=int,default=3)
    ap.add_argument("--skip-seconds",type=float,default=2)
    args=ap.parse_args()
    if args.stride<1 or args.skip_seconds<0:
        ap.error("Invalid sampling options")
    args.output.mkdir(parents=True,exist_ok=False)
    for side in ("left","right"):
        (args.output/side).mkdir()
    p=rs.pipeline(); c=rs.config()
    c.enable_device_from_file(str(args.recording.resolve()),repeat_playback=False)
    result={"status":"failed","source_recording":str(args.recording.resolve()),
            "sdk":importlib.metadata.version("pyrealsense2"),"stride":args.stride,
            "skip_seconds":args.skip_seconds,"pairs":[]}
    started=False
    try:
        profile=p.start(c); started=True
        playback=profile.get_device().as_playback(); playback.set_real_time(False)
        leftp=profile.get_stream(rs.stream.infrared,1)
        rightp=profile.get_stream(rs.stream.infrared,2)
        ext=leftp.get_extrinsics_to(rightp)
        result["left"]=intrinsics(leftp); result["right"]=intrinsics(rightp)
        result["left_to_right"]={"rotation_column_major":ext.rotation,"translation_m":ext.translation}
        result["baseline_m"]=-ext.translation[0]
        if result["baseline_m"]<=0 or np.max(np.abs(np.asarray(ext.rotation)-np.eye(3).ravel()))>1e-5:
            raise ValueError("Expected horizontal rectified stereo calibration")
        if any(abs(x)>1e-7 for side in ("left","right") for x in result[side]["coeffs"]):
            raise ValueError("Nonzero distortion needs explicit rectification")
        first=None; seen=set(); selected=0; begin=time.monotonic()
        while time.monotonic()-begin<180:
            try:
                frames=p.wait_for_frames(2000)
            except RuntimeError:
                if playback.current_status()==rs.playback_status.stopped:
                    break
                raise
            left=frames.get_infrared_frame(1); right=frames.get_infrared_frame(2)
            if not left or not right or left.get_frame_number() in seen:
                continue
            seen.add(left.get_frame_number())
            stamp=left.get_timestamp()/1000
            if first is None:
                first=stamp
            if stamp-first<args.skip_seconds:
                continue
            selected+=1
            if (selected-1)%args.stride:
                continue
            delta=(right.get_timestamp()-left.get_timestamp())/1000
            if abs(delta)>0.001:
                raise ValueError(f"Unsynchronized stereo pair: {delta}s")
            row={"index":len(result["pairs"]),"stamp_s":stamp,"elapsed_s":stamp-first,
                 "left_frame":left.get_frame_number(),"right_frame":right.get_frame_number(),
                 "right_minus_left_s":delta,"timestamp_domain":str(left.get_frame_timestamp_domain())}
            for side,frame in (("left",left),("right",right)):
                path=Path(side)/f"{row['index']:06d}.png"
                if not cv2.imwrite(str(args.output/path),np.asanyarray(frame.get_data())):
                    raise OSError(path)
                row[side]=path.as_posix()
            result["pairs"].append(row)
        result["decoded_unique_left_frames"]=len(seen)
        with args.recording.open("rb") as raw:
            result["source_sha256"]=hashlib.file_digest(raw,"sha256").hexdigest()
        expected=json.loads((args.recording.parent/"capture.json").read_text())["raw"]["sha256"]
        if result["source_sha256"]!=expected:
            raise ValueError("Recording SHA-256 differs from capture manifest")
        if result["pairs"]:
            result["status"]="exported"
            result["duration_s"]=result["pairs"][-1]["stamp_s"]-result["pairs"][0]["stamp_s"]
    except Exception as e:
        result["error"]=repr(e)
    finally:
        if started:
            p.stop()
        (args.output/"stereo.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="pairs"},indent=2))
    print(f"pairs={len(result['pairs'])}")
    return int(result["status"]!="exported")


if __name__=="__main__":
    raise SystemExit(main())
