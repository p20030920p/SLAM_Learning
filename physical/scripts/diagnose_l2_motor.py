"""Temporarily stop/restart L2 rotation and compare IMU; always restore scanning.

Uses official USER_CMD_STANDBY_TYPE=2: 1 standby, 0 start. No firmware,
stored work-mode, clock, IP or factory-calibration writes.
"""
import argparse
import collections
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import time

import numpy as np
import serial
from protocol_l2 import Parser, info, user_command


def summarize(rows):
    if len(rows)<2:
        return {"samples":len(rows)}
    a=np.asarray(rows)
    a=a[a[:,2]>=2]
    if len(a)<2:
        return {"samples":len(a)}
    slope,intercept=np.polyfit(a[:,1]-a[0,1],a[:,2]-a[0,2],1)
    return {"samples_after_settling":len(a),
        "host_hz":(len(a)-1)/(a[-1,2]-a[0,2]),
        "host_per_device_second":float(slope),
        "gyro_mean":np.mean(a[:,3:6],axis=0).tolist(),
        "gyro_std":np.std(a[:,3:6],axis=0).tolist(),
        "gyro_norm_p95":float(np.percentile(np.linalg.norm(a[:,3:6],axis=1),95)),
        "accel_mean":np.mean(a[:,6:9],axis=0).tolist(),
        "accel_std":np.std(a[:,6:9],axis=0).tolist()}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--port",default=r"\\?\GLOBALROOT\Device\Serial2")
    ap.add_argument("--seconds",type=float,default=12)
    ap.add_argument("--resume-seconds",type=float,default=45,
                    help="Longer startup verification; observed cloud restart exceeds 12 seconds")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.seconds<4 or args.resume_seconds<20:
        ap.error("At least 4 seconds per stage")
    args.output.mkdir(parents=True,exist_ok=False)
    record={"kind":"temporary_motor_imu_diagnostic","started_at":datetime.now(timezone.utc).isoformat(),
            "commands":[],"stages":{},"scanning_restored":False,"status":"running"}

    def command(port,value):
        packet=user_command(2,value)
        port.write(packet)
        port.flush()
        record["commands"].append({"command":"standby" if value else "start","hex":packet.hex()})

    def capture(port,name,duration=None):
        parser=Parser(); imu=[]; counts=collections.Counter(); acks=[]
        start=time.perf_counter()
        with (args.output/f"{name}.bin").open("wb") as raw:
            while time.perf_counter()-start<(duration or args.seconds):
                chunk=port.read(max(1,min(port.in_waiting,65536)))
                now=time.perf_counter()-start
                raw.write(chunk)
                for kind,packet in parser.feed(chunk):
                    if now>=2:
                        counts[kind]+=1
                    if kind==104:
                        seq,stamp=info(packet)
                        values=struct.unpack_from("<10f",packet,28)
                        imu.append([seq,stamp,now,*values[4:]])
                    elif kind==101:
                        acks.append(list(struct.unpack_from("<4I",packet,12)))
        with (args.output/f"{name}-imu.csv").open("w",newline="") as f:
            w=csv.writer(f); w.writerow(["seq","device_s","host_elapsed_s","wx","wy","wz","ax","ay","az"]); w.writerows(imu)
        result={"packet_counts_after_settling":dict(counts),"crc_errors":parser.crc_errors,"acks":acks,"imu":summarize(imu)}
        record["stages"][name]=result
        print(json.dumps({name:result}),flush=True)
        return result

    try:
        with serial.Serial(args.port,4000000,timeout=0.05) as port:
            port.set_buffer_size(rx_size=1024*1024,tx_size=65536)
            try:
                capture(port,"running")
                command(port,1)
                capture(port,"standby")
            finally:
                command(port,0)
                resumed=capture(port,"resumed",args.resume_seconds)
                record["scanning_restored"]=resumed["packet_counts_after_settling"].get(102,0)>0
        record["status"]="diagnosed" if record["scanning_restored"] else "restore_unverified"
    except Exception as e:
        record.update(status="failed",error=repr(e))
    finally:
        (args.output/"diagnostic.json").write_text(json.dumps(record,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(args.output/"diagnostic.json")
    return int(record["status"]!="diagnosed")


if __name__=="__main__":
    raise SystemExit(main())
