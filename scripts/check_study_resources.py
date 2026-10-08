"""Read-only resource gate; exit 2 means defer heavy work without changing other jobs."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.identity_budget import check_resources


def main():
    try:
        record = {"status": "idle", **check_resources()}
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        record = {"status": "defer", "reason": str(error)}
    record["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(record, indent=2))
    return 0 if record["status"] == "idle" else 2


if __name__ == "__main__":
    raise SystemExit(main())
