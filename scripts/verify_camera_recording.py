"""Audit DB3 at SDK sensor level, without synchronization filtering or hardware.

Compare every image-message count against SQLite and preserve every live frame
number. Pipeline framesets can omit startup frames and are not a raw-file audit.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import threading
import time
import pyrealsense2 as rs


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("recording",type=Path)
    ap.add_argument("--output",type=Path,help="New evidence path; defaults to playback-v2.json next to recording")
    args=ap.parse_args()
    output=args.output or args.recording.parent/"playback-v2.json"
    if output.exists():
        ap.error("Use a new output path; keep previous checks")
    frames=collections.defaultdict(set)
    counts=collections.Counter()
    record={"status":"failed","observer_version":2,"scope":"Raw sensor callback playback, SQLite image counts and live frame-number coverage; no SLAM evaluation"}
    opened=[]; running=[]; done=threading.Event()
    try:
        with args.recording.open("rb") as f:
            record["raw_sha256"]=hashlib.file_digest(f,"sha256").hexdigest()
        with sqlite3.connect(args.recording.resolve().as_uri()+"?mode=ro",uri=True) as db:
            messages=db.execute("SELECT t.name,count(*) FROM messages m JOIN topics t ON m.topic_id=t.id WHERE t.name LIKE '%/image/data' GROUP BY t.id").fetchall()
        expected_counts={}
        for name,count in messages:
            match=re.search(r"/([^/]+)_(\d+)/image/data$",name)
            if not match:
                raise ValueError(f"Unrecognized image topic {name}")
            expected_counts[f"stream.{match[1].lower()}:{match[2]}"]=count
        required=["stream.color:0","stream.depth:0","stream.infrared:1","stream.infrared:2"]
        if not all(expected_counts.get(k,0)>0 for k in required):
            raise ValueError("Recording does not contain all four requested video streams")
        ctx=rs.context()
        playback=ctx.load_device(str(args.recording.resolve()))
        playback.pause()
        playback.set_real_time(False)
        record["duration_s"]=playback.get_duration().total_seconds()

        def receive(frame):
            profile=frame.get_profile()
            key=f"{profile.stream_type()}:{profile.stream_index()}"
            frames[key].add(frame.get_frame_number()); counts[key]+=1

        def status(state):
            if state==rs.playback_status.stopped:
                done.set()

        playback.set_status_changed_callback(status)
        for sensor in playback.query_sensors():
            sensor.open(sensor.get_stream_profiles()); opened.append(sensor)
        for sensor in opened:
            sensor.start(receive); running.append(sensor)
        playback.resume()
        deadline=time.perf_counter()+120
        while not done.wait(0.25):
            if time.perf_counter()>deadline:
                raise TimeoutError("Raw playback did not reach EOF")
        record["eof_reached"]=True
        record["raw_image_message_counts"]=expected_counts
        record["sdk_frame_callbacks"]=dict(counts)
        record["decoded_unique_frames"]={k:len(v) for k,v in frames.items()}
        same={k:counts[k]==v for k,v in expected_counts.items()}
        record["sdk_counts_match_raw_file"]=same
        complete=all(same.values())
        manifest=args.recording.parent/"capture.json"
        if manifest.exists():
            live=json.loads(manifest.read_text(encoding="utf-8"))
            if record["raw_sha256"]!=live["raw"]["sha256"]:
                raise ValueError("Recording SHA-256 differs from capture")
            live_frames=json.loads((args.recording.parent/"frames.json").read_text(encoding="utf-8"))
            missing={k:sorted({r[0] for r in live_frames[k]}-frames[k]) for k in required}
            record["live_frame_numbers_missing_from_recording"]=missing
            record["raw_minus_live_unique_counts"]={k:len(frames[k])-live["streams"][k]["unique_frames"] for k in required}
            record["coverage_note"]="Recording may include startup frames omitted by live frameset synchronization; every live frame must still exist in raw playback."
            complete=complete and all(not v for v in missing.values())
        record["status"]="verified" if complete else "incomplete"
    except Exception as e:
        record["error"]=repr(e)
    finally:
        errors=[]
        for sensor in reversed(running):
            try:
                sensor.stop()
            except Exception as e:
                errors.append(repr(e))
        for sensor in reversed(opened):
            try:
                sensor.close()
            except Exception as e:
                errors.append(repr(e))
        if errors:
            record.update(status="failed",cleanup_errors=errors)
    output.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(record,indent=2))
    return int(record["status"]!="verified")


if __name__=="__main__":
    raise SystemExit(main())
