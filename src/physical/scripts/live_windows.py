"""Own the physical Windows device and relay lossless samples to local WSL."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import queue
import socket
import struct
import threading
import time
import traceback
import numpy as np
from live_transport import send


def camera(config, connection, record):
    import pyrealsense2 as rs
    pipeline = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    for index in (1, 2):
        cfg.enable_stream(rs.stream.infrared, index, 640, 480, rs.format.y8, 30)
    if config["record"]:
        cfg.enable_record_to_file(str(Path(config["windows_session"]) / "raw.db3"))
    started = False
    changed = []
    frames_seen = {}
    start = time.monotonic()
    try:
        profile = pipeline.start(cfg)
        started = True
        device = profile.get_device()
        record["device"] = {key: device.get_info(option) for key, option in (
            ("name", rs.camera_info.name), ("serial", rs.camera_info.serial_number),
            ("usb", rs.camera_info.usb_type_descriptor), ("firmware", rs.camera_info.firmware_version))}
        depth_sensor = device.first_depth_sensor()
        record["depth_scale_m"] = depth_sensor.get_depth_scale()
        record["emitter_before"] = depth_sensor.get_option(rs.option.emitter_enabled)
        if config["emitter"] != "default":
            changed.append((rs.option.emitter_enabled, record["emitter_before"]))
            depth_sensor.set_option(rs.option.emitter_enabled, int(config["emitter"] == "on"))
        record["emitter_during"] = depth_sensor.get_option(rs.option.emitter_enabled)
        align = rs.align(rs.stream.color)
        left = profile.get_stream(rs.stream.infrared, 1)
        right = profile.get_stream(rs.stream.infrared, 2)
        color = profile.get_stream(rs.stream.color)
        def intrinsics(p):
            i = p.as_video_stream_profile().get_intrinsics()
            if max(abs(v) for v in i.coeffs) > 1e-7:
                raise ValueError("Nonzero distortion needs explicit rectification before this bridge")
            return {key: getattr(i, key) for key in ("width", "height", "fx", "fy", "ppx", "ppy")}
        ext = left.get_extrinsics_to(color)
        calibration = dict(left=intrinsics(left), right=intrinsics(right), color=intrinsics(color),
                           baseline_m=-left.get_extrinsics_to(right).translation[0],
                           sdk_left_to_color=dict(rotation_column_major=ext.rotation, translation_m=ext.translation))
        if calibration["baseline_m"] <= 0:
            raise ValueError("Expected positive rectified stereo baseline")
        record["calibration"] = calibration
        record["timestamp_policy"] = "Host frameset arrival; native per-stream timestamps/skews retained; not hardware synchronization"
        start = time.monotonic()
        record["started_at"] = datetime.now(timezone.utc).isoformat()
        previous_send = 0
        record["framesets_acquired"] = 0
        record["frames_sent"] = 0
        record["stereo_skew_rejected"] = 0
        record["stereo_skew_rejected_first_ms"] = []
        while not config["seconds"] or time.monotonic() - start < config["seconds"]:
            frames = pipeline.wait_for_frames(5000)
            record["framesets_acquired"] += 1
            for frame in frames if config["record"] else ():
                p = frame.get_profile()
                key = f"{p.stream_type()}:{p.stream_index()}"
                frames_seen.setdefault(key, []).append([frame.get_frame_number(), frame.get_timestamp(),
                                                        time.monotonic(), str(frame.get_frame_timestamp_domain())])
            now = time.monotonic()
            if now - previous_send < 1 / config["fps"]:
                continue
            l, r = frames.get_infrared_frame(1), frames.get_infrared_frame(2)
            c, d = frames.get_color_frame(), frames.get_depth_frame()
            if not all((l, r, c, d)):
                continue
            if abs(r.get_timestamp() - l.get_timestamp()) > 1:
                record["stereo_skew_rejected"] += 1
                if len(record["stereo_skew_rejected_first_ms"]) < 10:
                    record["stereo_skew_rejected_first_ms"].append(r.get_timestamp() - l.get_timestamp())
                continue
            aligned = align.process(frames)
            depth = np.asanyarray(aligned.get_depth_frame().get_data())
            depth_mm = np.clip(np.rint(depth.astype(float) * record["depth_scale_m"] * 1000),
                               0, 65535).astype("<u2")
            arrays = dict(color=np.asanyarray(c.get_data()).copy(),
                          depth=depth_mm, left=np.asanyarray(l.get_data()).copy(),
                          right=np.asanyarray(r.get_data()).copy())
            metadata = dict(kind="camera", stamp_ns=time.time_ns(), calibration=calibration,
                            depth_unit_m=0.001, depth_aligned_to="color",
                            device_timestamps_ms={key: f.get_timestamp() for key, f in
                                                  (("left", l), ("right", r), ("color", c), ("depth", d))},
                            sequence={key: f.get_frame_number() for key, f in
                                      (("left", l), ("right", r), ("color", c), ("depth", d))})
            send(connection, metadata, arrays)
            previous_send = now
            record["frames_sent"] += 1
            if record["frames_sent"] % 30 == 0:
                print(f"LIVE camera: {record['frames_sent']} sets, sampling <= {config['fps']} Hz", flush=True)
    finally:
        record["elapsed_seconds"] = time.monotonic() - start
        if started:
            pipeline.stop()
        if changed:
            for option, value in reversed(changed):
                depth_sensor.set_option(option, value)
            record["temporary_options_restored"] = all(depth_sensor.get_option(o) == v for o, v in changed)
        else:
            record["temporary_options_restored"] = True
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        if config["record"] and started:
            session = Path(config["windows_session"])
            raw = session / "raw.db3"
            with raw.open("rb") as raw_stream:
                record["raw"] = dict(bytes=raw.stat().st_size,
                                     sha256=hashlib.file_digest(raw_stream, "sha256").hexdigest())
            record["streams"] = {key: {"unique_frames": len({row[0] for row in rows})}
                                 for key, rows in frames_seen.items()}
            (session / "frames.json").write_text(json.dumps(frames_seen) + "\n")


def lidar(config, connection, record):
    import serial
    from protocol_l2 import Parser, info, points, version_request
    session = Path(config["windows_session"])
    parser = Parser()
    stop = threading.Event()
    chunks = queue.Queue(maxsize=512)
    errors = []
    raw = (session / "uart.bin").open("wb") if config["record"] else None
    timing = (session / "receive.csv").open("w", newline="") if config["record"] else None
    csv_writer = csv.writer(timing) if timing else None
    if csv_writer:
        csv_writer.writerow(["host_receive_elapsed_s", "bytes"])
    start = time.monotonic()
    samples = {102: [], 104: []}
    record["clouds_sent"] = 0
    record["imu_sent"] = 0
    record["port"] = config["serial_port"]
    record["decoder"] = "Python SDK-based conversion with float angle accumulation; not native SDK binary"
    record["timestamp_policy"] = "Host UART receive time; raw device and per-point times preserved; no IMU fusion or deskew"
    try:
        with serial.Serial(config["serial_port"], 4000000, timeout=0.03) as port:
            record["started_at"] = datetime.now(timezone.utc).isoformat()
            port.set_buffer_size(rx_size=1024 * 1024, tx_size=65536)
            port.write(version_request())
            def reader():
                try:
                    while not stop.is_set():
                        chunk = port.read(max(1, min(port.in_waiting, 65536)))
                        host_ns = time.time_ns()
                        elapsed = time.monotonic() - start
                        if chunk:
                            if raw:
                                raw.write(chunk)
                                csv_writer.writerow([elapsed, len(chunk)])
                            chunks.put((host_ns, elapsed, chunk), timeout=1)
                except Exception as error:
                    errors.append(repr(error))
                    stop.set()
            thread = threading.Thread(target=reader, daemon=True)
            thread.start()
            lines, line_stamps = [], []
            try:
                while not config["seconds"] or time.monotonic() - start < config["seconds"]:
                    if errors:
                        raise RuntimeError("UART reader: " + "; ".join(errors))
                    host_ns, elapsed, chunk = chunks.get(timeout=5)
                    for kind, packet in parser.feed(chunk):
                        if kind in samples:
                            seq, device_s = info(packet)
                            samples[kind].append((seq, device_s, elapsed))
                        if kind == 102:
                            cloud = points(packet, sdk_float_angles=True)
                            lines.append(cloud)
                            line_stamps.append(device_s)
                            if len(lines) < config["lines"]:
                                continue
                            cloud = np.concatenate(lines)
                            xyzi = np.column_stack([cloud[k] for k in ("x", "y", "z", "intensity")]).astype("<f4")
                            send(connection, dict(kind="lidar", stamp_ns=host_ns, lines=len(lines),
                                                  device_first_s=line_stamps[0], device_last_s=line_stamps[-1],
                                                  crc_errors=parser.crc_errors),
                                 dict(xyzi=xyzi, point_dt=cloud["time"].copy(), ring=cloud["ring"].copy()))
                            lines, line_stamps = [], []
                            record["clouds_sent"] += 1
                            if record["clouds_sent"] % 20 == 0:
                                print(f"LIVE L2: {record['clouds_sent']} clouds, CRC rejects={parser.crc_errors}", flush=True)
                        elif kind == 104:
                            values = struct.unpack_from("<10f", packet, 28)
                            send(connection, dict(kind="imu_raw", stamp_ns=host_ns, device_s=device_s,
                                                  values=values, unit_status="Raw SDK convention; not calibrated for LIO"))
                            record["imu_sent"] += 1
                        elif kind == 105:
                            record["device"] = dict(name=packet[20:44].split(b"\0")[0].decode(errors="replace"),
                                                    firmware=".".join(map(str, packet[16:20])),
                                                    hardware=".".join(map(str, packet[12:16])))
            finally:
                stop.set()
                thread.join(timeout=2)
    finally:
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        if raw:
            raw.close()
            timing.close()
            with (session / "uart.bin").open("rb") as raw_stream:
                record["raw_sha256"] = hashlib.file_digest(raw_stream, "sha256").hexdigest()
        record.update(elapsed_seconds=time.monotonic() - start, crc_errors=parser.crc_errors,
                      packet_counts=dict(parser.counts), discarded_bytes=parser.discarded_bytes)
        for kind, rows in samples.items():
            if len(rows) < 2:
                continue
            a = np.asarray(rows)
            sequence_delta = np.diff(a[:, 0]).astype(int) % 1024
            slope = np.polyfit(a[:, 1] - a[0, 1], a[:, 2] - a[0, 2], 1)[0]
            record[str(kind)] = dict(count=len(a), missing=int(np.maximum(sequence_delta - 1, 0).sum()),
                                     duplicates=int((sequence_delta == 0).sum()),
                                     host_hz=float((len(a) - 1) / (a[-1, 2] - a[0, 2])),
                                     host_seconds_per_device_second=float(slope))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    args = ap.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    record = dict(started_at=datetime.now(timezone.utc).isoformat(), sensor=config["sensor"],
                  status="starting", scope="Live receipt; preview is not precision acceptance")
    connection = None
    try:
        deadline = time.monotonic() + 25
        while True:
            try:
                connection = socket.create_connection(("127.0.0.1", config["port"]), timeout=2)
                connection.settimeout(10)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.3)
        send(connection, dict(kind="hello", sensor=config["sensor"], token=config["token"]))
        (camera if config["sensor"] == "camera" else lidar)(config, connection, record)
        record["status"] = "streamed"
    except KeyboardInterrupt:
        record["status"] = "stopped_by_operator"
    except Exception as error:
        record.update(status="failed", error=repr(error), traceback=traceback.format_exc())
    finally:
        if connection:
            connection.close()
        (Path(config["windows_session"]) / "live-capture.json").write_text(
            json.dumps(record, indent=2, allow_nan=False) + "\n")
        if config["record"]:
            (Path(config["windows_session"]) / "capture.json").write_text(
                json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: record[key] for key in ("sensor", "status", "frames_sent", "clouds_sent", "crc_errors", "error") if key in record}, indent=2))
    return int(record["status"] == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
