"""Recheck a saved UART capture; preserve the original acquisition record."""
import argparse
import collections
import json
from pathlib import Path

import numpy as np
from protocol_l2 import Parser, info, points


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("capture",type=Path)
    args=ap.parse_args()
    parser=Parser()
    samples=collections.defaultdict(list)
    point_count=0
    with (args.capture/"uart.bin").open("rb") as f:
        while chunk:=f.read(65536):
            for kind,packet in parser.feed(chunk):
                if kind in (102,104):
                    samples[kind].append(info(packet))
                if kind==102:
                    point_count+=len(points(packet))
    result={"status":"received" if parser.counts[102] and parser.counts[104] else "incomplete",
            "packet_counts":dict(parser.counts),"crc_errors":parser.crc_errors,"valid_points":point_count,
            "crc_reject_fraction":parser.crc_errors/(sum(parser.counts.values())+parser.crc_errors) if sum(parser.counts.values())+parser.crc_errors else None,
            "clock_policy":"report raw timing discrepancy; no timestamp scaling applied"}
    for kind,rows in samples.items():
        a=np.asarray(rows)
        delta=np.diff(a[:,0]).astype(np.int64)%1024
        row={"sequence_modulus":1024,"sequence_wraps":int((np.diff(a[:,0])<0).sum()),
             "missing_packets":int(np.maximum(delta-1,0).sum()),"duplicates":int((delta==0).sum()),
             "raw_sensor_hz":(len(a)-1)/(a[-1,1]-a[0,1]),
             "timestamp_non_increasing":int((np.diff(a[:,1])<=0).sum())}
        csv_path=args.capture/f"packets-{kind}.csv"
        if csv_path.exists():
            delivered=np.loadtxt(csv_path,delimiter=",",skiprows=1)
            x=delivered[:,1]-delivered[0,1]
            y=delivered[:,2]-delivered[0,2]
            slope,intercept=np.polyfit(x,y,1)
            row.update(host_receive_hz=(len(y)-1)/(y[-1]-y[0]),
                       host_per_device_second=float(slope),
                       residual_p95_ms=float(np.percentile(np.abs(y-(slope*x+intercept)),95)*1000),
                       ready_for_inertial_odometry=bool(abs(slope-1)<0.001))
        result[str(kind)]=row
    out=args.capture/"audit.json"
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(out)
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
