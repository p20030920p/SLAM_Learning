from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from live_metrics import match_observations


class CoverageTest(unittest.TestCase):
    def test_rgbd_can_stamp_depth_instead_of_color(self):
        self.assertEqual(match_observations([[10000,20000],[30000,40000]],[20000,40000]),{0,1})
    def test_one_output_cannot_cover_two_inputs(self):
        self.assertEqual(len(match_observations([[10000],[10000]],[10000])),1)
    def test_small_rounding_only(self):
        self.assertEqual(match_observations([[10000],[30000],[50000]],[10999,31001]),{0})
    def test_empty_output(self):
        self.assertEqual(match_observations([[10000]],[]),set())


if __name__ == '__main__':
    unittest.main()
