"""Aggregate CRC-valid L2 lines for non-inertial, static ICP evaluation.

18 lines is an SDK consumer grouping, not a complete revolution. Uses recorded
host receive time for replay, preserves raw device time and point dt separately.
No motion compensation or IMU fusion is applied.
"""
import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

import numpy as np
from protocol_l2 import Parser,info,points,POINT_DTYPE


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("session",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--lines",type=int,default=18)
    ap.add_argument("--skip-seconds",type=float,default=2)
    ap.add_argument("--sdk-decoder",type=Path,
                    help="Linux compiled decode_sdk_lines binary; uses unchanged official XYZ conversion")
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
    official_lines=None
    result["decoder"]="python vectorized double angles (original baseline)"
    if args.sdk_decoder:
        decoded=Parser()
        packets=[p for kind,p in decoded.feed(raw) if kind==102]
        with tempfile.TemporaryDirectory(prefix="physical-sdk-lines-") as temporary:
            packet_path=Path(temporary)/"packets.bin"; point_path=Path(temporary)/"points.bin"
            packet_path.write_bytes(b"".join(packets))
            run=subprocess.run([str(args.sdk_decoder.resolve()),str(packet_path),str(point_path)],
                               capture_output=True,text=True,check=True)
            result["sdk_decode_counts"]=json.loads(run.stdout)
            blob=point_path.read_bytes()
        if result["sdk_decode_counts"]["point_bytes"]!=POINT_DTYPE.itemsize:
            raise ValueError("Official decoder point layout differs")
        official_lines=[]; cursor=0
        while cursor<len(blob):
            count=struct.unpack_from("<I",blob,cursor)[0]; cursor+=4
            if count>300 or cursor+count*POINT_DTYPE.itemsize>len(blob):
                raise ValueError("Official decoder line length invalid")
            official_lines.append(np.frombuffer(blob,dtype=POINT_DTYPE,count=count,offset=cursor))
            cursor+=count*POINT_DTYPE.itemsize
        if cursor!=len(blob) or len(official_lines)!=len(packets):
            raise ValueError("Official decoder output incomplete")
        result["decoder"]="official Unitree SDK2 parseFromPacketToPointCloud (unchanged)"
        result["sdk_commit"]="0e3c51f512e6b8ff60b8c32f160b412cb48445c2"
        result["sdk_decoder_binary_sha256"]=hashlib.sha256(args.sdk_decoder.read_bytes()).hexdigest()
    point_index=0
    parser=Parser(); offset=0; lines=[]; line_times=[]; seqs=[]
    epoch=datetime.fromisoformat(capture["started_at"]).timestamp()
    for row in timing:
        n=int(row["bytes"]); chunk=raw[offset:offset+n]; offset+=n
        host=float(row["host_receive_elapsed_s"])
        for kind,packet in parser.feed(chunk):
            if kind!=102:
                continue
            p=official_lines[point_index] if official_lines is not None else points(packet)
            point_index+=1
            if host<args.skip_seconds:
                continue
            seq,stamp=info(packet)
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
