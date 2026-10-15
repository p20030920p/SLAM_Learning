"""Package fresh A/B runs for the simplified three-hypothesis protocol."""

import argparse
from pathlib import Path

from freeze_direction_mapping_a import freeze
from package_direction_run import package
from score_direction_time_grid import score


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("suite")
    parser.add_argument("scene")
    args = parser.parse_args()
    output = Path(args.suite) / ("2d-" + args.scene)
    package(args.run, output)
    score(output)
    freeze(args.scene, args.suite, fresh=True)
