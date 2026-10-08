"""Linux: sample actual packets across a session against unmodified SDK utilities."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from protocol_l2 import Parser,points,POINT_DTYPE


ap=argparse.ArgumentParser()
ap.add_argument("raw",type=Path)
ap.add_argument("--binary",type=Path,required=True)
ap.add_argument("--output",type=Path,required=True)
ap.add_argument("--sdk-float-angles",action="store_true")
args=ap.parse_args()
raw=args.raw.read_bytes(); parser=Parser()
packets=[packet for kind,packet in parser.feed(raw) if kind==102]
indices=np.unique(np.linspace(0,len(packets)-1,min(20,len(packets))).astype(int))
result={"source_sha256":hashlib.sha256(raw).hexdigest(),"official_sdk_commit":"0e3c51f512e6b8ff60b8c32f160b412cb48445c2",
        "sdk_float_angle_control":args.sdk_float_angles,
        "sample_policy":"20 evenly spaced CRC-valid line packets over entire session",
        "xyz_tolerance_m":0.0001,"point_dt_tolerance_s":1e-7,"samples":[]}
with tempfile.TemporaryDirectory(prefix="physical-sdk-check-") as directory:
    packetfile=Path(directory)/"packet.bin"; output=Path(directory)/"points.bin"
    for index in indices:
        packet=packets[index]; packetfile.write_bytes(packet)
        subprocess.run([str(args.binary.resolve()),str(packetfile),str(output)],capture_output=True,check=True)
        official=np.fromfile(output,dtype=POINT_DTYPE); python=points(packet,sdk_float_angles=args.sdk_float_angles)
        equal_count=len(official)==len(python)
        delta=max(float(np.abs(official[k]-python[k]).max()) for k in ("x","y","z")) if equal_count and len(python) else None
        dt=float(np.abs(official["time"]-python["time"]).max()) if equal_count and len(python) else None
        item={"line_index":int(index),"point_count":len(python),"point_count_equal":equal_count,
              "xyz_max_component_error_m":delta,"point_dt_max_error_s":dt,
              "ring_equal":bool(equal_count and np.array_equal(official["ring"],python["ring"])),
              "intensity_equal":bool(equal_count and np.array_equal(official["intensity"],python["intensity"]))}
        item["pass"]=bool(equal_count and delta is not None and delta<=result["xyz_tolerance_m"] and
                          dt<=result["point_dt_tolerance_s"] and item["ring_equal"] and item["intensity_equal"])
        result["samples"].append(item)
result["pass"]=bool(result["samples"] and all(s["pass"] for s in result["samples"]))
args.output.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"samples":len(indices),"pass":result["pass"],
                  "xyz_max_component_error_m":max(s["xyz_max_component_error_m"] for s in result["samples"])},indent=2))
raise SystemExit(int(not result["pass"]))
