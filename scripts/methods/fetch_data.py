"""Bootstrap download before an editable installation; same implementation as CLI."""
import argparse
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src"))
from slam_learning.runtime.fetch import fetch  # noqa: E402 - bootstrap the src checkout

parser = argparse.ArgumentParser()
parser.add_argument("--direct", action="store_true", help="Bypass an explicitly broken proxy for this request")
fetch(root, parser.parse_args().direct)
