"""Aggregate CRC-valid L2 lines for non-inertial, static ICP evaluation.

18 lines is an SDK consumer grouping, not a complete revolution. Uses recorded
host receive time for replay, preserves raw device time and point dt separately.
No motion compensation or IMU fusion is applied.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from protocol_l2 import Parser,info,points


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("session",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--lines",type=int,default=18)
    ap.add_argument("--skip-seconds",type=float,default=2)
    args=ap.parse_args()
    if args.lines<1 or args.skip_seconds<0:
        ap.error("Invalid grouping")
    args.output.mkdir(parents=True,exist_ok=False)
    raw=(args.session/"uart.bin").read_bytes()
    timing=list(csv.DictReader((args.session/"receive.csv").open()))
    if sum(int(r["bytes"]) for r in timing)!=len(raw):
        raise ValueError("Raw/timing byte counts disagree")
    capture=json.loads((args.session/"capture.json").read_text())
    result={"status":"exported","schema_version":2,"mode":"lidar","source_session":str(args.session),
            "source_sha256":hashlib.sha256(raw).hexdigest(),"lines_per_cloud":args.lines,
            "timestamp_policy":"recorded host receive time of last line; not hardware synchronization",
            "deskewing":False,"imu_used":False,"pairs":[]}
    if result["source_sha256"]!=capture["raw_sha256"]:
        raise ValueError("UART SHA-256 differs from capture manifest")
    parser=Parser(); offset=0; lines=[]; line_times=[]; seqs=[]
    epoch=__import__("datetime").datetime.fromisoformat(capture["started_at"]).timestamp()
    for row in timing:
        n=int(row["bytes"]); chunk=raw[offset:offset+n]; offset+=n
        host=float(row["host_receive_elapsed_s"])
        for kind,packet in parser.feed(chunk):
            if kind!=102 or host<args.skip_seconds:
                continue
            seq,stamp=info(packet); p=points(packet)
            lines.append(p); line_times.append([stamp,host,struct.unpack_from("<f",packet,124)[0]])
            seqs.append(seq)
            if len(lines)<args.lines:
                continue
            index=len(result["pairs"]); path=f"{index:06d}.npz"
            cloud=np.concatenate(lines)
            xyzi=np.column_stack([cloud[k] for k in ("x","y","z","intensity")]).astype("<f4")
            np.savez_compressed(args.output/path,xyzi=xyzi,point_dt=cloud["time"],
                                ring=cloud["ring"],line_point_counts=np.asarray([len(p) for p in lines]),
                                line_timing=np.asarray(line_times),line_seq=np.asarray(seqs))
            result["pairs"].append({"index":index,"cloud":path,"points":len(cloud),
                                    "stamp_s":epoch+host,"elapsed_s":host,"device_end_s":stamp,
                                    "host_line_span_s":line_times[-1][1]-line_times[0][1]})
            lines=[]; line_times=[]; seqs=[]
    result.update(crc_errors=parser.crc_errors,packet_counts=dict(parser.counts),
                  incomplete_final_lines=len(lines),duration_s=result["pairs"][-1]["elapsed_s"]-result["pairs"][0]["elapsed_s"])
    (args.output/"clouds.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="pairs"},indent=2))
    print(f"clouds={len(result['pairs'])}")


if __name__=="__main__":
    main()
