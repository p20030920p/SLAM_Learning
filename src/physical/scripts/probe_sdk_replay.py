"""Linux-only offline replay through official SDK2 compiled binary."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import tty

ap=argparse.ArgumentParser()
ap.add_argument("binary")
ap.add_argument("raw",type=Path)
ap.add_argument("clock",nargs="?",default="device",choices=("device","system"))
ap.add_argument("--receive-timing",type=Path)
ap.add_argument("--output",type=Path)
args=ap.parse_args()
master,slave=os.openpty()
tty.setraw(slave)
child=subprocess.Popen([args.binary,os.ttyname(slave),*(["system"] if args.clock=="system" else [])],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
raw=args.raw.read_bytes()
timing=list(csv.DictReader(args.receive_timing.open())) if args.receive_timing else None
if timing and sum(int(r["bytes"]) for r in timing)!=len(raw):
    child.kill()
    raise ValueError("Receive log and raw byte count disagree")
progress={"fed_bytes":0,"fed_host_span_s":None}

def feed():
    try:
        start=time.monotonic(); offset=0
        chunks=timing or [{"bytes":min(4096,len(raw)-i)} for i in range(0,len(raw),4096)]
        for row in chunks:
            if child.poll() is not None:
                break
            if timing:
                elapsed=float(row["host_receive_elapsed_s"])
                due=start+elapsed
                delay=due-time.monotonic()
                if delay>0:
                    time.sleep(delay)
                progress["fed_host_span_s"]=elapsed
            size=int(row["bytes"])
            chunk=memoryview(raw[offset:offset+size]); offset+=size
            while chunk:
                n=os.write(master,chunk)
                chunk=chunk[n:]
                progress["fed_bytes"]+=n
    except OSError:
        pass

threading.Thread(target=feed,daemon=True).start()
try:
    out,_=child.communicate(timeout=12)
except subprocess.TimeoutExpired:
    child.kill()
    out,_=child.communicate()
finally:
    os.close(master)
    os.close(slave)
output=out.decode(errors="replace")
print(output)
if args.output:
    result={"raw":str(args.raw),"clock":args.clock,"paced_to_original_receive_timing":bool(timing),
            "exit_code":child.returncode,"native_output":output,**progress,
            "limitation":"Host parsing timestamp, not hardware sync; raw clock remains unchanged"}
    args.output.write_text(json.dumps(result,indent=2)+"\n")
raise SystemExit(child.returncode)
