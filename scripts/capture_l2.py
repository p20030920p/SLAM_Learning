"""Capture physical L2 UART with CRC checks; no mode/reset/clock commands."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import struct
import time
import queue
import threading
from datetime import datetime, timezone

import cv2
import numpy as np
import serial

from protocol_l2 import Parser, info, points, version_request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=r"\\?\GLOBALROOT\Device\Serial2")
    ap.add_argument("--baud", type=int, default=4000000)
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--query-version", action="store_true")
    args = ap.parse_args()
    if args.seconds <= 0:
        ap.error("seconds must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    record = {"sensor": "Unitree L2", "started_at": datetime.now(timezone.utc).isoformat(),
              "port": args.port, "baud": args.baud, "status": "running",
              "evaluation_completed": False, "sdk_reference_commit": "0e3c51f512e6b8ff60b8c32f160b412cb48445c2",
              "clock": "device uptime; host receive time is separately recorded; not cross-sensor synchronized"}
    parser = Parser()
    stats = collections.defaultdict(list)
    preview_clouds = collections.deque(maxlen=100)
    imu = []
    receive = []
    start = time.perf_counter()
    next_preview = 0
    writer = cv2.VideoWriter(str(args.output/"preview.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10, (1000, 560))
    if not writer.isOpened():
        raise RuntimeError("Cannot open video writer")
    total_bytes = 0
    valid_points = 0
    try:
        with serial.Serial(args.port, args.baud, timeout=0.05) as port, (args.output/"uart.bin").open("wb") as raw:
            try:
                port.set_buffer_size(rx_size=1024*1024, tx_size=65536)
                record["requested_driver_rx_buffer_bytes"]=1024*1024
            except (AttributeError, OSError) as e:
                record["driver_buffer_note"]=repr(e)
            if args.query_version:
                request = version_request()
                port.write(request)
                record["transmitted"] = {"purpose": "read device version only", "hex": request.hex()}
            start = time.perf_counter()
            chunks=queue.Queue()
            read_errors=[]
            stop_reader=threading.Event()
            def read_uart():
                try:
                    while not stop_reader.is_set() and time.perf_counter()-start<args.seconds:
                        chunk=port.read(max(1,min(port.in_waiting,65536)))
                        now=time.perf_counter()-start
                        if chunk:
                            raw.write(chunk)
                            chunks.put((now,chunk))
                except Exception as e:
                    read_errors.append(repr(e))
                finally:
                    chunks.put(None)
            reader=threading.Thread(target=read_uart,name="l2-uart-reader",daemon=True)
            reader.start()
            while True:
                item=chunks.get(timeout=10)
                if item is None:
                    break
                now,chunk=item
                total_bytes += len(chunk)
                receive.append([now, len(chunk)])
                for kind, packet in parser.feed(chunk):
                    if kind in (102, 104):
                        seq, stamp = info(packet)
                        stats[kind].append((seq, stamp, now))
                    if kind == 102:
                        cloud = points(packet)
                        valid_points += len(cloud)
                        preview_clouds.append((stamp, cloud))
                        if not (args.output/"first_point_packet.bin").exists():
                            (args.output/"first_point_packet.bin").write_bytes(packet)
                            np.save(args.output/"first_points.npy", cloud)
                        if len(stats[102]) % 100 == 0:
                            record["last_inside_state"] = dict(zip(
                                ["sys_rotation_period", "com_rotation_period", "dirty_index", "packet_lost_up", "packet_lost_down", "apd_temperature", "apd_voltage", "laser_voltage", "imu_temperature"],
                                struct.unpack_from("<II7f", packet, 28)))
                    elif kind == 104:
                        imu.append([seq, stamp, now, *struct.unpack_from("<10f", packet, 28)])
                    elif kind == 105:
                        record["device_version"] = {"hardware": ".".join(map(str, packet[12:16])),
                            "firmware": ".".join(map(str, packet[16:20])),
                            "name": packet[20:44].split(b"\0")[0].decode("ascii", errors="replace"),
                            "date": packet[44:52].split(b"\0")[0].decode("ascii", errors="replace")}
                while now >= next_preview:
                    canvas = np.full((560, 1000, 3), 18, dtype=np.uint8)
                    if preview_clouds:
                        latest = preview_clouds[-1][0]
                        recent = [p for t,p in preview_clouds if latest-t <= 0.15]
                        cloud = np.concatenate(recent)
                        xyz = np.column_stack([cloud[k] for k in ("x", "y", "z")])
                        for origin, axes, label in (([250,300], (0,1), "TOP: X/Y, +/-5m"), ([750,400], (0,2), "SIDE: X/Z, +/-5m")):
                            px = np.rint(origin[0] + xyz[:,axes[0]]*45).astype(int)
                            py = np.rint(origin[1] - xyz[:,axes[1]]*45).astype(int)
                            ok = (px >= origin[0]-225) & (px < origin[0]+225) & (py >= 75) & (py < 530)
                            canvas[py[ok],px[ok]] = (80,210,100)
                            cv2.putText(canvas,label,(origin[0]-220,70),0,0.6,(230,230,230),1)
                    cv2.putText(canvas,f"L2 LIVE UART CAPTURE {next_preview:.1f}s | RAW SENSOR, NO SLAM",(20,30),0,0.65,(240,240,240),1)
                    writer.write(canvas)
                    if next_preview >= 2 and not (args.output/"preview.png").exists():
                        cv2.imwrite(str(args.output/"preview.png"),canvas)
                    next_preview += 0.1
            reader.join(timeout=2)
            if read_errors:
                raise RuntimeError("UART reader: "+"; ".join(read_errors))
            record["status"] = "received" if parser.counts[102] and parser.counts[104] else "incomplete"
    except Exception as e:
        record.update(status="failed", error=repr(e))
    finally:
        if "stop_reader" in locals():
            stop_reader.set()
            reader.join(timeout=2)
        record["elapsed_seconds"] = time.perf_counter()-start
        writer.release()
        record.update(raw_bytes=total_bytes, valid_points=valid_points, crc_errors=parser.crc_errors,
                      discarded_bytes=parser.discarded_bytes, trailing_bytes=len(parser.buffer),
                      packet_counts=dict(parser.counts), packet_sizes=dict(parser.sizes))
        for kind, samples in stats.items():
            a = np.asarray(samples)
            delta = np.diff(a[:,1])
            # This firmware wraps both packet counters from 1023 to 0.
            seq_delta = (np.diff(a[:,0]).astype(np.int64)) % 1024
            slope, intercept = np.polyfit(a[:,1]-a[0,1], a[:,2], 1) if len(a)>1 else (float("nan"),float("nan"))
            residual = a[:,2] - (slope*(a[:,1]-a[0,1])+intercept)
            record[str(kind)] = {"count":len(a), "sensor_hz":(len(a)-1)/(a[-1,1]-a[0,1]) if len(a)>1 and a[-1,1]>a[0,1] else None,
                "sequence_missing":int(np.maximum(seq_delta-1,0).sum()), "sequence_duplicates":int((seq_delta==0).sum()),
                "timestamp_non_increasing":int((delta<=0).sum()), "max_sensor_gap_s":float(delta.max()) if len(delta) else None,
                "host_hz":(len(a)-1)/(a[-1,2]-a[0,2]) if len(a)>1 and a[-1,2]>a[0,2] else None,
                "sequence_modulus":1024,"clock_host_seconds_per_device_second":float(slope) if len(a)>1 else None,
                "clock_affine_residual_p95_s":float(np.percentile(np.abs(residual),95)) if len(a)>1 else None}
            with (args.output/f"packets-{kind}.csv").open("w",newline="") as f:
                w=csv.writer(f); w.writerow(["seq","device_timestamp_s","host_receive_elapsed_s"]); w.writerows(samples)
        if imu:
            a=np.asarray(imu)
            record["imu_summary"]={"acceleration_norm_median":float(np.median(np.linalg.norm(a[:,10:13],axis=1))),
                "gyro_norm_median":float(np.median(np.linalg.norm(a[:,7:10],axis=1))),
                "quaternion_norm_median":float(np.median(np.linalg.norm(a[:,3:7],axis=1)))}
            with (args.output/"imu.csv").open("w",newline="") as f:
                w=csv.writer(f); w.writerow(["seq","device_timestamp_s","host_receive_elapsed_s","qx","qy","qz","qw","wx","wy","wz","ax","ay","az"]); w.writerows(imu)
        with (args.output/"receive.csv").open("w",newline="") as f:
            w=csv.writer(f); w.writerow(["host_receive_elapsed_s","bytes"]); w.writerows(receive)
        p=args.output/"uart.bin"
        if p.exists():
            with p.open("rb") as f:
                record["raw_sha256"]=hashlib.file_digest(f,"sha256").hexdigest()
        (args.output/"capture.json").write_text(json.dumps(record,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(record,indent=2))
    return int(record["status"] != "received")


if __name__ == "__main__":
    raise SystemExit(main())
