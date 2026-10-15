"""Loopback transport between ROS2/Jazzy and the ROS1-era author C++ build.

One connection creates one fresh mapper. The socket carries scan+wheel odometry
only. All author diagnostic stderr is retained separately from protocol stdout.
"""

import json
import os
import socketserver
import subprocess
import shutil
from pathlib import Path

ROOT = Path("/root/srrg-reproduction-ws")


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = (
            str(ROOT / "devel/lib") + ":/opt/ros/noetic/lib:" + env.get("LD_LIBRARY_PATH", "")
        )
        config = json.loads(self.rfile.readline())
        run = Path(config["run"])
        args = [str(ROOT / "srrg_worker")]
        if config.get("graph_merge", False):
            args.append("--graph-merge")
        if config.get("prior"):
            source = Path(config["prior"])
            for p in source.glob("prior*"):
                if p.is_file():
                    shutil.copy2(p, run / p.name)
            args.append("prior.g2o")
        with (run / "logs/srrg-author.log").open("w") as log:
            process = subprocess.Popen(
                args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, env=env, cwd=run
            )
            try:
                for line in self.rfile:
                    process.stdin.write(line)
                    process.stdin.flush()
                    reply = process.stdout.readline()
                    if not reply:
                        raise RuntimeError(f"Author mapper exited {process.poll()}")
                    self.wfile.write(reply)
                    self.wfile.flush()
                    if line.startswith(b"F"):
                        break
            finally:
                process.stdin.close()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=5)


if __name__ == "__main__":

    class Server(socketserver.TCPServer):
        allow_reuse_address = True

    with Server(("127.0.0.1", 19192), Handler) as server:
        print("SRRG native mapper transport listening on loopback:19192", flush=True)
        server.serve_forever()
