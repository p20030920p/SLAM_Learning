"""Linux-only offline replay through official SDK2 compiled binary."""
import os
from pathlib import Path
import subprocess
import sys
import threading
import tty

master,slave=os.openpty()
tty.setraw(slave)
child=subprocess.Popen([sys.argv[1],os.ttyname(slave)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
raw=Path(sys.argv[2]).read_bytes()

def feed():
    try:
        for i in range(0,len(raw),4096):
            chunk=memoryview(raw[i:i+4096])
            while chunk:
                n=os.write(master,chunk)
                chunk=chunk[n:]
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
print(out.decode(errors="replace"))
raise SystemExit(child.returncode)
