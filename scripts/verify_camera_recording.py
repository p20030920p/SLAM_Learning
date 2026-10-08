"""Decode recorded DB3 with RealSense SDK without opening the physical camera."""
import argparse
import collections
import json
from pathlib import Path
import time
import pyrealsense2 as rs


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("recording",type=Path)
    args=ap.parse_args()
    p=rs.pipeline()
    c=rs.config()
    c.enable_device_from_file(str(args.recording.resolve()),repeat_playback=False)
    frames=collections.defaultdict(set)
    record={"status":"failed"}
    started=False
    try:
        profile=p.start(c)
        started=True
        playback=profile.get_device().as_playback()
        playback.set_real_time(False)
        record["duration_s"]=playback.get_duration().total_seconds()
        start=time.perf_counter()
        while time.perf_counter()-start<120:
            try:
                bundle=p.wait_for_frames(2000)
            except RuntimeError:
                if playback.current_status()==rs.playback_status.stopped:
                    break
                raise
            for f in bundle:
                profile=f.get_profile()
                frames[f"{profile.stream_type()}:{profile.stream_index()}"].add(f.get_frame_number())
        record["decoded_unique_frames"]={k:len(v) for k,v in frames.items()}
        expected=["stream.color:0","stream.depth:0","stream.infrared:1","stream.infrared:2"]
        complete=all(len(frames[k])>0 for k in expected)
        manifest=args.recording.parent/"capture.json"
        if manifest.exists():
            live=json.loads(manifest.read_text(encoding="utf-8"))
            same={k:len(frames[k])==v["unique_frames"] for k,v in live.get("streams",{}).items()}
            record["counts_match_capture"]=same
            complete=complete and bool(same) and all(same.values())
        record["status"]="verified" if complete else "incomplete"
        record["scope"]="Full non-realtime SDK playback of four video streams. No SLAM evaluation."
    except Exception as e:
        record["error"]=repr(e)
    finally:
        if started:
            p.stop()
    (args.recording.parent/"playback.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(record,indent=2))
    return int(record["status"]!="verified")


if __name__=="__main__":
    raise SystemExit(main())
