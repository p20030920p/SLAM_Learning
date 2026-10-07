# Measured experiment ledger

Generated from run records. Paper agreement is distinct from execution.

| Experiment | Scope | Execution | Paper table | SA % | DA % | AA % | HA % | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| beautymap | full_teaser | executed | mismatch | 96.9529 | 98.3382 | 97.6431 | 97.6407 | [beautymap](reference/beautymap/record.json) |
| beautymap | full_teaser | failed | not evaluated | — | — | — | — | [beautymap-windows-failure](reference/beautymap-windows-failure/record.json) |
| dufomap | full_teaser | executed | mismatch | 97.9798 | 98.7029 | 98.3407 | 98.3400 | [dufomap](reference/dufomap/record.json) |
| controlled synthetic calibration test | controlled_synthetic_calibration_test | executed | not evaluated | — | — | — | — | [evidence-stress](reference/evidence-stress/record.json) |
| controlled synthetic mechanism test | controlled_synthetic_mechanism_test | executed | not evaluated | — | — | — | — | [mechanism](reference/mechanism/record.json) |
| real data pose sensitivity | real_data_pose_sensitivity | executed | not evaluated | — | — | — | — | [pose-stress](reference/pose-stress/record.json) |

Recorded failures:

- beautymap (beautymap-windows-failure): CalledProcessError: Command '['D:\\workspace\\be2\\SLAM_Learning\\.venv310\\Scripts\\python.exe', '-m', 'slam_learning.cli', '_worker', '--root', 'D:\\workspace\\be2\\SLAM_Learning', '--method', 'beautymap', '--output', 'D:\\workspace\\be2\\SLAM_Learning\\results\\runs\\beautymap-9d32b2cc4c1c', '--frames', '0']' returned non-zero exit status 1.

Synthetic trials are a mechanism test with oracle associations/visibility, not a paper reproduction.
Large maps and source datasets are local-only; portable records contain their hashes and fresh-run logs.
`verify --full` requires those maps to be present. No historical archive score contributes to this table.
