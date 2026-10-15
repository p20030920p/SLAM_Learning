"""Print the released evaluation error trajectory of a probe trial."""

import re
import sys
from pathlib import Path

import numpy as np

log = Path(sys.argv[1])
text = re.sub(r"\x1b\[[0-9;]*m", "", log.read_text(errors="replace"))
errors = [float(value) for value in re.findall(r"Error in position:\s*\[?([0-9.eE+-]+)", text)]
errors = np.sqrt(np.array(errors))
print("updates", len(errors))
for start in range(0, len(errors), 10):
    window = errors[start:start + 10]
    print(f"{start + 1:4d}-{start + len(window):4d}  " +
          " ".join(f"{value:8.2f}" for value in window))
