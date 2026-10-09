# Selected KITTI-01/02 original-workflow results

English | [中文](KITTI_SELECTED_RESULTS.zh-CN.md)

Current author preprocessing, original DUFOMap/BeautyMap entries, PCL export and Python scoring completed. Inputs use the current 50 m filter and SemanticKITTI SuMa poses, separate from released and historical inputs.

## 1. Measured scores

| Interval | Method / XY m | SA % | DA % | AA % | HA % |
| --- | --- | ---: | ---: | ---: | ---: |
| 01, 101 scans | DUFOMap | 98.9445 | 93.9332 | 96.4063 | 96.3737 |
| 01, 101 scans | BeautyMap / 1 | 99.3033 | 92.3692 | 95.7735 | 95.7108 |
| 02, 91 scans | DUFOMap | 68.6114 | 89.2862 | 78.2691 | 77.5953 |
| 02, 91 scans | BeautyMap / 0.5 | 83.2957 | 86.0901 | 84.6814 | 84.6699 |
| 02, 91 scans | BeautyMap / 1 | 83.4254 | 84.6594 | 84.0401 | 84.0378 |
| 02, 91 scans | BeautyMap / 2 | 74.5822 | 90.6875 | 82.2416 | 81.8502 |

[Original metrics](../../results/runs/kitti-author-selected-02/metrics.json) · [Six-map validation](../../results/runs/kitti-result-validation-01/validation.json).

## 2. Interpretation

01 uses inclusive frames 150–250; 02 uses 860–950. The reconstructed 00 input differs from the older release in all 141 scan counts and supplied poses. These scores cannot be combined with released-input paper matches or attributed uniquely to localization error.

Keep SA/DA and the grid tradeoff visible. Matching paper values requires input/pose/version reconciliation; finite PCD output is execution evidence, not scientific equivalence. [Input differences](../guides/DATA_ACCESS.md) · [Historical Table III](KITTI_PAPER_PROTOCOL.md) · [Detailed paper gaps](KITTI_SELECTED_RESULTS.zh-CN.md).
