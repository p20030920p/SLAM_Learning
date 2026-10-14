"""Stop only processes carrying this exact presentation session ownership tag."""

import argparse
import os
import signal
import time
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--run", required=True)
args = parser.parse_args()
tag = ("PRESENTATION_RUN=" + args.run).encode()
excluded = {os.getpid(), os.getppid()}
pids = []
for directory in Path("/proc").iterdir():
    if not directory.name.isdigit() or int(directory.name) in excluded:
        continue
    try:
        if tag in (directory / "environ").read_bytes().split(b"\0"):
            pids.append(int(directory.name))
    except (PermissionError, FileNotFoundError, ProcessLookupError):
        continue
for sig in (signal.SIGTERM, signal.SIGKILL):
    for pid in pids:
        try:
            if tag in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
                os.kill(pid, sig)
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            pass
    if sig == signal.SIGTERM:
        time.sleep(2)
print(f"Stopped {len(pids)} processes owned by {args.run}")
