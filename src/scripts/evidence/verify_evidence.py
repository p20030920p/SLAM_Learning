"""Verify published evidence after checkout, including preservation of byte hashes."""
from pathlib import Path

from slam_learning.runtime.runner import verify_record


def main() -> int:
    paths = sorted(Path("results/reference").glob("*/record.json"))
    if not paths:
        raise ValueError("No published reference evidence")
    errors = [f"{path}: {issue}" for path in paths for issue in verify_record(path)]
    print("\n".join(errors) if errors else f"Verified {len(paths)} portable evidence records")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
