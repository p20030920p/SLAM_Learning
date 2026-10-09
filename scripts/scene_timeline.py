"""Cue and annotate an 80-second fixed-sensor tabletop trial.

Run beside start_live.ps1, which alone owns the sensor. Planned cues and operator
keypresses are separate evidence. This tool neither detects events nor stops
capture, and never labels the whole scene as independently verified static.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
EVENTS = ("static", "occlusion", "removal", "move")
FIELDS = ("kind", "label", "planned_s", "elapsed_s", "host_monotonic_ns",
          "host_perf_counter_ns", "utc")


def schedule(event):
    action = {
        "static": "Keep all objects and sensor still.",
        "occlusion": "Place notebook in front of box. Do not move the box.",
        "removal": "Remove box; expose its former space and background.",
        "move": "Move box from mark A to mark B. Cup and notebook stay put.",
    }[event]
    restore = {
        "static": "Continue keeping everything still.",
        "occlusion": "Return notebook to its marked original position.",
        "removal": "Return box to mark A, with its original orientation.",
        "move": "Return box to mark A, with its original orientation.",
    }[event]
    return [(0, "baseline", "Keep all objects and sensor still."),
            (20, "action", action),
            (25, "hold", "Hold current state. Mark actual completion with SPACE."),
            (60, "restore", restore),
            (65, "restored_hold", "Hold restored state. Mark completion with SPACE."),
            (80, "end", "Trial ended. Stop capture in window A with Ctrl+C.")]


def completion_label(event, elapsed):
    if event == "static" or elapsed < 20:
        return "unexpected_completion_key"
    return "action_complete" if elapsed < 60 else "restore_complete"


def drive_timeline(event, emit, announce, read_key, *, clock=time.monotonic,
                   sleep=time.sleep, active=lambda: True):
    """Timing loop with injectable I/O for abort and annotation tests."""
    start = clock()
    pending = iter(schedule(event))
    cue = next(pending)
    while True:
        elapsed = clock() - start
        if not active():
            emit("capture_stopped", "capture_ended_before_timeline", None, elapsed)
            return "aborted"
        while cue is not None and elapsed >= cue[0]:
            planned, label, message = cue
            emit("planned_cue", label, planned, elapsed)
            announce(f"[{planned:02d}s] {message}")
            if label == "end":
                return "timeline_completed"
            cue = next(pending, None)
        key = read_key()
        if key and key.lower() == "q":
            emit("operator_abort", "q", None, elapsed)
            return "aborted"
        if key == " ":
            label = completion_label(event, elapsed)
            emit("operator_key", label, None, elapsed)
            announce(f"MARK {label} at {elapsed:.3f}s (keypress, not detected motion)")
        sleep(0.05)


def resolve_session(root, explicit=None, latest=None):
    if explicit:
        session = Path(explicit).resolve()
    else:
        choices = list((root / "data").glob(f"live-{latest}-*/config.json"))
        if not choices:
            raise ValueError(f"No live {latest} session. Start window A first.")
        session = max(choices, key=lambda p: p.stat().st_mtime_ns).parent.resolve()
    config = json.loads((session / "config.json").read_text(encoding="utf-8-sig"))
    if Path(config["windows_session"]).resolve() != session:
        raise ValueError("Session path differs from its capture configuration")
    if config.get("sensor") not in ("camera", "lidar"):
        raise ValueError("Unsupported sensor")
    if config.get("algorithm") != "sensor" or config.get("session_type") != "stationary":
        raise ValueError("Use Algorithm sensor and SessionType stationary for event capture")
    if not config.get("record"):
        raise ValueError("Window A must include -Record")
    if (session / "live-capture.json").exists() or (session / "capture.json").exists():
        raise ValueError("Capture already ended. Start a new session; never relabel an old one")
    raw = session / ("raw.db3" if config["sensor"] == "camera" else "uart.bin")
    if not raw.exists():
        raise ValueError("Raw capture has not opened. Wait for the live RViz view")
    outputs = ("session-note.json", "trial-scene.json", "events.csv")
    if any((session / name).exists() for name in outputs):
        raise ValueError("Trial annotation already exists; start a new capture, do not overwrite")
    return session, config


def keyboard_key():
    import msvcrt
    return msvcrt.getwch() if msvcrt.kbhit() else None


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def annotate(session, config, event):
    record = {
        "schema_version": 1, "status": "starting", "event": event,
        "sensor": config["sensor"], "session": str(session), "started_at": utc_now(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "objects": {"B01": "box", "C01": "cup", "N01": "paper notebook"},
        "target": "B01", "occluder": "N01" if event == "occlusion" else None,
        "nominal_move_m": 0.30 if event == "move" else None,
        "measured_move_m": None, "reference_uncertainty_m": None,
        "illumination": "not_measured", "planned_duration_s": 80,
        "annotation_policy": "Cues are planned; keys are operator reports, not detected physical events",
        "clock_policy": "Windows host clocks; no exposure/firing synchronization claim",
        "completion_marks": [], "independent_event_verification": False,
    }
    note = {
        "sensor_fixed_declared_by_operator": True,
        "camera_fixed_declared_by_operator": config["sensor"] == "camera",
        "lidar_fixed_declared_by_operator": config["sensor"] == "lidar",
        "declaration_source": "Operator invoked scene_timeline.py --fixed-sensor",
        "event": event, "objects": record["objects"],
        "pure_static_scene_eligible": None,
        "note": "Sensor fixed does not mean all scene objects are static or independently verified",
    }
    for name, data in (("trial-scene.json", record), ("session-note.json", note)):
        with (session / name).open("x", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(f"SESSION: {session}", flush=True)
    print("SPACE = actual action/restore completed; Q = mark trial aborted.", flush=True)
    print("This tool does not stop capture. Keep sensor fixed. Countdown:", flush=True)
    status = "aborted"
    with (session / "events.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()

        def emit(kind, label, planned, elapsed):
            row = dict(kind=kind, label=label, planned_s=planned,
                       elapsed_s=round(elapsed, 6) if elapsed is not None else None,
                       host_monotonic_ns=time.monotonic_ns(),
                       host_perf_counter_ns=time.perf_counter_ns(), utc=utc_now())
            writer.writerow(row)
            stream.flush()
            if kind == "operator_key":
                record["completion_marks"].append(row)

        def active():
            return not (session / "live-capture.json").exists()

        try:
            for remaining in range(5, 0, -1):
                print(remaining, flush=True)
                time.sleep(1)
            record["timeline_start_host_monotonic_ns"] = time.monotonic_ns()
            status = drive_timeline(event, emit, lambda s: print(s, flush=True),
                                    keyboard_key, active=active)
        except KeyboardInterrupt:
            emit("operator_abort", "ctrl_c", None, None)
        except Exception as error:
            record["error"] = repr(error)
            emit("error", type(error).__name__, None, None)
        finally:
            record.update(status=status, finished_at=utc_now())
            note["trial_status"] = status
            if status != "timeline_completed":
                for key in ("sensor_fixed_declared_by_operator",
                            "camera_fixed_declared_by_operator", "lidar_fixed_declared_by_operator"):
                    note[key] = False
                note["note"] = "Aborted trial: fixed-pose export declaration withdrawn; preserve raw data"
            (session / "session-note.json").write_text(
                json.dumps(note, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            marks = {r["label"] for r in record["completion_marks"]}
            record["required_completion_keys_present"] = (
                status == "timeline_completed" and
                (event == "static" or {"action_complete", "restore_complete"} <= marks))
            (session / "trial-scene.json").write_text(
                json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"STATUS: {status}; completion keys: {record['required_completion_keys_present']}")
    print("NOW: go to window A, Ctrl+C, wait for 'Saved session'.")
    return 0 if status == "timeline_completed" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", choices=EVENTS, required=True)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--session", type=Path)
    source.add_argument("--latest", choices=("camera", "lidar"))
    parser.add_argument("--fixed-sensor", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print schedule; no files or devices")
    args = parser.parse_args()
    if args.dry_run:
        for seconds, label, message in schedule(args.event):
            print(f"{seconds:02d}s {label}: {message}")
        return 0
    if os.name != "nt":
        parser.error("Interactive key marking requires Windows PowerShell")
    if not args.fixed_sensor or not (args.session or args.latest):
        parser.error("Require --fixed-sensor and either --session or --latest")
    try:
        session, config = resolve_session(ROOT, args.session, args.latest)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    return annotate(session, config, args.event)


if __name__ == "__main__":
    sys.exit(main())
