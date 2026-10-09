"""Timestamp coverage shared by ROS reporting and reproducible software tests."""
import numpy as np


def match_observations(candidates, output_stamps, tolerance_ns=1000):
    delivered = np.sort(np.asarray(output_stamps, dtype=np.int64))
    matched, used = set(), set()
    for i, alternatives in enumerate(candidates):
        for candidate in alternatives:
            index = int(np.searchsorted(delivered, candidate))
            choices = [j for j in (index-1, index) if 0 <= j < len(delivered) and j not in used]
            if choices:
                closest = min(choices, key=lambda j: abs(int(delivered[j])-candidate))
                if abs(int(delivered[closest])-candidate) <= tolerance_ns:
                    used.add(closest)
                    matched.add(i)
                    break
    return matched
